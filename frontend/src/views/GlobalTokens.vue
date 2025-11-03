<template>
  <div class="global-tokens-container">
    <!-- 顶部导航栏 -->
    <header class="tokens-header">
      <div class="header-left">
        <h1 class="title">全局 Token</h1>
        <p class="subtitle">管理全局 Token 配置，所有未配置认证的接口将自动使用全局 Token</p>
      </div>

      <div class="header-right">
        <el-button type="primary" @click="handleCreate">
          <el-icon><Plus /></el-icon>
          新建 Token
        </el-button>
      </div>
    </header>

    <!-- Token 列表 -->
    <el-card class="table-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <span class="card-title">全局 Token 列表</span>
          <span class="card-subtitle">共 {{ globalTokens.length }} 个 Token</span>
        </div>
      </template>

      <el-table
        :data="globalTokens"
        stripe
        style="width: 100%"
        v-loading="loading"
        empty-text="暂无 Token"
      >
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="Token 名称" min-width="150" show-overflow-tooltip />
        <el-table-column label="认证类型" width="150">
          <template #default="{ row }">
            <el-tag size="small">
              {{ getAuthTypeLabel(row.auth_type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="Token 值" min-width="200" show-overflow-tooltip>
          <template #default="{ row }">
            <code class="token-code">{{ maskToken(row.token) }}</code>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="120">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
              {{ row.is_active ? '启用' : '停用' }}
            </el-tag>
            <el-tag v-if="row.is_default" type="warning" size="small" style="margin-left: 8px">
              默认
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" min-width="150" show-overflow-tooltip />
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="handleEdit(row)">
              编辑
            </el-button>
            <el-button type="danger" link size="small" @click="handleDelete(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- Token 新建/编辑对话框 -->
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
        label-width="120px"
        style="margin-top: 20px"
      >
        <el-form-item label="Token 名称" prop="name">
          <el-input v-model="form.name" placeholder="如：API Token、登录 Token" />
        </el-form-item>
        <el-form-item label="认证类型" prop="auth_type">
          <el-select v-model="form.auth_type" style="width: 100%">
            <el-option label="Bearer Token" value="bearer" />
            <el-option label="Django REST Framework Token" value="drf_token" />
            <el-option label="自定义 Header" value="header" />
          </el-select>
        </el-form-item>
        <el-form-item label="Token 值" prop="token">
          <el-input
            v-model="form.token"
            type="textarea"
            :rows="3"
            placeholder="输入 Token 值，支持变量 ${variable}"
          />
        </el-form-item>
        <el-form-item
          v-if="form.auth_type === 'header'"
          label="Header 名称"
          prop="header_name"
        >
          <el-input v-model="form.header_name" placeholder="如：Authorization" />
        </el-form-item>
        <el-form-item
          v-if="form.auth_type === 'header'"
          label="Token 格式"
          prop="token_format"
        >
          <el-input v-model="form.token_format" placeholder="如：Bearer、Token（留空则不加前缀）" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="2"
            placeholder="说明这个 Token 的用途"
          />
        </el-form-item>
        <el-form-item>
          <el-checkbox v-model="form.is_active">启用</el-checkbox>
          <el-checkbox v-model="form.is_default" style="margin-left: 20px">
            设为默认 Token
          </el-checkbox>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSave" :loading="submitting">
          保存
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import {
  getGlobalTokens,
  createGlobalToken,
  updateGlobalToken,
  deleteGlobalToken
} from '../api/globalTokens'

// 数据定义
const loading = ref(false)
const globalTokens = ref([])
const dialogVisible = ref(false)
const dialogTitle = ref('新建 Token')
const formRef = ref(null)
const submitting = ref(false)
const form = ref({
  id: null,
  name: '',
  auth_type: 'bearer',
  token: '',
  header_name: 'Authorization',
  token_format: 'Bearer',
  description: '',
  is_active: true,
  is_default: false,
  variables: {}
})

const formRules = {
  name: [{ required: true, message: '请输入 Token 名称', trigger: 'blur' }],
  auth_type: [{ required: true, message: '请选择认证类型', trigger: 'change' }],
  token: [{ required: true, message: '请输入 Token 值', trigger: 'blur' }]
}

// 方法
const loadGlobalTokens = async () => {
  loading.value = true
  try {
    const response = await getGlobalTokens()
    if (response.results) {
      globalTokens.value = response.results
    } else if (Array.isArray(response)) {
      globalTokens.value = response
    } else {
      globalTokens.value = []
    }
  } catch (error) {
    console.error('加载 Token 失败:', error)
    ElMessage.error(error.response?.data?.detail || '加载 Token 失败')
  } finally {
    loading.value = false
  }
}

const handleCreate = () => {
  dialogTitle.value = '新建 Token'
  form.value = {
    id: null,
    name: '',
    auth_type: 'bearer',
    token: '',
    header_name: 'Authorization',
    token_format: 'Bearer',
    description: '',
    is_active: true,
    is_default: false,
    variables: {}
  }
  dialogVisible.value = true
}

const handleEdit = (row) => {
  dialogTitle.value = '编辑 Token'
  form.value = { ...row }
  dialogVisible.value = true
}

const handleSave = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (valid) {
      submitting.value = true
      try {
        if (form.value.id) {
          await updateGlobalToken(form.value.id, form.value)
          ElMessage.success('更新成功')
        } else {
          await createGlobalToken(form.value)
          ElMessage.success('创建成功')
        }
        dialogVisible.value = false
        await loadGlobalTokens()
      } catch (error) {
        console.error('保存失败:', error)
        ElMessage.error(error.response?.data?.detail || '保存失败')
      } finally {
        submitting.value = false
      }
    }
  })
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(`确定要删除 Token "${row.name}" 吗？`, '确认删除', {
      type: 'warning'
    })
    await deleteGlobalToken(row.id)
    ElMessage.success('删除成功')
    await loadGlobalTokens()
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

const getAuthTypeLabel = (type) => {
  const labels = {
    bearer: 'Bearer Token',
    drf_token: 'DRF Token',
    header: '自定义 Header'
  }
  return labels[type] || type
}

const maskToken = (token) => {
  if (!token) return ''
  if (token.length <= 10) return token
  return token.substring(0, 6) + '****' + token.substring(token.length - 4)
}

onMounted(() => {
  loadGlobalTokens()
})
</script>

<style scoped>
.global-tokens-container {
  padding: 24px;
  background-color: #f5f7fa;
  min-height: calc(100vh - 60px);
}

.tokens-header {
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

.token-code {
  background: #f5f7fa;
  padding: 2px 6px;
  border-radius: 3px;
  font-size: 12px;
  color: #606266;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
}
</style>

