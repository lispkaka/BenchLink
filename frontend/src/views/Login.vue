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
          <label class="form-label">用户名</label>
          <el-input
            v-model="form.username"
            placeholder="请输入用户名"
            class="custom-input"
            clearable
          />
        </el-form-item>

        <!-- Password -->
        <el-form-item prop="password">
          <label class="form-label">密码</label>
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
  background: linear-gradient(to bottom, #f8fafc, #e2e8f0);
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

.login-card {
  background: white;
  border-radius: 16px;
  width: 100%;
  max-width: 420px;
  padding: 40px;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
}

.logo-section {
  text-align: center;
  margin-bottom: 40px;
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
  font-size: 28px;
  font-weight: 700;
  color: #1e293b;
  margin: 0 0 8px 0;
}

.platform-subtitle {
  font-size: 14px;
  color: #64748b;
  margin: 0;
}

.login-form {
  margin-top: 0;
}

.form-label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: #374151;
  margin-bottom: 8px;
}

:deep(.el-form-item) {
  margin-bottom: 24px;
}

:deep(.el-form-item__label) {
  padding: 0;
  margin-bottom: 8px;
  line-height: 1.5;
}

.custom-input :deep(.el-input__wrapper) {
  background-color: #f9fafb;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  padding: 12px 16px;
  box-shadow: none;
  transition: all 0.2s;
}

.custom-input :deep(.el-input__wrapper:hover) {
  border-color: #94a3b8;
}

.custom-input :deep(.el-input__wrapper.is-focus) {
  border-color: #94a3b8;
  box-shadow: 0 0 0 4px rgba(148, 163, 184, 0.2);
}

.custom-input :deep(.el-input__inner) {
  color: #1e293b;
  font-size: 14px;
}

.custom-input :deep(.el-input__inner::placeholder) {
  color: #9ca3af;
}


.login-button {
  width: 100%;
  height: 44px;
  background-color: #475569;
  border-color: #475569;
  font-size: 15px;
  font-weight: 500;
  border-radius: 8px;
  transition: all 0.2s;
}

.login-button:hover {
  background-color: #334155;
  border-color: #334155;
  transform: scale(1.02);
}

.login-button:active {
  transform: scale(0.98);
}

.footer {
  margin-top: 40px;
  text-align: center;
  font-size: 12px;
  color: #9ca3af;
}
</style>



