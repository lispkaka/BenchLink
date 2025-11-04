<template>
  <div class="performance-scripts-container">
    <header class="page-header">
      <div class="header-left">
        <h1 class="title">脚本管理</h1>
        <p class="subtitle">管理自定义 Locust 性能测试脚本</p>
      </div>
      <div class="header-right">
        <el-button type="primary" @click="handleCreate">
          <el-icon><Plus /></el-icon>
          新建脚本
        </el-button>
      </div>
    </header>

    <el-alert
      title="脚本说明"
      type="info"
      :closable="false"
      style="margin-bottom: 24px"
    >
      <template #default>
        <div style="line-height: 1.8;">
          <p>您可以创建自定义的 Locust 性能测试脚本，用于更复杂的测试场景。</p>
          <p>脚本将自动应用到关联的性能测试任务中。</p>
        </div>
      </template>
    </el-alert>

    <el-card class="table-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <span class="card-title">脚本列表</span>
          <span class="card-subtitle">共 {{ scripts.length }} 个脚本</span>
        </div>
      </template>

      <el-table
        :data="scripts"
        stripe
        style="width: 100%"
        v-loading="loading"
        empty-text="暂无脚本"
      >
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="脚本名称" min-width="200" show-overflow-tooltip />
        <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
        <el-table-column label="关联任务" width="200">
          <template #default="{ row }">
            <span v-if="row.task_count > 0">{{ row.task_count }} 个任务</span>
            <span v-else class="text-gray">未关联</span>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            <span class="text-gray">{{ formatDate(row.created_at) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="handleEdit(row)">
              编辑
            </el-button>
            <el-button type="info" link size="small" @click="handleView(row)">
              查看
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
      width="900px"
      @close="handleDialogClose"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="formRules"
        label-width="120px"
      >
        <el-form-item label="脚本名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入脚本名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="2"
            placeholder="请输入脚本描述"
          />
        </el-form-item>
        <el-form-item label="脚本内容" prop="content">
          <el-input
            v-model="form.content"
            type="textarea"
            :rows="20"
            placeholder="请输入 Locust 脚本内容"
            style="font-family: 'Courier New', monospace;"
          />
          <div class="form-tip">
            <p>提示：脚本需要包含 Locust HttpUser 类，例如：</p>
            <pre style="background: #f5f7fa; padding: 10px; border-radius: 4px; margin-top: 8px; font-size: 12px;">from locust import HttpUser, task, between

class BenchLinkUser(HttpUser):
    wait_time = between(0, 0)
    
    def on_start(self):
        # 初始化代码
        pass
    
    @task
    def api_request(self):
        # 测试请求
        self.client.get("/api/endpoint")
</pre>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSave" :loading="submitting">
          保存
        </el-button>
      </template>
    </el-dialog>

    <!-- 查看脚本对话框 -->
    <el-dialog
      v-model="viewDialogVisible"
      title="查看脚本"
      width="900px"
    >
      <div v-if="currentScript">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="脚本名称">
            {{ currentScript.name }}
          </el-descriptions-item>
          <el-descriptions-item label="描述">
            {{ currentScript.description || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="创建时间">
            {{ formatDate(currentScript.created_at) }}
          </el-descriptions-item>
        </el-descriptions>
        <el-divider>脚本内容</el-divider>
        <el-input
          :model-value="currentScript.content"
          type="textarea"
          :rows="20"
          readonly
          style="font-family: 'Courier New', monospace;"
        />
      </div>
      <template #footer>
        <el-button type="primary" @click="viewDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
// TODO: 创建 API 文件用于脚本管理
// import { getPerformanceScripts, createPerformanceScript, updatePerformanceScript, deletePerformanceScript } from '../../api/performanceScripts'

const loading = ref(false)
const scripts = ref([])
const dialogVisible = ref(false)
const dialogTitle = ref('新建脚本')
const viewDialogVisible = ref(false)
const currentScript = ref(null)
const formRef = ref(null)
const submitting = ref(false)

const form = ref({
  id: null,
  name: '',
  description: '',
  content: ''
})

const formRules = {
  name: [{ required: true, message: '请输入脚本名称', trigger: 'blur' }],
  content: [{ required: true, message: '请输入脚本内容', trigger: 'blur' }]
}

const loadScripts = async () => {
  loading.value = true
  try {
    // TODO: 实现脚本列表 API
    // const response = await getPerformanceScripts()
    // scripts.value = response.results || response || []
    scripts.value = [] // 临时空数组
    ElMessage.info('脚本管理功能开发中，请稍后...')
  } catch (error) {
    console.error('加载脚本列表失败:', error)
    ElMessage.error('加载脚本列表失败')
  } finally {
    loading.value = false
  }
}

const handleCreate = () => {
  dialogTitle.value = '新建脚本'
  form.value = {
    id: null,
    name: '',
    description: '',
    content: `from locust import HttpUser, task, between

class BenchLinkUser(HttpUser):
    wait_time = between(0, 0)
    
    def on_start(self):
        # 初始化代码
        pass
    
    @task
    def api_request(self):
        # 测试请求
        self.client.get("/api/endpoint")
`
  }
  dialogVisible.value = true
}

const handleEdit = (row) => {
  dialogTitle.value = '编辑脚本'
  form.value = {
    id: row.id,
    name: row.name,
    description: row.description || '',
    content: row.content || ''
  }
  dialogVisible.value = true
}

const handleView = (row) => {
  currentScript.value = row
  viewDialogVisible.value = true
}

const handleSave = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (valid) {
      submitting.value = true
      try {
        // TODO: 实现保存脚本 API
        // if (form.value.id) {
        //   await updatePerformanceScript(form.value.id, form.value)
        //   ElMessage.success('更新成功')
        // } else {
        //   await createPerformanceScript(form.value)
        //   ElMessage.success('创建成功')
        // }
        ElMessage.info('脚本管理功能开发中，请稍后...')
        dialogVisible.value = false
        await loadScripts()
      } catch (error) {
        console.error('保存失败:', error)
        ElMessage.error(error.response?.data?.detail || error.response?.data?.error || '保存失败')
      } finally {
        submitting.value = false
      }
    }
  })
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(`确定要删除脚本 "${row.name}" 吗？`, '确认删除', {
      type: 'warning'
    })
    // TODO: 实现删除脚本 API
    // await deletePerformanceScript(row.id)
    ElMessage.info('脚本管理功能开发中，请稍后...')
    await loadScripts()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
      ElMessage.error(error.response?.data?.detail || '删除失败')
    }
  }
}

const handleDialogClose = () => {
  formRef.value?.resetFields()
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
  loadScripts()
})
</script>

<style scoped>
.performance-scripts-container {
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

.text-gray {
  color: #909399;
  font-size: 12px;
}

.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.form-tip pre {
  white-space: pre-wrap;
  word-wrap: break-word;
}
</style>

