<template>
  <div class="settings-container">
    <!-- 顶部导航栏 -->
    <header class="settings-header">
      <div class="header-left">
        <h1 class="title">通知配置</h1>
        <p class="subtitle">配置测试执行完成后的通知告警渠道</p>
      </div>
      <div class="header-right">
        <el-button type="primary" @click="handleCreate">
          <el-icon><Plus /></el-icon>
          新建通知渠道
        </el-button>
      </div>
    </header>

    <!-- 通知渠道列表 -->
    <el-card class="table-card" shadow="hover">
        <template #header>
          <div class="card-header">
          <span class="card-title">通知渠道配置</span>
          <span class="card-subtitle">共 {{ channels.length }} 个</span>
          </div>
        </template>

      <el-table
        :data="channels"
        stripe
        style="width: 100%"
        v-loading="loading"
        empty-text="暂无通知渠道"
      >
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="渠道名称" min-width="150" />
        <el-table-column label="渠道类型" width="120">
          <template #default="{ row }">
            <el-tag :type="getChannelTagType(row.channel_type)">
              {{ row.channel_type_display }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="通知规则" width="200">
          <template #default="{ row }">
            <el-tag v-if="row.notify_on_success" type="success" size="small" style="margin-right: 4px">成功</el-tag>
            <el-tag v-if="row.notify_on_failure" type="danger" size="small" style="margin-right: 4px">失败</el-tag>
            <el-tag v-if="row.notify_on_complete" type="info" size="small">完成</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
              {{ row.is_active ? '启用' : '停用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" link @click="handleTest(row)">
              测试
            </el-button>
            <el-button type="primary" size="small" link @click="handleEdit(row)">
              编辑
            </el-button>
            <el-button type="danger" size="small" link @click="handleDelete(row)">
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
      width="600px"
      @close="handleDialogClose"
    >
      <el-form ref="formRef" :model="form" :rules="formRules" label-width="120px">
        <el-form-item label="渠道名称" prop="name">
          <el-input v-model="form.name" placeholder="例如：测试通知" />
        </el-form-item>
        
        <el-form-item label="渠道类型" prop="channel_type">
          <el-select v-model="form.channel_type" placeholder="请选择渠道类型" style="width: 100%">
            <el-option label="企业微信" value="wecom">
              <span>企业微信</span>
            </el-option>
            <el-option label="钉钉" value="dingtalk">
              <span>钉钉</span>
            </el-option>
            <el-option label="飞书" value="feishu" disabled>
              <span>飞书（开发中）</span>
            </el-option>
            <el-option label="Telegram" value="telegram" disabled>
              <span>Telegram（开发中）</span>
            </el-option>
          </el-select>
        </el-form-item>
        
        <el-form-item label="Webhook URL" prop="webhook_url">
          <el-input
            v-model="form.webhook_url"
            type="textarea"
            :rows="3"
            placeholder="请输入机器人的Webhook URL"
          />
          <div class="form-tip">
            <el-link type="primary" href="https://developer.work.weixin.qq.com/document/path/91770" target="_blank" v-if="form.channel_type === 'wecom'">
              如何获取企业微信Webhook？
            </el-link>
            <el-link type="primary" href="https://open.dingtalk.com/document/robots/custom-robot-access" target="_blank" v-if="form.channel_type === 'dingtalk'">
              如何获取钉钉Webhook？
            </el-link>
          </div>
          </el-form-item>
        
        <el-form-item label="加签密钥" v-if="form.channel_type === 'dingtalk'">
          <el-input
            v-model="form.secret"
            placeholder="钉钉机器人的加签密钥（可选）"
          />
          <div class="form-tip">如果钉钉机器人启用了加签，请填写密钥</div>
          </el-form-item>
        
        <el-form-item label="通知规则">
          <el-checkbox v-model="form.notify_on_success">成功时通知</el-checkbox>
          <el-checkbox v-model="form.notify_on_failure">失败时通知</el-checkbox>
          <el-checkbox v-model="form.notify_on_complete">完成时通知</el-checkbox>
          </el-form-item>
        
        <el-form-item label="状态">
          <el-switch
            v-model="form.is_active"
            active-text="启用"
            inactive-text="停用"
          />
          </el-form-item>
        </el-form>
      
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">
          确定
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
  getNotificationChannels,
  createNotificationChannel,
  updateNotificationChannel,
  deleteNotificationChannel,
  testNotificationChannel
} from '../api/notifications'

const loading = ref(false)
const channels = ref([])
const submitting = ref(false)
const dialogVisible = ref(false)
const dialogTitle = ref('新建通知渠道')
const formRef = ref(null)

const form = ref({
  id: null,
  name: '',
  channel_type: 'wecom',
  webhook_url: '',
  secret: '',
  notify_on_success: false,
  notify_on_failure: true,
  notify_on_complete: false,
  is_active: true
})

const formRules = {
  name: [{ required: true, message: '请输入渠道名称', trigger: 'blur' }],
  channel_type: [{ required: true, message: '请选择渠道类型', trigger: 'change' }],
  webhook_url: [
    { required: true, message: '请输入Webhook URL', trigger: 'blur' },
    { type: 'url', message: '请输入有效的URL', trigger: 'blur' }
  ]
}

const loadChannels = async () => {
  loading.value = true
  try {
    const response = await getNotificationChannels()
    channels.value = Array.isArray(response) ? response : response.results || []
  } catch (error) {
    console.error('加载通知渠道失败:', error)
    ElMessage.error('加载通知渠道失败')
  } finally {
    loading.value = false
  }
}

const handleCreate = () => {
  dialogTitle.value = '新建通知渠道'
  form.value = {
    id: null,
    name: '',
    channel_type: 'wecom',
    webhook_url: '',
    secret: '',
    notify_on_success: false,
    notify_on_failure: true,
    notify_on_complete: false,
    is_active: true
  }
  dialogVisible.value = true
}

const handleEdit = (row) => {
  dialogTitle.value = '编辑通知渠道'
  form.value = {
    id: row.id,
    name: row.name,
    channel_type: row.channel_type,
    webhook_url: row.webhook_url,
    secret: row.secret || '',
    notify_on_success: row.notify_on_success,
    notify_on_failure: row.notify_on_failure,
    notify_on_complete: row.notify_on_complete,
    is_active: row.is_active
  }
  dialogVisible.value = true
}

const handleSubmit = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    
    submitting.value = true
    try {
      const submitData = {
        name: form.value.name,
        channel_type: form.value.channel_type,
        webhook_url: form.value.webhook_url,
        secret: form.value.secret || '',
        notify_on_success: form.value.notify_on_success,
        notify_on_failure: form.value.notify_on_failure,
        notify_on_complete: form.value.notify_on_complete,
        is_active: form.value.is_active
      }
      
      if (form.value.id) {
        await updateNotificationChannel(form.value.id, submitData)
        ElMessage.success('更新成功')
      } else {
        await createNotificationChannel(submitData)
        ElMessage.success('创建成功')
      }
      
      dialogVisible.value = false
      await loadChannels()
    } catch (error) {
      console.error('提交失败:', error)
      ElMessage.error(error.response?.data?.detail || '操作失败')
    } finally {
      submitting.value = false
    }
  })
}

const handleTest = async (row) => {
  try {
    await ElMessageBox.confirm(
      '将发送一条测试消息到该通知渠道，确定继续吗？',
      '测试通知',
      {
        type: 'info'
      }
    )
    
    loading.value = true
    await testNotificationChannel(row.id)
    ElMessage.success('测试消息已发送，请检查通知渠道')
      } catch (error) {
    if (error !== 'cancel') {
      console.error('测试失败:', error)
      ElMessage.error(error.response?.data?.error || error.response?.data?.detail || '测试失败')
    }
      } finally {
    loading.value = false
  }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除通知渠道 "${row.name}" 吗？`,
      '确认删除',
      {
        type: 'warning'
      }
    )
    
    await deleteNotificationChannel(row.id)
    ElMessage.success('删除成功')
    await loadChannels()
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

const getChannelTagType = (type) => {
  const types = {
    wecom: 'success',
    dingtalk: 'primary',
    feishu: 'warning',
    telegram: 'info'
  }
  return types[type] || 'info'
}

const formatDate = (dateString) => {
  if (!dateString) return '-'
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN')
}

onMounted(() => {
  loadChannels()
})
</script>

<style scoped>
.settings-container {
  padding: 24px;
  background-color: #f5f7fa;
  min-height: calc(100vh - 60px);
}

.settings-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  background: white;
  padding: 20px 24px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
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

.table-card {
  margin-bottom: 24px;
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

.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}
</style>
