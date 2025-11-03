<template>
  <div class="settings-container">
    <!-- 顶部导航栏 -->
    <header class="settings-header">
      <div class="header-left">
        <h1 class="title">系统设置</h1>
        <p class="subtitle">管理个人账户和系统配置</p>
      </div>
    </header>

    <!-- 设置内容 -->
    <div class="settings-content">
      <!-- 用户信息卡片 -->
      <el-card class="settings-card" shadow="hover">
        <template #header>
          <div class="card-header">
            <span class="card-title">
              <el-icon><User /></el-icon>
              用户信息
            </span>
          </div>
        </template>
        <el-form ref="userFormRef" :model="userForm" :rules="userFormRules" label-width="120px">
          <el-form-item label="用户名" prop="username">
            <el-input v-model="userForm.username" disabled />
          </el-form-item>
          <el-form-item label="邮箱" prop="email">
            <el-input v-model="userForm.email" placeholder="请输入邮箱" />
          </el-form-item>
          <el-form-item label="手机号" prop="phone">
            <el-input v-model="userForm.phone" placeholder="请输入手机号" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="handleSaveUser" :loading="saving">
              保存修改
            </el-button>
            <el-button @click="handleResetUser">重置</el-button>
          </el-form-item>
        </el-form>
      </el-card>

      <!-- 修改密码卡片 -->
      <el-card class="settings-card" shadow="hover">
        <template #header>
          <div class="card-header">
            <span class="card-title">
              <el-icon><Lock /></el-icon>
              修改密码
            </span>
          </div>
        </template>
        <el-form ref="passwordFormRef" :model="passwordForm" :rules="passwordFormRules" label-width="120px">
          <el-form-item label="当前密码" prop="oldPassword">
            <el-input
              v-model="passwordForm.oldPassword"
              type="password"
              placeholder="请输入当前密码"
              show-password
            />
          </el-form-item>
          <el-form-item label="新密码" prop="newPassword">
            <el-input
              v-model="passwordForm.newPassword"
              type="password"
              placeholder="请输入新密码"
              show-password
            />
          </el-form-item>
          <el-form-item label="确认新密码" prop="confirmPassword">
            <el-input
              v-model="passwordForm.confirmPassword"
              type="password"
              placeholder="请再次输入新密码"
              show-password
            />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="handleChangePassword" :loading="changingPassword">
              修改密码
            </el-button>
            <el-button @click="handleResetPassword">重置</el-button>
          </el-form-item>
        </el-form>
      </el-card>

      <!-- 系统配置卡片 -->
      <el-card class="settings-card" shadow="hover">
        <template #header>
          <div class="card-header">
            <span class="card-title">
              <el-icon><Setting /></el-icon>
              系统配置
            </span>
          </div>
        </template>
        <el-form :model="systemForm" label-width="120px">
          <el-form-item label="主题模式">
            <el-radio-group v-model="systemForm.theme">
              <el-radio label="light">浅色</el-radio>
              <el-radio label="dark">深色</el-radio>
              <el-radio label="auto">跟随系统</el-radio>
            </el-radio-group>
          </el-form-item>
          <el-form-item label="语言设置">
            <el-select v-model="systemForm.language" style="width: 200px">
              <el-option label="简体中文" value="zh-CN" />
              <el-option label="English" value="en-US" />
            </el-select>
          </el-form-item>
          <el-form-item label="自动保存">
            <el-switch v-model="systemForm.autoSave" />
            <span style="margin-left: 10px; color: #909399; font-size: 12px">
              编辑内容时自动保存
            </span>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="handleSaveSystem">
              保存配置
            </el-button>
          </el-form-item>
        </el-form>
      </el-card>

      <!-- 关于卡片 -->
      <el-card class="settings-card" shadow="hover">
        <template #header>
          <div class="card-header">
            <span class="card-title">
              <el-icon><InfoFilled /></el-icon>
              关于
            </span>
          </div>
        </template>
        <div class="about-content">
          <div class="about-item">
            <span class="about-label">应用名称：</span>
            <span class="about-value">BenchLink 接口测试平台</span>
          </div>
          <div class="about-item">
            <span class="about-label">版本号：</span>
            <span class="about-value">v1.0.0</span>
          </div>
          <div class="about-item">
            <span class="about-label">开发团队：</span>
            <span class="about-value">BenchLink Team</span>
          </div>
          <div class="about-item">
            <span class="about-label">许可证：</span>
            <span class="about-value">MIT License</span>
          </div>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { User, Lock, Setting, InfoFilled } from '@element-plus/icons-vue'
import { getCurrentUser } from '../api/users'
import api from '../api/index'

const saving = ref(false)
const changingPassword = ref(false)
const userFormRef = ref(null)
const passwordFormRef = ref(null)

const userForm = ref({
  username: '',
  email: '',
  phone: ''
})

const originalUserForm = ref({
  username: '',
  email: '',
  phone: ''
})

const userFormRules = {
  email: [
    { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' }
  ],
  phone: [
    { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号', trigger: 'blur' }
  ]
}

const passwordForm = ref({
  oldPassword: '',
  newPassword: '',
  confirmPassword: ''
})

const validateConfirmPassword = (rule, value, callback) => {
  if (value !== passwordForm.value.newPassword) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const passwordFormRules = {
  oldPassword: [
    { required: true, message: '请输入当前密码', trigger: 'blur' }
  ],
  newPassword: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码长度至少6位', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' }
  ]
}

const systemForm = ref({
  theme: 'light',
  language: 'zh-CN',
  autoSave: true
})

const loadUserInfo = async () => {
  try {
    const user = await getCurrentUser()
    userForm.value = {
      username: user.username || '',
      email: user.email || '',
      phone: user.phone || ''
    }
    originalUserForm.value = { ...userForm.value }
  } catch (error) {
    console.error('获取用户信息失败', error)
    ElMessage.error('获取用户信息失败')
  }
}

const handleSaveUser = async () => {
  if (!userFormRef.value) return

  await userFormRef.value.validate(async (valid) => {
    if (valid) {
      saving.value = true
      try {
        // TODO: 调用更新用户信息的API
        await api.patch('/users/users/me/', userForm.value)
        originalUserForm.value = { ...userForm.value }
        ElMessage.success('保存成功')
      } catch (error) {
        console.error('保存用户信息失败', error)
        ElMessage.error(error.response?.data?.detail || '保存失败')
      } finally {
        saving.value = false
      }
    }
  })
}

const handleResetUser = () => {
  userForm.value = { ...originalUserForm.value }
  userFormRef.value?.resetFields()
}

const handleChangePassword = async () => {
  if (!passwordFormRef.value) return

  await passwordFormRef.value.validate(async (valid) => {
    if (valid) {
      changingPassword.value = true
      try {
        // TODO: 调用修改密码的API
        await api.post('/users/users/change-password/', {
          old_password: passwordForm.value.oldPassword,
          new_password: passwordForm.value.newPassword
        })
        ElMessage.success('密码修改成功')
        handleResetPassword()
      } catch (error) {
        console.error('修改密码失败', error)
        ElMessage.error(error.response?.data?.detail || '修改密码失败')
      } finally {
        changingPassword.value = false
      }
    }
  })
}

const handleResetPassword = () => {
  passwordForm.value = {
    oldPassword: '',
    newPassword: '',
    confirmPassword: ''
  }
  passwordFormRef.value?.resetFields()
}

const handleSaveSystem = () => {
  // 保存系统配置到localStorage
  localStorage.setItem('systemConfig', JSON.stringify(systemForm.value))
  ElMessage.success('配置已保存')
}

onMounted(() => {
  loadUserInfo()
  
  // 从localStorage加载系统配置
  const savedConfig = localStorage.getItem('systemConfig')
  if (savedConfig) {
    try {
      systemForm.value = { ...systemForm.value, ...JSON.parse(savedConfig) }
    } catch (error) {
      console.error('加载系统配置失败', error)
    }
  }
})
</script>

<style scoped>
.settings-container {
  padding: 24px;
  background-color: #f5f7fa;
  min-height: calc(100vh - 60px);
}

.settings-header {
  margin-bottom: 24px;
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

.settings-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.settings-card {
  transition: transform 0.2s;
}

.settings-card:hover {
  transform: translateY(-2px);
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
  display: flex;
  align-items: center;
  gap: 8px;
}

.about-content {
  padding: 8px 0;
}

.about-item {
  display: flex;
  padding: 12px 0;
  border-bottom: 1px solid #f0f0f0;
}

.about-item:last-child {
  border-bottom: none;
}

.about-label {
  font-weight: 500;
  color: #606266;
  min-width: 100px;
}

.about-value {
  color: #909399;
}
</style>
