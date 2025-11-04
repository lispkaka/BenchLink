<template>
  <div class="performance-task-create-container">
    <header class="page-header">
      <div class="header-left">
        <h1 class="title">{{ isEdit ? '编辑任务' : '新建任务' }}</h1>
        <p class="subtitle">{{ isEdit ? '编辑性能测试任务配置' : '创建新的性能测试任务' }}</p>
      </div>
      <div class="header-right">
        <el-button @click="$router.back()">返回</el-button>
      </div>
    </header>

    <el-card class="form-card" shadow="hover">
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
      <div class="form-actions">
        <el-button @click="$router.back()">取消</el-button>
        <el-button type="primary" @click="handleSave" :loading="submitting">
          {{ isEdit ? '更新' : '创建' }}
        </el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getProjects } from '../../api/projects'
import { getAPIs } from '../../api/apis'
import { getEnvironments } from '../../api/environments'
import { getPerformanceTest, createPerformanceTest, updatePerformanceTest } from '../../api/performanceTests'

const route = useRoute()
const router = useRouter()
const formRef = ref(null)
const submitting = ref(false)
const projects = ref([])
const apis = ref([])
const environments = ref([])

const taskId = computed(() => {
  const id = route.query.id
  return id ? parseInt(id) : null
})
const isEdit = computed(() => !!taskId.value)

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

const loadEnvironments = async (projectId) => {
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

const loadTask = async () => {
  if (!taskId.value) return
  try {
    const response = await getPerformanceTest(taskId.value)
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
    await loadEnvironments(form.value.project_id)
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
        router.push('/performance/tasks')
      } catch (error) {
        console.error('保存失败:', error)
        ElMessage.error(error.response?.data?.detail || error.response?.data?.error || '保存失败')
      } finally {
        submitting.value = false
      }
    }
  })
}

onMounted(async () => {
  await loadProjects()
  if (taskId.value) {
    await loadTask()
  }
})
</script>

<style scoped>
.performance-task-create-container {
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

.form-card {
  max-width: 900px;
  margin: 0 auto;
}

.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 20px 0;
  border-top: 1px solid #ebeef5;
  margin-top: 20px;
}
</style>

