<template>
  <div class="performance-reports-container">
    <header class="page-header">
      <div class="header-left">
        <h1 class="title">测试报告</h1>
        <p class="subtitle">查看性能测试执行报告和历史记录</p>
      </div>
      <div class="header-right">
        <el-select v-model="taskFilter" style="width: 200px" placeholder="筛选任务" clearable @change="loadReports">
          <el-option v-for="task in tasks" :key="task.id" :label="task.name" :value="task.id" />
        </el-select>
      </div>
    </header>

    <el-card class="table-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <span class="card-title">报告列表</span>
          <span class="card-subtitle">共 {{ filteredReports.length }} 份报告</span>
        </div>
      </template>

      <el-table
        :data="filteredReports"
        stripe
        style="width: 100%"
        v-loading="loading"
        empty-text="暂无报告"
      >
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="task_name" label="任务名称" min-width="200" show-overflow-tooltip />
        <el-table-column label="测试状态" width="120">
          <template #default="{ row }">
            <el-tag :type="row.success ? 'success' : 'danger'" size="small">
              {{ row.success ? '成功' : '失败' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="性能指标" width="300">
          <template #default="{ row }">
            <div v-if="row.metrics" class="metrics-info">
              <div>总样本: {{ row.metrics.total_samples || 0 }}</div>
              <div>TPS: {{ (row.metrics.throughput || 0).toFixed(2) }}</div>
              <div>平均响应: {{ (row.metrics.avg_response_time || 0).toFixed(0) }}ms</div>
              <div>错误率: {{ (row.metrics.error_rate || 0).toFixed(2) }}%</div>
            </div>
            <span v-else class="text-gray">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="execution_time" label="执行时间" width="180">
          <template #default="{ row }">
            <span class="text-gray">{{ formatDate(row.execution_time) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="duration" label="测试耗时" width="120">
          <template #default="{ row }">
            <span v-if="row.duration">{{ row.duration.toFixed(2) }}s</span>
            <span v-else class="text-gray">-</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="handleViewDetail(row)">
              查看详情
            </el-button>
            <el-button type="info" link size="small" @click="handleViewHTML(row)" v-if="row.html_report">
              HTML报告
            </el-button>
            <el-button type="danger" link size="small" @click="handleDelete(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 报告详情对话框 -->
    <el-dialog
      v-model="detailDialogVisible"
      title="测试报告详情"
      width="1000px"
    >
      <div v-if="currentReport">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="任务名称">
            {{ currentReport.task_name }}
          </el-descriptions-item>
          <el-descriptions-item label="测试状态">
            <el-tag :type="currentReport.success ? 'success' : 'danger'" size="small">
              {{ currentReport.success ? '成功' : '失败' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="总样本数">
            {{ currentReport.metrics?.total_samples || 0 }}
          </el-descriptions-item>
          <el-descriptions-item label="成功样本">
            {{ currentReport.metrics?.success_samples || 0 }}
          </el-descriptions-item>
          <el-descriptions-item label="失败样本">
            {{ currentReport.metrics?.failed_samples || 0 }}
          </el-descriptions-item>
          <el-descriptions-item label="错误率">
            {{ (currentReport.metrics?.error_rate || 0).toFixed(2) }}%
          </el-descriptions-item>
          <el-descriptions-item label="吞吐量(TPS)">
            {{ (currentReport.metrics?.throughput || 0).toFixed(2) }}
          </el-descriptions-item>
          <el-descriptions-item label="平均响应时间">
            {{ (currentReport.metrics?.avg_response_time || 0).toFixed(2) }}ms
          </el-descriptions-item>
          <el-descriptions-item label="最小响应时间">
            {{ currentReport.metrics?.min_response_time ? currentReport.metrics.min_response_time.toFixed(2) : 0 }}ms
          </el-descriptions-item>
          <el-descriptions-item label="最大响应时间">
            {{ currentReport.metrics?.max_response_time || 0 }}ms
          </el-descriptions-item>
          <el-descriptions-item label="中位数响应时间">
            {{ currentReport.metrics?.median_response_time || 0 }}ms
          </el-descriptions-item>
          <el-descriptions-item label="P90响应时间">
            {{ currentReport.metrics?.p90_response_time || 0 }}ms
          </el-descriptions-item>
          <el-descriptions-item label="P95响应时间">
            {{ currentReport.metrics?.p95_response_time || 0 }}ms
          </el-descriptions-item>
          <el-descriptions-item label="P99响应时间">
            {{ currentReport.metrics?.p99_response_time || 0 }}ms
          </el-descriptions-item>
          <el-descriptions-item label="执行时间" :span="2">
            {{ formatDate(currentReport.execution_time) }}
          </el-descriptions-item>
          <el-descriptions-item label="测试耗时" :span="2">
            {{ currentReport.duration ? currentReport.duration.toFixed(2) + 's' : '-' }}
          </el-descriptions-item>
        </el-descriptions>
        <el-divider>执行日志</el-divider>
        <el-collapse v-model="logCollapse" style="margin-bottom: 20px">
          <el-collapse-item name="log">
            <template #title>
              <span>查看执行日志（{{ currentReport.log ? '点击展开' : '暂无日志' }}）</span>
            </template>
            <pre v-if="currentReport.log" style="background: #f5f7fa; padding: 12px; border-radius: 4px; max-height: 400px; overflow-y: auto; font-size: 12px; white-space: pre-wrap; word-wrap: break-word;">{{ currentReport.log }}</pre>
            <div v-else style="color: #909399; padding: 20px; text-align: center;">
              无执行日志
            </div>
          </el-collapse-item>
        </el-collapse>
        
        <el-divider v-if="currentReport.error">错误信息</el-divider>
        <el-alert
          v-if="currentReport.error"
          :title="currentReport.error"
          type="error"
          :closable="false"
          style="margin-bottom: 20px"
        />
        <el-divider v-if="currentReport.html_report">报告文件</el-divider>
        <el-alert
          v-if="currentReport.html_report"
          title="HTML 报告已生成"
          type="info"
          :closable="false"
        >
          <template #default>
            <div>报告路径: {{ currentReport.html_report }}</div>
          </template>
        </el-alert>
      </div>
      <template #footer>
        <el-button type="primary" @click="detailDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getPerformanceTests } from '../../api/performanceTests'
// TODO: 创建 API 文件用于报告管理
// import { getPerformanceReports, deletePerformanceReport } from '../../api/performanceReports'

const route = useRoute()
const loading = ref(false)
const taskFilter = ref(null)
const reports = ref([])
const tasks = ref([])

// 从路由参数获取任务ID
const taskIdFromRoute = computed(() => route.query.task_id)

const filteredReports = computed(() => {
  let filtered = reports.value
  if (taskFilter.value) {
    filtered = filtered.filter(report => report.task_id === taskFilter.value)
  }
  return filtered
})

const loadTasks = async () => {
  try {
    const response = await getPerformanceTests()
    tasks.value = response.results || response || []
  } catch (error) {
    console.error('加载任务列表失败:', error)
  }
}

const loadReports = async () => {
  loading.value = true
  try {
    // TODO: 实现报告列表 API
    // const response = await getPerformanceReports(taskFilter.value ? { task_id: taskFilter.value } : {})
    // reports.value = response.results || response || []
    
    // 临时方案：从任务列表中提取报告
    const response = await getPerformanceTests()
    const allTasks = response.results || response || []
    reports.value = []
    
    allTasks.forEach(task => {
      if (task.last_result && task.last_execution_time) {
        reports.value.push({
          id: task.id,
          task_id: task.id,
          task_name: task.name,
          success: task.last_result.success,
          metrics: task.last_result.metrics || task.last_result.result?.metrics,
          error: task.last_result.error,
          log: task.last_result.log || task.last_result.result?.log,  // 添加日志字段
          execution_time: task.last_execution_time,
          duration: task.last_result.duration || task.last_result.result?.duration,
          html_report: task.last_result.html_report || task.last_result.result?.html_report
        })
      }
    })
    
    // 如果路由中有 task_id，自动筛选
    if (taskIdFromRoute.value) {
      taskFilter.value = parseInt(taskIdFromRoute.value)
    }
  } catch (error) {
    console.error('加载报告列表失败:', error)
    ElMessage.error('加载报告列表失败')
  } finally {
    loading.value = false
  }
}

const detailDialogVisible = ref(false)
const currentReport = ref(null)
const logCollapse = ref([])

const handleViewDetail = (row) => {
  currentReport.value = row
  detailDialogVisible.value = true
}

const handleViewHTML = async (row) => {
  if (!row.html_report) {
    ElMessage.warning('该报告未生成HTML文件')
    return
  }
  
  try {
    // 使用API获取HTML报告内容（这样可以携带认证Token）
    // 需要直接使用axios，因为我们需要访问response.data（Blob对象）
    const axios = (await import('axios')).default
    const apiInstance = (await import('../../api/index')).default
    const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null
    
    // 使用axios直接调用，因为api实例的拦截器会处理response.data
    const response = await axios({
      method: 'get',
      url: `/testcases/performance-tests/${row.task_id}/html_report/`,
      baseURL: apiInstance.defaults.baseURL,
      responseType: 'blob',  // 获取二进制数据
      timeout: 30000,  // 30秒超时
      headers: {
        'Authorization': token ? `Token ${token}` : '',
        'Content-Type': 'application/json'
      }
    })
    
    // 创建Blob URL
    const blobURL = URL.createObjectURL(response.data)
    
    // 在新窗口打开
    const newWindow = window.open(blobURL, '_blank')
    
    // 清理Blob URL（当窗口关闭时）
    if (newWindow) {
      newWindow.addEventListener('beforeunload', () => {
        URL.revokeObjectURL(blobURL)
      })
      // 如果窗口立即关闭，也清理URL
      setTimeout(() => {
        if (newWindow.closed) {
          URL.revokeObjectURL(blobURL)
        }
      }, 1000)
    } else {
      // 如果弹窗被阻止，清理URL
      URL.revokeObjectURL(blobURL)
      ElMessage.warning('请允许弹窗以查看HTML报告')
    }
  } catch (error) {
    console.error('打开HTML报告失败:', error)
    if (error.response?.status === 403) {
      ElMessage.error('无权限访问HTML报告，请重新登录')
    } else if (error.response?.status === 404) {
      ElMessage.error('HTML报告文件不存在')
    } else {
      ElMessage.error(error.response?.data?.error || error.message || '打开HTML报告失败')
    }
  }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(`确定要删除报告吗？`, '确认删除', {
      type: 'warning'
    })
    // TODO: 实现删除报告 API
    // await deletePerformanceReport(row.id)
    ElMessage.info('删除报告功能开发中，请稍后...')
    await loadReports()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
      ElMessage.error(error.response?.data?.detail || '删除失败')
    }
  }
}

const formatDate = (dateString) => {
  if (!dateString) return '-'
  const date = new Date(dateString)
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  return `${year}-${month}-${day} ${hours}:${minutes}`
}

onMounted(() => {
  loadTasks()
  loadReports()
})
</script>

<style scoped>
.performance-reports-container {
  padding: 24px;
  background-color: #f5f7fa;
  min-height: calc(100vh - 60px);
}

.page-header {
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
}

.table-card {
  margin-bottom: 24px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-title {
  font-weight: 600;
  font-size: 16px;
}

.card-subtitle {
  color: #909399;
  font-size: 14px;
}

.metrics-info {
  font-size: 12px;
  color: #606266;
  line-height: 1.8;
}

.text-gray {
  color: #909399;
  font-size: 12px;
}
</style>

