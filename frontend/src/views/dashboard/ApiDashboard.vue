<template>
  <div class="dashboard-container">
    <!-- 顶部 header -->
    <header class="dashboard-header">
      <div class="header-left">
        <h1 class="title">测试平台 · 仪表盘</h1>
        <p class="subtitle">概览测试健康状况、历史趋势与失败热点</p>
      </div>
      <div class="header-right">
        <el-select v-model="dateRange" style="width: 150px" @change="handleDateRangeChange">
          <el-option label="最近 1 小时" value="1h" />
          <el-option label="最近 24 小时" value="24h" />
          <el-option label="最近 7 天" value="7d" />
          <el-option label="最近 30 天" value="30d" />
        </el-select>
        <el-input
          v-model="query"
          placeholder="搜索运行 ID / 套件"
          style="width: 200px"
          clearable
        />
        <el-button type="primary" @click="handleExport">导出 CSV</el-button>
      </div>
    </header>

    <!-- 指标卡片 -->
    <section class="stats-grid">
      <transition-group name="fade-up" tag="div" class="stats-cards">
        <el-card :key="'total'" class="stat-card" shadow="hover">
          <div class="stat-label">测试套件总数</div>
          <div class="stat-value">{{ summary.totalSuites }}</div>
          <div class="stat-desc">运行中: {{ summary.running }}</div>
        </el-card>

        <el-card :key="'passed'" class="stat-card" shadow="hover">
          <div class="stat-label">今日通过</div>
          <div class="stat-value text-success">{{ summary.passedToday }}</div>
          <div class="stat-desc">平均耗时: {{ summary.avgDurationSec }}s</div>
        </el-card>

        <el-card :key="'failed'" class="stat-card" shadow="hover">
          <div class="stat-label">今日失败</div>
          <div class="stat-value text-danger">{{ summary.failedToday }}</div>
          <div class="stat-desc">失败率: {{ summary.passedToday + summary.failedToday > 0 ? ((summary.failedToday / (summary.passedToday + summary.failedToday)) * 100).toFixed(2) : 0 }}%</div>
        </el-card>

        <el-card :key="'rate'" class="stat-card" shadow="hover">
          <div class="stat-label">总体通过率</div>
          <div class="stat-value text-primary">{{ summary.passRate }}%</div>
          <div class="stat-desc">SLA 目标: 99.0%</div>
        </el-card>
      </transition-group>
    </section>

    <!-- 主体图表区域 -->
    <section class="charts-grid">
      <!-- 趋势图 -->
      <el-card class="chart-card" shadow="hover">
        <template #header>
          <div class="card-header">
            <span class="card-title">近 12 小时测试执行趋势</span>
            <span class="card-subtitle">按时间窗口聚合</span>
          </div>
        </template>
        <VChart class="chart" :option="lineChartOption" :autoresize="true" />
      </el-card>

      <!-- 饼图 -->
      <el-card class="chart-card" shadow="hover">
        <template #header>
          <span class="card-title">通过 / 失败 / 跳过</span>
        </template>
        <div class="pie-chart-container">
          <VChart class="pie-chart" :option="pieChartOption" :autoresize="true" />
          <div class="pie-legend">
            <div v-for="(item, index) in passFailData" :key="item.name" class="legend-item">
              <span class="legend-color" :style="{ background: COLORS[index] }"></span>
  <div>
                <div class="legend-name">{{ item.name }}</div>
                <div class="legend-value">{{ item.value }}</div>
              </div>
            </div>
          </div>
        </div>
      </el-card>

      <!-- 失败趋势 -->
      <el-card class="chart-card" shadow="hover">
        <template #header>
          <div class="card-header">
            <span class="card-title">失败趋势（按用例）</span>
            <span class="card-subtitle">显示最近10个用例的执行情况</span>
          </div>
        </template>
        <div v-if="failureTrend.length > 0">
          <div style="min-height: 300px;">
            <VChart v-if="barChartOption && Object.keys(barChartOption).length > 0" class="chart" :option="barChartOption" :autoresize="true" />
            <div v-else style="padding: 40px; text-align: center; color: #909399;">图表加载中...</div>
          </div>
          <div class="chart-summary" style="margin-top: 16px; padding: 12px; background: #f5f7fa; border-radius: 4px; font-size: 12px; color: #606266;">
            <div style="margin-bottom: 8px;"><strong>说明：</strong></div>
            <div>• <span style="color: #3B82F6;">蓝色柱状图</span>：表示每个用例的执行次数</div>
            <div>• <span style="color: #EF4444;">红色柱状图</span>：表示每个用例的失败次数</div>
            <div>• 将鼠标悬停在柱状图上可查看详细数值</div>
            <div>• 数据来源：最近 {{ getHoursFromRange(dateRange) }} 小时内的执行记录</div>
          </div>
        </div>
        <el-empty v-else description="暂无测试数据，请先执行测试用例" :image-size="100" />
      </el-card>

      <!-- Flaky用例列表 -->
      <el-card class="chart-card" shadow="hover">
        <template #header>
          <span class="card-title">Flaky / 高风险用例</span>
        </template>
        <div class="flaky-list">
          <div v-for="item in flakyCases" :key="item.name" class="flaky-item">
            <div class="flaky-content">
              <div class="flaky-name">{{ item.name }}</div>
              <div class="flaky-desc">{{ item.desc }}</div>
            </div>
            <el-tag :type="item.type">{{ item.risk }}</el-tag>
          </div>
        </div>
      </el-card>

      <!-- 最近的运行列表 -->
      <el-card class="chart-card full-width" shadow="hover">
        <template #header>
          <div class="card-header">
            <span class="card-title">最近运行</span>
            <span class="card-subtitle">显示最新 10 条</span>
          </div>
        </template>
        <el-table :data="filteredRuns" style="width: 100%" stripe v-loading="loading" empty-text="暂无运行记录">
          <el-table-column prop="id" label="ID" width="120" />
          <el-table-column prop="suite" label="套件" width="150" />
          <el-table-column prop="testcase" label="用例" width="180" show-overflow-tooltip />
          <el-table-column prop="env" label="环境" width="100">
            <template #default="{ row }">
              <el-tag :type="getEnvTagType(row.env)" size="small">{{ row.env || '-' }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="startedAt" label="开始时间" width="180" />
          <el-table-column prop="duration" label="耗时" width="100" />
          <el-table-column prop="status" label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="getStatusTagType(row.status)" size="small">{{ row.status }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="150">
            <template #default="{ row }">
              <el-button size="small" @click="handleView(row)">查看</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-card>

      <!-- 右侧小面板 -->
      <div class="sidebar-panels">
        <!-- 环境健康 -->
        <el-card class="sidebar-card" shadow="hover">
          <template #header>
            <span class="card-title">环境健康</span>
          </template>
          <div class="env-grid">
            <div v-for="env in environments" :key="env.name" class="env-item">
              <div class="env-label">{{ env.name }}</div>
              <div class="env-status" :class="env.status === '在线' ? 'status-online' : 'status-offline'">
                {{ env.status }}
              </div>
              <div class="env-desc">响应: {{ env.response }}ms</div>
            </div>
          </div>
        </el-card>

        <!-- 快速操作 -->
        <el-card class="sidebar-card" shadow="hover">
          <template #header>
            <span class="card-title">快速操作</span>
          </template>
          <div class="quick-actions">
            <el-button type="success" style="width: 100%; margin-bottom: 10px" @click="handleQuickAction('smoke')">
              触发冒烟测试
            </el-button>
            <el-button type="primary" style="width: 100%; margin-bottom: 10px" @click="handleQuickAction('full')">
              触发完整回归
            </el-button>
            <el-button style="width: 100%" @click="handleQuickAction('clean')">清理历史运行</el-button>
          </div>
        </el-card>
      </div>
    </section>

    <!-- 页脚说明 -->
    <footer class="dashboard-footer">
      数据实时更新，基于实际执行记录统计
    </footer>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, provide, watch } from 'vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart, BarChart, PieChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent
} from 'echarts/components'
import VChart, { THEME_KEY } from 'vue-echarts'
import { ElMessage } from 'element-plus'
import { getDashboardData } from '../../api/dashboard'

// 注册ECharts组件
use([
  CanvasRenderer,
  LineChart,
  BarChart,
  PieChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent
])

// 提供主题（可选）
provide(THEME_KEY, 'default')

// 数据定义
const query = ref('')
const dateRange = ref('24h')
const loading = ref(false)

const summary = ref({
  totalSuites: 0,
  running: 0,
  passedToday: 0,
  failedToday: 0,
  passRate: 0,
  avgDurationSec: 0
})

const runsTrend = ref([])

const passFailData = ref([
  { name: '通过', value: 0 },
  { name: '失败', value: 0 },
  { name: '跳过', value: 0 }
])

const COLORS = ['#10B981', '#EF4444', '#FBBF24']

const recentRuns = ref([])

const flakyCases = ref([])
const failureTrend = ref([])

const environments = ref([
  { name: 'staging', status: '在线', response: 120 },
  { name: 'qa', status: '在线', response: 200 }
])

// 计算属性
const filteredRuns = computed(() => {
  if (!query.value) return recentRuns.value
  return recentRuns.value.filter(
    (r) => (r.suite && r.suite.includes(query.value)) || 
           (r.testcase && r.testcase.includes(query.value)) ||
           String(r.id).includes(query.value)
  )
})

// 图表配置
const lineChartOption = computed(() => ({
  tooltip: {
    trigger: 'axis'
  },
  xAxis: {
    type: 'category',
    data: runsTrend.value.map((item) => item.name)
  },
  yAxis: {
    type: 'value'
  },
  series: [
    {
      name: '执行次数',
      type: 'line',
      data: runsTrend.value.map((item) => item.runs),
      smooth: true,
      lineStyle: {
        color: '#2563EB',
        width: 2
      },
      itemStyle: {
        color: '#2563EB'
      }
    },
    {
      name: '失败次数',
      type: 'line',
      data: runsTrend.value.map((item) => item.failures),
      smooth: true,
      lineStyle: {
        color: '#EF4444',
        width: 2
      },
      itemStyle: {
        color: '#EF4444'
      },
      symbol: 'circle',
      symbolSize: 6
    }
  ],
  grid: {
    left: '3%',
    right: '4%',
    bottom: '3%',
    containLabel: true
  }
}))

const pieChartOption = computed(() => ({
  tooltip: {
    trigger: 'item',
    formatter: '{a} <br/>{b}: {c} ({d}%)'
  },
  series: [
    {
      name: '测试结果',
      type: 'pie',
      radius: ['40%', '70%'],
      avoidLabelOverlap: false,
      itemStyle: {
        borderRadius: 10,
        borderColor: '#fff',
        borderWidth: 2
      },
      label: {
        show: true,
        formatter: '{b}: {c}'
      },
      emphasis: {
        label: {
          show: true,
          fontSize: 14,
          fontWeight: 'bold'
        }
      },
      data: passFailData.value.map((item, index) => ({
        ...item,
        itemStyle: {
          color: COLORS[index]
        }
      }))
    }
  ]
}))

const barChartOption = computed(() => {
  if (failureTrend.value.length === 0) {
    return {}
  }
  
  const maxValue = Math.max(
    ...failureTrend.value.map(item => Math.max(item.runs || 0, item.failures || 0)),
    1  // 至少为1，避免maxValue为0时图表显示异常
  )
  
  return {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      },
      formatter: (params) => {
        if (!params || params.length === 0) return ''
        let result = params[0].name + '<br/>'
        params.forEach(param => {
          result += `${param.marker} ${param.seriesName}: ${param.value} 次<br/>`
        })
        return result
      }
    },
    legend: {
      data: ['执行次数', '失败次数'],
      top: 0,  // 图例放在顶部
      left: 'center',  // 居中显示
      itemGap: 30
    },
    xAxis: {
      type: 'category',
      data: failureTrend.value.map((item) => item.name || '未知用例'),
      position: 'bottom',
      axisLabel: {
        rotate: 0,  // 不旋转，水平显示
        interval: 0,  // 显示所有标签
        formatter: (value) => {
          // 水平显示时，根据可用宽度截断，如果名称太长，截断并显示省略号
          if (value.length > 15) {
            return value.substring(0, 15) + '...'
          }
          return value
        },
        margin: 12
      },
      axisLine: {
        show: true
      }
    },
    yAxis: {
      type: 'value',
      min: 0,
      minInterval: 1,  // 确保Y轴刻度为整数
      axisLabel: {
        formatter: '{value} 次'
      },
      splitLine: {
        show: true,
        lineStyle: {
          type: 'dashed'
        }
      }
    },
    series: [
      {
        name: '执行次数',
        type: 'bar',
        data: failureTrend.value.map((item) => item.runs || 0),
        itemStyle: {
          color: '#3B82F6',
          borderRadius: [4, 4, 0, 0]  // 顶部圆角
        },
        barWidth: 30,  // 使用固定像素宽度，避免百分比计算问题
        barGap: '30%',  // 同一组内两个柱子之间的间距
        barCategoryGap: '40%',  // 不同类别之间的间距
        label: {
          show: true,
          position: 'top',
          formatter: '{c}',
          color: '#303133',
          fontSize: 12,
          fontWeight: 'bold'
        },
        emphasis: {
          focus: 'series',
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)'
          }
        }
      },
      {
        name: '失败次数',
        type: 'bar',
        data: failureTrend.value.map((item) => item.failures || 0),
        itemStyle: {
          color: '#EF4444',
          borderRadius: [4, 4, 0, 0]  // 顶部圆角
        },
        barWidth: 30,  // 使用固定像素宽度
        label: {
          show: true,
          position: 'top',
          formatter: '{c}',
          color: '#303133',
          fontSize: 12,
          fontWeight: 'bold'
        },
        emphasis: {
          focus: 'series',
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)'
          }
        }
      }
    ],
    grid: {
      left: '12%',  // 增加左侧空间，避免Y轴标签被挤压
      right: '4%',
      bottom: '10%',  // 底部空间用于x轴标签
      top: '15%',  // 顶部空间用于图例
      containLabel: false  // 手动控制边距，避免自动计算导致的空间浪费
    }
  }
})

// 方法
const getHoursFromRange = (range) => {
  const map = {
    '1h': 1,
    '24h': 24,
    '7d': 168,
    '30d': 720
  }
  return map[range] || 24
}

const loadDashboardData = async () => {
  loading.value = true
  try {
    const hours = getHoursFromRange(dateRange.value)
    const response = await getDashboardData({ hours })
    
    console.log('Dashboard API响应:', response)
    
    // 更新统计数据
    if (response.summary) {
      summary.value = response.summary
    }
    
    // 更新趋势数据
    if (response.trend) {
      runsTrend.value = response.trend
    }
    
    // 更新通过/失败数据
    if (response.passFailData) {
      passFailData.value = response.passFailData
    }
    
    // 更新最近运行
    if (response.recentRuns) {
      recentRuns.value = response.recentRuns
    }
    
    // 更新Flaky用例
    if (response.flakyCases) {
      flakyCases.value = response.flakyCases
    }
    
    // 更新失败趋势
    if (response.failureTrend) {
      failureTrend.value = response.failureTrend
      console.log('失败趋势数据:', failureTrend.value)
    } else {
      console.warn('API响应中没有failureTrend字段')
      failureTrend.value = []
    }
  } catch (error) {
    console.error('加载仪表盘数据失败:', error)
    ElMessage.error('加载仪表盘数据失败')
  } finally {
    loading.value = false
  }
}

const handleDateRangeChange = (value) => {
  loadDashboardData()
}

const handleExport = () => {
  ElMessage.success('导出功能开发中...')
}

const handleView = (row) => {
  // 跳转到执行记录页面并打开详情
  window.location.href = `/executions?execution_id=${row.id}`
}

const handleRerun = (row) => {
  ElMessage.success(`重新运行: ${row.id}`)
}

const handleQuickAction = (action) => {
  const actions = {
    smoke: '触发冒烟测试',
    full: '触发完整回归',
    clean: '清理历史运行'
  }
  ElMessage.success(`${actions[action]} - 功能开发中...`)
}

const getEnvTagType = (env) => {
  const types = {
    prod: 'danger',
    staging: 'warning',
    qa: 'success'
  }
  return types[env] || ''
}

const getStatusTagType = (status) => {
  const types = {
    通过: 'success',
    失败: 'danger',
    运行中: 'warning'
  }
  return types[status] || ''
}

// 监听时间范围变化
watch(dateRange, () => {
  loadDashboardData()
})

onMounted(() => {
  loadDashboardData()
})
</script>

<style scoped>
.dashboard-container {
  padding: 24px;
  background-color: #f5f7fa;
  min-height: calc(100vh - 60px);
}

.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
  flex-wrap: wrap;
  gap: 16px;
}

.header-left {
  flex: 1;
}

.title {
  font-size: 24px;
  font-weight: 600;
  margin: 0 0 8px 0;
  color: #303133;
}

.subtitle {
  font-size: 14px;
  color: #909399;
  margin: 0;
}

.header-right {
  display: flex;
  gap: 12px;
  align-items: center;
  flex-wrap: wrap;
}

.stats-grid {
  margin-bottom: 24px;
}

.stats-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 16px;
}

.stat-card {
  transition: transform 0.2s;
}

.stat-card:hover {
  transform: translateY(-2px);
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-bottom: 8px;
}

.stat-value {
  font-size: 32px;
  font-weight: bold;
  margin-bottom: 8px;
  color: #303133;
}

.stat-value.text-success {
  color: #10b981;
}

.stat-value.text-danger {
  color: #ef4444;
}

.stat-value.text-primary {
  color: #409eff;
}

.stat-desc {
  font-size: 12px;
  color: #c0c4cc;
}

.charts-grid {
  display: grid;
  grid-template-columns: repeat(12, 1fr);
  gap: 16px;
}

.chart-card {
  grid-column: span 12;
}

.chart-card:first-child {
  grid-column: span 12;
}

.chart-card:nth-child(2) {
  grid-column: span 12;
}

.chart-card:nth-child(3),
.chart-card:nth-child(4) {
  grid-column: span 6;
}

.chart-card.full-width {
  grid-column: span 12;
}

@media (min-width: 1200px) {
  .chart-card:first-child {
    grid-column: span 8;
  }

  .chart-card:nth-child(2) {
    grid-column: span 4;
  }
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.card-subtitle {
  font-size: 12px;
  color: #909399;
}

.chart {
  height: 300px;
  width: 100%;
  min-height: 300px;
}

.pie-chart-container {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.pie-chart {
  height: 200px;
  width: 100%;
}

.pie-legend {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-top: 16px;
  width: 100%;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.legend-color {
  width: 12px;
  height: 12px;
  border-radius: 2px;
}

.legend-name {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
}

.legend-value {
  font-size: 12px;
  color: #909399;
}

.flaky-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.flaky-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
}

.flaky-content {
  flex: 1;
}

.flaky-name {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
  margin-bottom: 4px;
}

.flaky-desc {
  font-size: 12px;
  color: #909399;
}

.sidebar-panels {
  grid-column: span 12;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

@media (min-width: 1200px) {
  .sidebar-panels {
    grid-column: span 4;
  }

  .chart-card.full-width {
    grid-column: span 8;
  }
}

.sidebar-card {
  width: 100%;
}

.env-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.env-item {
  padding: 12px;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
}

.env-label {
  font-size: 12px;
  color: #909399;
  margin-bottom: 4px;
}

.env-status {
  font-size: 14px;
  font-weight: 500;
  margin-bottom: 4px;
}

.status-online {
  color: #10b981;
}

.status-offline {
  color: #ef4444;
}

.env-desc {
  font-size: 12px;
  color: #c0c4cc;
}

.quick-actions {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.dashboard-footer {
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px solid #e4e7ed;
  font-size: 12px;
  color: #c0c4cc;
  text-align: center;
}

/* 动画效果 */
.fade-up-enter-active,
.fade-up-leave-active {
  transition: all 0.3s ease;
}

.fade-up-enter-from {
  opacity: 0;
  transform: translateY(10px);
}

.fade-up-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}
</style>
