<template>
  <div class="login-container">
    <div class="login-card">
      <!-- Logo & Title -->
      <div class="logo-section">
        <div class="logo-icon">
          <i class="fas fa-cube"></i>
        </div>
        <h2 class="platform-title">BenchLink 平台</h2>
      
      </div>

      <!-- Login Form -->
      <el-form :model="form" :rules="rules" ref="formRef" @submit.prevent="handleLogin" class="login-form">
        <!-- Username -->
        <el-form-item prop="username">
          <el-input
            v-model="form.username"
            placeholder="请输入用户名"
            class="custom-input"
            clearable
          />
        </el-form-item>

        <!-- Password -->
        <el-form-item prop="password" class="password-item">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="请输入密码"
            class="custom-input"
            show-password
            @keyup.enter="handleLogin"
          />
        </el-form-item>

        <!-- Submit Button -->
        <el-form-item>
          <el-button
            type="primary"
            @click="handleLogin"
            :loading="loading"
            class="login-button"
          >
            立即登录
          </el-button>
        </el-form-item>
      </el-form>

      <!-- Footer -->
      <div class="footer">
        © 2025 BenchLink 平台. All rights reserved.
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../store'
import { login } from '../api/users'
import { ElMessage } from 'element-plus'

const router = useRouter()
const userStore = useUserStore()

const formRef = ref(null)
const loading = ref(false)
const form = ref({
  username: '',
  password: ''
})

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

const handleLogin = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      try {
        const res = await login(form.value)
        userStore.setToken(res.token)
        userStore.setUser(res.user)
        ElMessage.success('登录成功')
        router.push('/dashboard')
      } catch (error) {
        ElMessage.error(error.response?.data?.error || '登录失败')
      } finally {
        loading.value = false
      }
    }
  })
}

</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  padding: 20px;
  background: #f7f7f7;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
}

.login-card {
  background: white;
  border-radius: 16px;
  width: 100%;
  max-width: 420px;
  padding: 48px 40px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
}

.logo-section {
  text-align: center;
  margin-bottom: 48px;
}

.logo-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 80px;
  height: 80px;
  background-color: #f1f5f9;
  border-radius: 50%;
  margin-bottom: 24px;
}

.logo-icon i {
  font-size: 36px;
  color: #64748b;
}

.platform-title {
  font-size: 24px;
  font-weight: 600;
  color: #1e293b;
  margin: 0;
}

.login-form {
  margin-top: 0;
  flex: 1;
}

:deep(.el-form-item) {
  margin-bottom: 6px;
}

:deep(.el-form-item__error) {
  padding-top: 2px;
  color: #f56c6c;
  font-size: 12px;
}

/* 去掉验证失败时的红色边框 */
:deep(.el-form-item.is-error .el-input__wrapper) {
  border-bottom-color: #e0e0e0 !important;
  box-shadow: none !important;
}

:deep(.el-form-item.is-error .el-input__wrapper:hover) {
  border-bottom-color: #999 !important;
}

:deep(.el-form-item.is-error .el-input__wrapper.is-focus) {
  border-bottom-color: #333 !important;
  box-shadow: none !important;
}

.password-item {
  margin-bottom: 8px;
}

.custom-input {
  width: 100%;
}

.custom-input :deep(.el-input__wrapper) {
  background-color: transparent !important;
  border: none !important;
  border-bottom: 1px solid #e0e0e0 !important;
  border-radius: 0 !important;
  padding: 12px 0 !important;
  box-shadow: none !important;
  transition: border-color 0.2s;
}

.custom-input :deep(.el-input__wrapper:hover) {
  border-bottom-color: #999 !important;
  box-shadow: none !important;
}

.custom-input :deep(.el-input__wrapper.is-focus) {
  border-bottom-color: #333 !important;
  box-shadow: none !important;
}

.custom-input :deep(.el-input__wrapper::before),
.custom-input :deep(.el-input__wrapper::after) {
  display: none !important;
}

.custom-input :deep(.el-input__inner) {
  color: #333;
  font-size: 15px;
  padding: 0;
}

.custom-input :deep(.el-input__inner::placeholder) {
  color: #999;
}

.custom-input :deep(.el-input__suffix) {
  right: 0;
}

.login-button {
  width: 100%;
  height: 48px;
  background-color: #000;
  border-color: #000;
  font-size: 16px;
  font-weight: 500;
  border-radius: 8px;
  transition: all 0.2s;
  margin-top: 8px;
}

.login-button:hover {
  background-color: #333;
  border-color: #333;
}

.login-button:active {
  background-color: #1a1a1a;
}

.footer {
  margin-top: 32px;
  text-align: center;
  font-size: 13px;
  color: #666;
  line-height: 1.5;
}
</style>



