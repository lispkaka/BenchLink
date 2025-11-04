<template>
  <div class="performance-tests-container">
    <!-- 顶部导航栏 -->
    <header class="performance-tests-header">
      <div class="header-left">
        <h1 class="title">性能测试</h1>
        <p class="subtitle">管理和执行接口性能测试</p>
      </div>

      <div class="header-right">
        <el-select v-model="projectFilter" style="width: 200px" placeholder="筛选项目" clearable @change="loadPerformanceTests">
          <el-option v-for="project in projects" :key="project.id" :label="project.name" :value="project.id" />
        </el-select>
        <el-button type="primary" @click="handleCreate">
          <el-icon><Plus /></el-icon>
          新建性能测试
        </el-button>
      </div>
    </header>

    <!-- 性能测试列表 -->
    <el-card class="table-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <span class="card-title">性能测试列表</span>
          <span class="card-subtitle">共 {{ performanceTests.length }} 个测试</span>
        </div>
      </template>

      <el-table
        :data="performanceTests"
        stripe
        style="width: 100%"
        v-loading="loading"
        empty-text="暂无性能测试"
      >
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="测试名称" min-width="200" show-overflow-tooltip />
        <el-table-column label="关联接口" min-width="180">
          <template #default="{ row }">
            {{ row.api?.name || '-' }}
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
              <div class="result-info">
                <el-tag :type="row.last_result.success ? 'success' : 'danger'" size="small" style="margin-bottom: 4px">
                  {{ row.last_result.success ? '成功' : '失败' }}
                </el-tag>
                <div class="result-metrics">
                  <span>TPS: {{ (row.last_result.metrics.throughput || 0).toFixed(2) }}</span>
                  <span>平均: {{ (row.last_result.metrics.avg_response_time || 0).toFixed(0) }}ms</span>
                </div>
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
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="handleEdit(row)">
              编辑
            </el-button>
            <el-button type="success" link size="small" @click="handleExecute(row)" :loading="row.executing">
              执行
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
        <el-form-item label="测试名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入性能测试名称" />
        </el-form-item>
        <el-form-item label="所属项目" prop="project_id">
          <el-select
            v-model="form.project_id"
            placeholder="请选择项目"
            style="width: 100%"
            @change="handleProjectChange"
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
            placeholder="请先选择项目"
            :disabled="!form.project_id"
            style="width: 100%"
          >
            <el-option
              v-for="api in projectAPIs"
              :key="api.id"
              :label="api.name"
              :value="api.id"
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
            placeholder="请输入测试描述"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">
          保存
        </el-button>
      </template>
    </el-dialog>

    <!-- 执行结果对话框 -->
    <el-dialog
      v-model="resultDialog"
      title="性能测试结果"
      width="900px"
    >
      <div v-if="executionResult">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="测试状态">
            <el-tag :type="executionResult.success ? 'success' : 'danger'" size="small">
              {{ executionResult.success ? '成功' : '失败' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="总样本数">
            {{ executionResult.result?.metrics?.total_samples || 0 }}
          </el-descriptions-item>
          <el-descriptions-item label="成功样本">
            {{ executionResult.result?.metrics?.success_samples || 0 }}
          </el-descriptions-item>
          <el-descriptions-item label="失败样本">
            {{ executionResult.result?.metrics?.failed_samples || 0 }}
          </el-descriptions-item>
          <el-descriptions-item label="错误率">
            {{ (executionResult.result?.metrics?.error_rate || 0).toFixed(2) }}%
          </el-descriptions-item>
          <el-descriptions-item label="吞吐量(TPS)">
            {{ (executionResult.result?.metrics?.throughput || 0).toFixed(2) }}
          </el-descriptions-item>
          <el-descriptions-item label="平均响应时间">
            {{ (executionResult.result?.metrics?.avg_response_time || 0).toFixed(2) }}ms
          </el-descriptions-item>
          <el-descriptions-item label="最小响应时间">
            {{ executionResult.result?.metrics?.min_response_time || 0 }}ms
          </el-descriptions-item>
          <el-descriptions-item label="最大响应时间">
            {{ executionResult.result?.metrics?.max_response_time || 0 }}ms
          </el-descriptions-item>
          <el-descriptions-item label="中位数响应时间">
            {{ executionResult.result?.metrics?.median_response_time || 0 }}ms
          </el-descriptions-item>
          <el-descriptions-item label="P90响应时间">
            {{ executionResult.result?.metrics?.p90_response_time || 0 }}ms
          </el-descriptions-item>
          <el-descriptions-item label="P95响应时间">
            {{ executionResult.result?.metrics?.p95_response_time || 0 }}ms
          </el-descriptions-item>
          <el-descriptions-item label="P99响应时间">
            {{ executionResult.result?.metrics?.p99_response_time || 0 }}ms
          </el-descriptions-item>
          <el-descriptions-item label="测试耗时" :span="2">
            {{ (executionResult.result?.duration || 0).toFixed(2) }}秒
          </el-descriptions-item>
        </el-descriptions>
        <el-divider>错误信息</el-divider>
        <el-alert
          v-if="executionResult.error"
          :title="executionResult.error"
          type="error"
          :closable="false"
          style="margin-bottom: 20px"
        />
        <div v-if="executionResult.result?.html_report">
          <el-alert
            title="完整的 HTML 报告已生成"
            type="info"
            :closable="false"
            style="margin-bottom: 20px"
          >
            <template #default>
              <div>报告路径: {{ executionResult.result.html_report }}</div>
            </template>
          </el-alert>
        </div>
      </div>
      <template #footer>
        <el-button type="primary" @click="resultDialog = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import {
  getPerformanceTests,
  createPerformanceTest,
  updatePerformanceTest,
  deletePerformanceTest,
  executePerformanceTest
} from '../api/performanceTests'
import { getProjects } from '../api/projects'
import { getAPIs } from '../api/apis'
import { getEnvironments } from '../api/environments'

const loading = ref(false)
const projectFilter = ref(null)
const performanceTests = ref([])
const projects = ref([])
const projectAPIs = ref([])
const environments = ref([])

const dialogVisible = ref(false)
const dialogTitle = ref('新建性能测试')
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
  name: [{ required: true, message: '请输入测试名称', trigger: 'blur' }],
  project_id: [{ required: true, message: '请选择项目', trigger: 'change' }],
  api_id: [{ required: true, message: '请选择接口', trigger: 'change' }],
  threads: [{ required: true, message: '请输入并发线程数', trigger: 'blur' }],
  ramp_up: [{ required: true, message: '请输入启动时间', trigger: 'blur' }]
}

const resultDialog = ref(false)
const executionResult = ref(null)

const loadPerformanceTests = async () => {
  loading.value = true
  try {
    const params = {}
    if (projectFilter.value) {
      params.project_id = projectFilter.value
    }
    const response = await getPerformanceTests(params)
    if (response.results) {
      performanceTests.value = response.results
    } else if (Array.isArray(response)) {
      performanceTests.value = response
    } else {
      performanceTests.value = []
    }
  } catch (error) {
    console.error('加载性能测试列表失败:', error)
    ElMessage.error('加载性能测试列表失败')
  } finally {
    loading.value = false
  }
}

const loadProjects = async () => {
  try {
    const response = await getProjects()
    if (response.results) {
      projects.value = response.results
    } else if (Array.isArray(response)) {
      projects.value = response
    } else {
      projects.value = []
    }
  } catch (error) {
    console.error('加载项目列表失败:', error)
  }
}

const loadProjectAPIs = async (projectId) => {
  if (!projectId) {
    projectAPIs.value = []
    return
  }
  try {
    const response = await getAPIs({ project_id: projectId })
    if (response.results) {
      projectAPIs.value = response.results
    } else if (Array.isArray(response)) {
      projectAPIs.value = response
    } else {
      projectAPIs.value = []
    }
  } catch (error) {
    console.error('加载接口列表失败:', error)
  }
}

const loadEnvironments = async (projectId) => {
  if (!projectId) {
    environments.value = []
    return
  }
  try {
    const response = await getEnvironments({ project_id: projectId })
    if (response.results) {
      environments.value = response.results
    } else if (Array.isArray(response)) {
      environments.value = response
    } else {
      environments.value = []
    }
  } catch (error) {
    console.error('加载环境列表失败:', error)
  }
}

const handleCreate = () => {
  dialogTitle.value = '新建性能测试'
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
  projectAPIs.value = []
  environments.value = []
  dialogVisible.value = true
}

const handleEdit = (row) => {
  dialogTitle.value = '编辑性能测试'
  form.value = {
    id: row.id,
    name: row.name,
    project_id: row.project?.id || row.project_id,
    api_id: row.api?.id || row.api_id,
    environment_id: row.environment?.id || row.environment_id,
    threads: row.threads,
    ramp_up: row.ramp_up,
    duration: row.duration,
    loops: row.loops,
    description: row.description || ''
  }
  if (form.value.project_id) {
    loadProjectAPIs(form.value.project_id)
    loadEnvironments(form.value.project_id)
  }
  dialogVisible.value = true
}

const handleProjectChange = () => {
  form.value.api_id = null
  form.value.environment_id = null
  if (form.value.project_id) {
    loadProjectAPIs(form.value.project_id)
    loadEnvironments(form.value.project_id)
  } else {
    projectAPIs.value = []
    environments.value = []
  }
}

const handleSubmit = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (valid) {
      submitting.value = true
      try {
        const submitData = {
          ...form.value,
          project_id: form.value.project_id,
          api_id: form.value.api_id
        }
        delete submitData.id
        
        if (form.value.id) {
          await updatePerformanceTest(form.value.id, submitData)
          ElMessage.success('更新成功')
        } else {
          await createPerformanceTest(submitData)
          ElMessage.success('创建成功')
        }
        dialogVisible.value = false
        await loadPerformanceTests()
      } catch (error) {
        console.error('保存失败:', error)
        ElMessage.error(error.response?.data?.detail || error.response?.data?.error || '保存失败')
      } finally {
        submitting.value = false
      }
    }
  })
}

const handleExecute = async (row) => {
  try {
    row.executing = true
    const result = await executePerformanceTest(row.id)
    
    executionResult.value = result
    resultDialog.value = true
    
    if (result.success) {
      ElMessage.success('性能测试执行成功')
      await loadPerformanceTests() // 刷新列表以显示最新结果
    } else {
      ElMessage.error(result.error || '性能测试执行失败')
    }
  } catch (error) {
    console.error('执行失败:', error)
    ElMessage.error(error.response?.data?.error || error.response?.data?.detail || '执行失败')
  } finally {
    row.executing = false
  }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(`确定要删除性能测试 "${row.name}" 吗？`, '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    await deletePerformanceTest(row.id)
    ElMessage.success('删除成功')
    await loadPerformanceTests()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
      ElMessage.error(error.response?.data?.detail || '删除失败')
    }
  }
}

const handleDialogClose = () => {
  formRef.value?.resetFields()
  projectAPIs.value = []
  environments.value = []
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
  loadPerformanceTests()
  loadProjects()
})
</script>

<style scoped>
.performance-tests-container {
  padding: 24px;
  background-color: #f5f7fa;
  min-height: calc(100vh - 60px);
}

.performance-tests-header {
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

.result-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.result-metrics {
  font-size: 12px;
  color: #606266;
  display: flex;
  gap: 8px;
}

.text-gray {
  color: #909399;
  font-size: 12px;
}

.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}
</style>

