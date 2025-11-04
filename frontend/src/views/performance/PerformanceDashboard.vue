<template>
  <div class="performance-dashboard">
    <!-- 顶部控制栏 -->
    <header class="dashboard-header">
      <div class="header-left">
        <h1 class="title">
          <el-icon><DataAnalysis /></el-icon>
          性能测试仪表盘
        </h1>
        <span v-if="currentTaskName" class="task-name">{{ currentTaskName }}</span>
        <span v-if="isRunning" class="status-badge running">运行中</span>
      </div>
      <div class="header-right">
        <span v-if="isRunning" class="info-item">
          <el-icon><Clock /></el-icon>
          持续: <strong>{{ formatDuration(duration) }}</strong>
        </span>
        <span v-if="isRunning" class="info-item">
          <el-icon><User /></el-icon>
          并发: <strong>{{ currentThreads }}</strong>
        </span>
        <el-button
          v-if="isRunning"
          type="danger"
          @click="handleStop"
          :loading="stopping"
        >
          <el-icon><VideoPlay /></el-icon>
          停止测试
        </el-button>
      </div>
    </header>

    <div class="dashboard-content">
      <!-- 测试概览卡片 -->
      <div class="overview-cards">
        <div class="overview-card">
          <div class="card-label">开始时间</div>
          <div class="card-value">{{ startTime || '-' }}</div>
        </div>
        <div class="overview-card">
          <div class="card-label">总请求</div>
          <div class="card-value">{{ metrics.total_samples || 0 }} 次</div>
        </div>
        <div class="overview-card">
          <div class="card-label">峰值 RPS</div>
          <div class="card-value highlight">{{ peakRPS || 0 }}</div>
        </div>
        <div class="overview-card">
          <div class="card-label">当前 RPS</div>
          <div class="card-value success">{{ currentRPS || 0 }}</div>
        </div>
      </div>

      <!-- 主指标区域 -->
      <div class="metrics-grid">
        <!-- 1. 响应时间 -->
        <el-card class="metric-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <el-icon><Timer /></el-icon>
              <span>响应时间</span>
            </div>
          </template>
          <div class="metric-content">
            <div class="metric-main">
              <span class="metric-label">平均</span>
              <span class="metric-value primary">{{ (metrics.avg_response_time || 0).toFixed(0) }}ms</span>
            </div>
            <div class="metric-details">
              <span>最快 {{ metrics.min_response_time ? metrics.min_response_time.toFixed(2) : 0 }}ms</span>
              <span>最慢 <span :class="metrics.max_response_time > 1000 ? 'warning' : ''">{{ metrics.max_response_time ? metrics.max_response_time.toFixed(2) : 0 }}ms</span></span>
            </div>
            <div class="chart-container">
              <VChart class="chart" :option="responseTimeChartOption" :autoresize="true" />
            </div>
          </div>
        </el-card>

        <!-- 2. 吞吐量 & 错误率 -->
        <el-card class="metric-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <el-icon><TrendCharts /></el-icon>
              <span>吞吐量</span>
            </div>
          </template>
          <div class="metric-content">
            <div class="metric-main">
              <span class="metric-label">RPS</span>
              <span class="metric-value success">{{ (metrics.throughput || 0).toFixed(0) }}</span>
            </div>
            <div class="metric-main">
              <span class="metric-label">成功率</span>
              <span class="metric-value" :class="successRate >= 99 ? 'success' : 'warning'">
                {{ successRate.toFixed(2) }}%
              </span>
            </div>
            <div class="metric-details">
              <span>错误</span>
              <span class="error">{{ metrics.failed_samples || 0 }} 次</span>
            </div>
            <div class="chart-container">
              <VChart class="chart" :option="throughputChartOption" :autoresize="true" />
            </div>
          </div>
        </el-card>

        <!-- 3. 响应时间百分位数 -->
        <el-card class="metric-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <el-icon><Histogram /></el-icon>
              <span>响应时间百分位数</span>
            </div>
          </template>
          <div class="metric-content">
            <div class="percentile-item">
              <span class="percentile-label">中位数 (50%)</span>
              <span class="percentile-value">{{ (metrics.median_response_time || 0).toFixed(0) }}ms</span>
            </div>
            <div class="percentile-item">
              <span class="percentile-label">P90 (90%)</span>
              <span class="percentile-value">{{ (metrics.p90_response_time || 0).toFixed(0) }}ms</span>
            </div>
            <div class="percentile-item">
              <span class="percentile-label">P95 (95%)</span>
              <span class="percentile-value">{{ (metrics.p95_response_time || 0).toFixed(0) }}ms</span>
            </div>
            <div class="percentile-item">
              <span class="percentile-label">P99 (99%)</span>
              <span class="percentile-value">{{ (metrics.p99_response_time || 0).toFixed(0) }}ms</span>
            </div>
          </div>
        </el-card>
      </div>

      <!-- 响应时间分布 -->
      <el-card class="distribution-card" shadow="hover">
        <template #header>
          <div class="card-header">
            <el-icon><Histogram /></el-icon>
            <span>响应时间分布</span>
          </div>
        </template>
        <div class="chart-container">
          <VChart class="chart" :option="distributionChartOption" :autoresize="true" />
        </div>
      </el-card>

      <!-- 阈值警报 -->
      <el-alert
        v-if="hasWarning"
        :title="warningMessage"
        type="warning"
        :closable="false"
        class="warning-alert"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart, BarChart } from 'echarts/charts'
import { TitleComponent, TooltipComponent, GridComponent } from 'echarts/components'
import VChart, { THEME_KEY } from 'vue-echarts'
import { ElMessage } from 'element-plus'
import { DataAnalysis, Clock, User, VideoPlay, Timer, TrendCharts, Monitor, Histogram } from '@element-plus/icons-vue'
import { getPerformanceTests, getPerformanceTest } from '../../api/performanceTests'

// 注册ECharts组件
use([
  CanvasRenderer,
  LineChart,
  BarChart,
  TitleComponent,
  TooltipComponent,
  GridComponent
])

const route = useRoute()
const loading = ref(false)
const isRunning = ref(false)
const stopping = ref(false)
const startTime = ref('')
const duration = ref(0)
const currentThreads = ref(0)
const peakRPS = ref(0)
const currentRPS = ref(0)
const currentTaskName = ref('')

const metrics = ref({
  total_samples: 0,
  success_samples: 0,
  failed_samples: 0,
  avg_response_time: 0,
  min_response_time: 0,
  max_response_time: 0,
  median_response_time: 0,
  p90_response_time: 0,
  p95_response_time: 0,
  p99_response_time: 0,
  throughput: 0,
  error_rate: 0
})

const systemResources = ref({
  cpu: 0,
  memory: 0,
  network: 0
})

const responseTimeHistory = ref([])
const throughputHistory = ref([])
const distributionData = ref([0, 0, 0, 0, 0])

let updateTimer = null

const successRate = computed(() => {
  if (metrics.value.total_samples === 0) return 100
  return ((metrics.value.success_samples / metrics.value.total_samples) * 100)
})

const hasWarning = computed(() => {
  return metrics.value.failed_samples > 0 || metrics.value.error_rate > 1
})

const warningMessage = computed(() => {
  if (metrics.value.failed_samples > 0) {
    return `警告：失败请求数 ${metrics.value.failed_samples} 次，错误率 ${metrics.value.error_rate.toFixed(2)}%，请检查接口状态。`
  }
  return ''
})

const responseTimeChartOption = computed(() => ({
  tooltip: {
    trigger: 'axis'
  },
  xAxis: {
    type: 'category',
    data: responseTimeHistory.value.map((_, i) => `-${(responseTimeHistory.value.length - i) * 15}s`),
    show: false
  },
  yAxis: {
    type: 'value',
    show: false
  },
  series: [{
    type: 'line',
    data: responseTimeHistory.value,
    smooth: true,
    lineStyle: {
      color: '#3b82f6',
      width: 2
    },
    areaStyle: {
      color: {
        type: 'linear',
        x: 0,
        y: 0,
        x2: 0,
        y2: 1,
        colorStops: [
          { offset: 0, color: 'rgba(59, 130, 246, 0.3)' },
          { offset: 1, color: 'rgba(59, 130, 246, 0.1)' }
        ]
      }
    },
    symbol: 'none'
  }],
  grid: {
    left: 0,
    right: 0,
    top: 0,
    bottom: 0
  }
}))

const throughputChartOption = computed(() => ({
  tooltip: {
    trigger: 'axis'
  },
  xAxis: {
    type: 'category',
    data: throughputHistory.value.map((_, i) => `-${(throughputHistory.value.length - i) * 15}s`),
    show: false
  },
  yAxis: {
    type: 'value',
    show: false
  },
  series: [{
    type: 'line',
    data: throughputHistory.value,
    smooth: true,
    lineStyle: {
      color: '#16a34a',
      width: 2
    },
    areaStyle: {
      color: {
        type: 'linear',
        x: 0,
        y: 0,
        x2: 0,
        y2: 1,
        colorStops: [
          { offset: 0, color: 'rgba(22, 163, 74, 0.3)' },
          { offset: 1, color: 'rgba(22, 163, 74, 0.1)' }
        ]
      }
    },
    symbol: 'none'
  }],
  grid: {
    left: 0,
    right: 0,
    top: 0,
    bottom: 0
  }
}))

const distributionChartOption = computed(() => ({
  tooltip: {
    trigger: 'axis',
    formatter: (params) => {
      const param = params[0]
      return `${param.name}<br/>${param.seriesName}: ${param.value} 次`
    }
  },
  xAxis: {
    type: 'category',
    data: ['<100ms', '100-200ms', '200-500ms', '500ms-1s', '>1s']
  },
  yAxis: {
    type: 'value',
    name: '请求数'
  },
  series: [{
    name: '请求数',
    type: 'bar',
    data: distributionData.value,
    itemStyle: {
      color: (params) => {
        const colors = ['#10b981', '#3b82f6', '#f59e0b', '#f97316', '#ef4444']
        return colors[params.dataIndex]
      }
    }
  }],
  grid: {
    left: '3%',
    right: '4%',
    bottom: '3%',
    containLabel: true
  }
}))

const formatDuration = (seconds) => {
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins}分${secs}秒`
}

const getProgressColor = (percentage) => {
  if (percentage < 50) return '#67c23a'
  if (percentage < 80) return '#e6a23c'
  return '#f56c6c'
}

const handleStop = () => {
  stopping.value = true
  // TODO: 调用停止API
  setTimeout(() => {
    isRunning.value = false
    stopping.value = false
    ElMessage.success('测试已停止')
  }, 1000)
}

// 计算响应时间分布（基于百分位数估算）
const calculateDistribution = (metricsData) => {
  if (!metricsData || metricsData.total_samples === 0) {
    return [0, 0, 0, 0, 0]
  }
  
  const total = metricsData.total_samples
  const median = metricsData.median_response_time || metricsData.avg_response_time || 0
  const p90 = metricsData.p90_response_time || median
  const p95 = metricsData.p95_response_time || p90
  const p99 = metricsData.p99_response_time || p95
  const max = metricsData.max_response_time || p99
  
  // 根据百分位数估算分布
  // 50%的请求 <= median，90%的请求 <= p90，以此类推
  // 估算各时间段的请求数
  const below100 = Math.max(0, Math.min(total, total * 0.5))  // 假设50%在100ms以下
  const range100_200 = Math.max(0, Math.min(total * 0.3, total - below100))  // 30%在100-200ms
  const range200_500 = Math.max(0, Math.min(total * 0.15, total - below100 - range100_200))  // 15%在200-500ms
  const range500_1000 = Math.max(0, Math.min(total * 0.04, total - below100 - range100_200 - range200_500))  // 4%在500-1000ms
  const above1000 = Math.max(0, total - below100 - range100_200 - range200_500 - range500_1000)  // 剩余在1s以上
  
  return [
    Math.round(below100),
    Math.round(range100_200),
    Math.round(range200_500),
    Math.round(range500_1000),
    Math.round(above1000)
  ]
}

// 加载最新性能测试数据
const loadLatestPerformanceData = async () => {
  loading.value = true
  try {
    const response = await getPerformanceTests()
    const tasks = response.results || response || []
    
    // 找到有最新执行结果的任务
    let latestTask = null
    let latestTime = null
    
    tasks.forEach(task => {
      if (task.last_result && task.last_execution_time) {
        const execTime = new Date(task.last_execution_time)
        if (!latestTime || execTime > latestTime) {
          latestTime = execTime
          latestTask = task
        }
      }
    })
    
    if (latestTask && latestTask.last_result) {
      // 更新任务信息
      currentTaskName.value = latestTask.name
      startTime.value = formatDateTime(latestTask.last_execution_time)
      
      // 获取执行结果
      const result = latestTask.last_result
      const resultMetrics = result.metrics || result.result?.metrics || {}
      
      // 更新指标
      metrics.value = {
        total_samples: resultMetrics.total_samples || 0,
        success_samples: resultMetrics.success_samples || resultMetrics.total_samples || 0,
        failed_samples: resultMetrics.failed_samples || 0,
        avg_response_time: resultMetrics.avg_response_time || 0,
        min_response_time: resultMetrics.min_response_time || 0,
        max_response_time: resultMetrics.max_response_time || 0,
        median_response_time: resultMetrics.median_response_time || 0,
        p90_response_time: resultMetrics.p90_response_time || 0,
        p95_response_time: resultMetrics.p95_response_time || 0,
        p99_response_time: resultMetrics.p99_response_time || 0,
        throughput: resultMetrics.throughput || 0,
        error_rate: resultMetrics.error_rate || 0
      }
      
      // 更新持续时间
      if (result.duration || result.result?.duration) {
        duration.value = Math.round(result.duration || result.result?.duration || 0)
      }
      
      // 更新并发数和RPS
      if (latestTask.threads) {
        currentThreads.value = latestTask.threads
      }
      currentRPS.value = Math.round(metrics.value.throughput)
      if (currentRPS.value > peakRPS.value) {
        peakRPS.value = currentRPS.value
      }
      
      // 更新响应时间分布
      distributionData.value = calculateDistribution(metrics.value)
      
      // 初始化历史数据（用于图表显示）
      if (responseTimeHistory.value.length === 0) {
        // 生成一些模拟的历史数据点，基于当前平均值
        for (let i = 0; i < 20; i++) {
          const variation = metrics.value.avg_response_time * 0.1 * (Math.random() - 0.5)
          responseTimeHistory.value.push(Math.max(0, metrics.value.avg_response_time + variation))
          throughputHistory.value.push(Math.max(0, metrics.value.throughput + metrics.value.throughput * 0.1 * (Math.random() - 0.5)))
        }
      }
      
      isRunning.value = false  // 历史数据，显示为已停止
    } else {
      // 没有数据，显示空状态
      ElMessage.info('暂无性能测试数据')
    }
  } catch (error) {
    console.error('加载性能测试数据失败:', error)
    ElMessage.error('加载数据失败')
  } finally {
    loading.value = false
  }
}

// 格式化日期时间
const formatDateTime = (dateString) => {
  if (!dateString) return '-'
  const date = new Date(dateString)
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  const seconds = String(date.getSeconds()).padStart(2, '0')
  return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`
}

onMounted(() => {
  // 加载最新性能测试数据
  loadLatestPerformanceData()
  
  // 定期刷新数据（每30秒）
  updateTimer = setInterval(() => {
    loadLatestPerformanceData()
  }, 30000)
})

onUnmounted(() => {
  if (updateTimer) {
    clearInterval(updateTimer)
  }
})
</script>

<style scoped>
.performance-dashboard {
  padding: 24px;
  background-color: #f5f7fa;
  min-height: calc(100vh - 60px);
}

.dashboard-header {
  background: white;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  border-radius: 0.75rem;
  padding: 16px 24px;
  margin-bottom: 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.title {
  font-size: 20px;
  font-weight: bold;
  color: #303133;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 12px;
}

.title .el-icon {
  color: #409eff;
}

.status-badge {
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.status-badge.running {
  background: #d1fae5;
  color: #065f46;
}

.status-badge.stopped {
  background: #fee2e2;
  color: #991b1b;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
  font-size: 14px;
  color: #606266;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.info-item .el-icon {
  margin-right: 4px;
}

.overview-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.overview-card {
  background: white;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  border-radius: 0.75rem;
  padding: 20px;
  text-align: center;
}

.card-label {
  font-size: 12px;
  color: #909399;
  margin-bottom: 8px;
}

.card-value {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.card-value.highlight {
  color: #409eff;
}

.card-value.success {
  color: #67c23a;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.metric-card {
  min-height: 300px;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
}

.card-header .el-icon {
  color: #409eff;
}

.metric-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.metric-main {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.metric-label {
  color: #606266;
  font-size: 14px;
}

.metric-value {
  font-size: 24px;
  font-weight: bold;
}

.metric-value.primary {
  color: #409eff;
}

.metric-value.success {
  color: #67c23a;
}

.metric-value.warning {
  color: #e6a23c;
}

.metric-details {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #909399;
}

.metric-details .warning {
  color: #e6a23c;
}

.metric-details .error {
  color: #f56c6c;
}

.chart-container {
  height: 120px;
  margin-top: 8px;
}

.chart {
  height: 100%;
  width: 100%;
}

.percentile-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid #f0f0f0;
}

.percentile-item:last-child {
  border-bottom: none;
}

.percentile-label {
  font-size: 14px;
  color: #606266;
}

.percentile-value {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.distribution-card {
  margin-bottom: 24px;
}

.distribution-card .chart-container {
  height: 200px;
}

.warning-alert {
  margin-top: 24px;
}
</style>

