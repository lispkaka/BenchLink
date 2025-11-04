<template>
  <div class="performance-task-list-container">
    <header class="page-header">
      <div class="header-left">
        <h1 class="title">性能测试</h1>
        <p class="subtitle">管理和执行接口性能测试任务</p>
      </div>
      <div class="header-right">
        <el-select v-model="projectFilter" style="width: 200px" placeholder="筛选项目" clearable @change="loadTasks">
          <el-option v-for="project in projects" :key="project.id" :label="project.name" :value="project.id" />
        </el-select>
        <el-button type="primary" @click="handleCreate">
          <el-icon><Plus /></el-icon>
          新建任务
        </el-button>
      </div>
    </header>

    <el-card class="table-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <span class="card-title">性能测试任务</span>
          <span class="card-subtitle">共 {{ filteredTasks.length }} 个任务</span>
        </div>
      </template>

      <el-table
        :data="filteredTasks"
        stripe
        style="width: 100%"
        v-loading="loading"
        empty-text="暂无任务"
      >
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="任务名称" min-width="200" show-overflow-tooltip />
        <el-table-column label="关联接口" min-width="180">
          <template #default="{ row }">
            <div>
              <div>{{ row.api?.name || '-' }}</div>
              <div class="text-gray" style="font-size: 12px;">{{ row.api?.method }} {{ row.api?.url }}</div>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="所属项目" width="150">
          <template #default="{ row }">
            {{ row.project?.name || '-' }}
          </template>
        </el-table-column>
        <el-table-column label="并发配置" width="150">
          <template #default="{ row }">
            <div class="config-info">
              <div>线程: {{ row.threads }}</div>
              <div>启动: {{ row.ramp_up }}s</div>
              <div>持续: {{ row.duration }}s</div>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="最新结果" width="200">
          <template #default="{ row }">
            <div v-if="row.last_result && row.last_result.metrics">
              <el-tag :type="row.last_result.success ? 'success' : 'danger'" size="small" style="margin-bottom: 4px">
                {{ row.last_result.success ? '成功' : '失败' }}
              </el-tag>
              <div class="result-metrics">
                <span>TPS: {{ (row.last_result.metrics.throughput || 0).toFixed(2) }}</span>
                <span>平均: {{ (row.last_result.metrics.avg_response_time || 0).toFixed(0) }}ms</span>
              </div>
            </div>
            <span v-else class="text-gray">暂无结果</span>
          </template>
        </el-table-column>
        <el-table-column prop="last_execution_time" label="执行时间" width="180">
          <template #default="{ row }">
            <span v-if="row.last_execution_time" class="text-gray">{{ formatDate(row.last_execution_time) }}</span>
            <span v-else class="text-gray">-</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="280" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="handleEdit(row)">
              编辑
            </el-button>
            <el-button type="success" link size="small" @click="handleExecute(row)" :loading="row.executing">
              执行
            </el-button>
            <el-button type="info" link size="small" @click="handleViewReport(row)" v-if="row.last_result">
              查看报告
            </el-button>
            <el-button type="danger" link size="small" @click="handleDelete(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 创建/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="700px"
      @close="handleDialogClose"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="formRules"
        label-width="140px"
        style="margin-top: 20px"
      >
        <el-form-item label="任务名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入任务名称" />
        </el-form-item>
        <el-form-item label="所属项目" prop="project_id">
          <el-select
            v-model="form.project_id"
            placeholder="请选择项目"
            style="width: 100%"
            @change="loadAPIsForProject"
          >
            <el-option
              v-for="project in projects"
              :key="project.id"
              :label="project.name"
              :value="project.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="关联接口" prop="api_id">
          <el-select
            v-model="form.api_id"
            placeholder="请选择关联接口"
            style="width: 100%"
            :disabled="!form.project_id"
          >
            <el-option
              v-for="apiItem in apis"
              :key="apiItem.id"
              :label="`${apiItem.name} (${apiItem.method} ${apiItem.url})`"
              :value="apiItem.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="测试环境">
          <el-select
            v-model="form.environment_id"
            placeholder="请选择测试环境"
            clearable
            style="width: 100%"
          >
            <el-option
              v-for="env in environments"
              :key="env.id"
              :label="env.name"
              :value="env.id"
            />
          </el-select>
        </el-form-item>
        <el-divider>性能参数</el-divider>
        <el-form-item label="并发线程数" prop="threads">
          <el-input-number
            v-model="form.threads"
            :min="1"
            :max="1000"
            style="width: 100%"
          />
          <div class="form-tip">同时运行的虚拟用户数</div>
        </el-form-item>
        <el-form-item label="启动时间(秒)" prop="ramp_up">
          <el-input-number
            v-model="form.ramp_up"
            :min="1"
            style="width: 100%"
          />
          <div class="form-tip">所有线程启动完成所需的时间</div>
        </el-form-item>
        <el-form-item label="持续时间(秒)" prop="duration">
          <el-input-number
            v-model="form.duration"
            :min="0"
            style="width: 100%"
          />
          <div class="form-tip">测试持续运行的时间，0表示使用循环次数</div>
        </el-form-item>
        <el-form-item label="循环次数" prop="loops">
          <el-input-number
            v-model="form.loops"
            :min="-1"
            style="width: 100%"
          />
          <div class="form-tip">每个线程执行的次数，-1表示无限循环</div>
        </el-form-item>
        <el-form-item label="描述">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="3"
            placeholder="请输入任务描述"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSave" :loading="submitting">
          {{ isEdit ? '更新' : '创建' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { getProjects } from '../../api/projects'
import { getAPIs } from '../../api/apis'
import { getEnvironments } from '../../api/environments'
import { getPerformanceTests, getPerformanceTest, createPerformanceTest, updatePerformanceTest, deletePerformanceTest, executePerformanceTest } from '../../api/performanceTests'

const router = useRouter()
const loading = ref(false)
const projectFilter = ref(null)
const tasks = ref([])
const projects = ref([])
const apis = ref([])
const environments = ref([])
const dialogVisible = ref(false)
const dialogTitle = ref('新建任务')
const formRef = ref(null)
const submitting = ref(false)

const form = ref({
  id: null,
  name: '',
  project_id: null,
  api_id: null,
  environment_id: null,
  threads: 10,
  ramp_up: 10,
  duration: 60,
  loops: 1,
  description: ''
})

const formRules = {
  name: [{ required: true, message: '请输入任务名称', trigger: 'blur' }],
  project_id: [{ required: true, message: '请选择项目', trigger: 'change' }],
  api_id: [{ required: true, message: '请选择接口', trigger: 'change' }],
  threads: [{ required: true, message: '请输入并发线程数', trigger: 'blur' }],
  ramp_up: [{ required: true, message: '请输入启动时间', trigger: 'blur' }]
}

const isEdit = computed(() => !!form.value.id)

const filteredTasks = computed(() => {
  if (!projectFilter.value) {
    return tasks.value
  }
  return tasks.value.filter(task => task.project_id === projectFilter.value)
})

const loadTasks = async () => {
  loading.value = true
  try {
    const params = projectFilter.value ? { project_id: projectFilter.value } : {}
    const response = await getPerformanceTests(params)
    tasks.value = response.results || response || []
  } catch (error) {
    console.error('加载任务列表失败:', error)
    ElMessage.error('加载任务列表失败')
  } finally {
    loading.value = false
  }
}

const loadProjects = async () => {
  try {
    const response = await getProjects()
    projects.value = response.results || response || []
  } catch (error) {
    console.error('加载项目列表失败:', error)
  }
}

const loadAPIsForProject = async (projectId) => {
  apis.value = []
  form.value.api_id = null
  if (!projectId) return
  try {
    const response = await getAPIs({ project_id: projectId })
    apis.value = response.results || response || []
  } catch (error) {
    console.error('加载接口列表失败:', error)
  }
}

const loadEnvironmentsForProject = async (projectId) => {
  environments.value = []
  form.value.environment_id = null
  if (!projectId) return
  try {
    const response = await getEnvironments({ project_id: projectId })
    environments.value = response.results || response || []
  } catch (error) {
    console.error('加载环境列表失败:', error)
  }
}

const handleCreate = () => {
  dialogTitle.value = '新建任务'
  form.value = {
    id: null,
    name: '',
    project_id: null,
    api_id: null,
    environment_id: null,
    threads: 10,
    ramp_up: 10,
    duration: 60,
    loops: 1,
    description: ''
  }
  apis.value = []
  environments.value = []
  dialogVisible.value = true
}

const handleEdit = async (row) => {
  dialogTitle.value = '编辑任务'
  try {
    const response = await getPerformanceTest(row.id)
    form.value = {
      id: response.id,
      name: response.name,
      project_id: response.project?.id || response.project_id,
      api_id: response.api?.id || response.api_id,
      environment_id: response.environment?.id || response.environment_id,
      threads: response.threads,
      ramp_up: response.ramp_up,
      duration: response.duration,
      loops: response.loops,
      description: response.description || ''
    }
    await loadAPIsForProject(form.value.project_id)
    await loadEnvironmentsForProject(form.value.project_id)
    dialogVisible.value = true
  } catch (error) {
    console.error('加载任务失败:', error)
    ElMessage.error('加载任务失败')
  }
}

const handleSave = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (valid) {
      submitting.value = true
      try {
        const submitData = {
          ...form.value,
          project: form.value.project_id,
          api: form.value.api_id,
          environment: form.value.environment_id
        }
        if (isEdit.value) {
          await updatePerformanceTest(form.value.id, submitData)
          ElMessage.success('更新成功')
        } else {
          await createPerformanceTest(submitData)
          ElMessage.success('创建成功')
        }
        dialogVisible.value = false
        await loadTasks()
      } catch (error) {
        console.error('保存失败:', error)
        ElMessage.error(error.response?.data?.detail || error.response?.data?.error || '保存失败')
      } finally {
        submitting.value = false
      }
    }
  })
}

const handleDialogClose = () => {
  formRef.value?.resetFields()
  apis.value = []
  environments.value = []
}

const handleExecute = async (row) => {
  try {
    row.executing = true
    // 显示执行提示
    const loadingMessage = ElMessage({
      message: '性能测试执行中，请稍候...',
      type: 'info',
      duration: 0,  // 不自动关闭
      showClose: false
    })
    
    try {
      const result = await executePerformanceTest(row.id)
      loadingMessage.close()
      
      if (result.success) {
        ElMessage.success('任务执行成功')
        await loadTasks()
        // 跳转到报告页面
        router.push({
          path: '/performance/reports',
          query: { task_id: row.id }
        })
      } else {
        ElMessage.error(result.error || result.message || '任务执行失败')
      }
    } catch (apiError) {
      loadingMessage.close()
      // 检查是否是超时错误
      if (apiError.code === 'ECONNABORTED' || apiError.message?.includes('timeout')) {
        ElMessage.warning('请求超时，但性能测试可能仍在后台执行中，请稍后查看结果')
        // 延迟刷新列表，看看是否有结果
        setTimeout(async () => {
          await loadTasks()
        }, 5000)
      } else {
        throw apiError  // 重新抛出其他错误
      }
    }
  } catch (error) {
    console.error('执行失败:', error)
    ElMessage.error(error.response?.data?.error || error.response?.data?.detail || error.message || '执行失败')
  } finally {
    row.executing = false
  }
}

const handleViewReport = (row) => {
  router.push({
    path: '/performance/reports',
    query: { task_id: row.id }
  })
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(`确定要删除任务 "${row.name}" 吗？`, '确认删除', {
      type: 'warning'
    })
    await deletePerformanceTest(row.id)
    ElMessage.success('删除成功')
    await loadTasks()
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
  loadProjects()
  loadTasks()
})
</script>

<style scoped>
.performance-task-list-container {
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
  flex-wrap: wrap;
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

.config-info {
  font-size: 12px;
  color: #606266;
  line-height: 1.6;
}

.result-metrics {
  font-size: 12px;
  color: #606266;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.text-gray {
  color: #909399;
  font-size: 12px;
}
</style>

