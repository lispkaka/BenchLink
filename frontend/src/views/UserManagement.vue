<template>
  <div class="user-management-container">
    <!-- 顶部操作栏 -->
    <header class="page-header">
      <div class="header-left">
        <h1 class="title">用户管理</h1>
        <p class="subtitle">管理系统用户账号和权限</p>
      </div>
      <div class="header-right">
        <el-input
          v-model="searchQuery"
          placeholder="搜索用户名或邮箱"
          style="width: 250px; margin-right: 12px"
          clearable
          @input="handleSearch"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <el-button type="primary" @click="handleCreate">
          <el-icon><Plus /></el-icon>
          新建用户
        </el-button>
      </div>
    </header>

    <!-- 用户列表 -->
    <el-card class="table-card" shadow="hover">
      <el-table
        :data="filteredUsers"
        stripe
        style="width: 100%"
        v-loading="loading"
        empty-text="暂无用户"
      >
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="username" label="用户名" min-width="120" />
        <el-table-column prop="email" label="邮箱" min-width="180" />
        <el-table-column prop="phone" label="手机号" width="130">
          <template #default="{ row }">
            {{ row.phone || '-' }}
          </template>
        </el-table-column>
        <el-table-column label="角色" width="100">
          <template #default="{ row }">
            <el-tag v-if="row.is_superuser" type="danger" size="small">超级管理员</el-tag>
            <el-tag v-else-if="row.is_staff" type="warning" size="small">管理员</el-tag>
            <el-tag v-else type="info" size="small">普通用户</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
              {{ row.is_active ? '正常' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="last_login" label="最后登录" width="180">
          <template #default="{ row }">
            {{ row.last_login ? formatDate(row.last_login) : '从未登录' }}
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" link @click="handleEdit(row)">
              编辑
            </el-button>
            <el-button type="warning" size="small" link @click="handleResetPassword(row)">
              重置密码
            </el-button>
            <el-button 
              type="danger" 
              size="small" 
              link 
              @click="handleDelete(row)"
              :disabled="row.id === currentUser?.id"
            >
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
      <el-form ref="formRef" :model="form" :rules="formRules" label-width="100px">
        <el-form-item label="用户名" prop="username">
          <el-input 
            v-model="form.username" 
            placeholder="请输入用户名" 
            :disabled="!!form.id"
          />
          <div class="form-tip" v-if="form.id">用户名创建后不可修改</div>
        </el-form-item>
        
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="form.email" placeholder="请输入邮箱" />
        </el-form-item>
        
        <el-form-item label="手机号" prop="phone">
          <el-input v-model="form.phone" placeholder="请输入手机号（可选）" />
        </el-form-item>
        
        <el-form-item label="密码" prop="password" v-if="!form.id">
          <el-input 
            v-model="form.password" 
            type="password" 
            placeholder="请输入密码（至少6位）"
            show-password
          />
        </el-form-item>
        
        <el-form-item label="角色" prop="role">
          <el-radio-group v-model="form.role">
            <el-radio value="user">普通用户</el-radio>
            <el-radio value="staff">管理员</el-radio>
            <el-radio value="superuser">超级管理员</el-radio>
          </el-radio-group>
        </el-form-item>
        
        <el-form-item label="状态">
          <el-switch
            v-model="form.is_active"
            active-text="正常"
            inactive-text="禁用"
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

    <!-- 重置密码对话框 -->
    <el-dialog
      v-model="resetPasswordVisible"
      title="重置密码"
      width="400px"
    >
      <el-form ref="resetFormRef" :model="resetForm" :rules="resetFormRules" label-width="100px">
        <el-form-item label="新密码" prop="password">
          <el-input 
            v-model="resetForm.password" 
            type="password" 
            placeholder="请输入新密码（至少6位）"
            show-password
          />
        </el-form-item>
        <el-form-item label="确认密码" prop="confirmPassword">
          <el-input 
            v-model="resetForm.confirmPassword" 
            type="password" 
            placeholder="请再次输入新密码"
            show-password
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="resetPasswordVisible = false">取消</el-button>
        <el-button type="primary" @click="handleResetPasswordSubmit" :loading="submitting">
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search } from '@element-plus/icons-vue'
import api from '../api/index'
import { useUserStore } from '../store'

const userStore = useUserStore()
const currentUser = computed(() => userStore.user)

const loading = ref(false)
const users = ref([])
const searchQuery = ref('')
const submitting = ref(false)
const dialogVisible = ref(false)
const resetPasswordVisible = ref(false)
const dialogTitle = ref('新建用户')
const formRef = ref(null)
const resetFormRef = ref(null)

const form = ref({
  id: null,
  username: '',
  email: '',
  phone: '',
  password: '',
  role: 'user',
  is_active: true
})

const resetForm = ref({
  userId: null,
  password: '',
  confirmPassword: ''
})

const formRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 30, message: '用户名长度3-30个字符', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入有效的邮箱地址', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度至少6位', trigger: 'blur' }
  ]
}

const resetFormRules = {
  password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码长度至少6位', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请再次输入新密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== resetForm.value.password) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
}

const filteredUsers = computed(() => {
  if (!searchQuery.value) return users.value
  const query = searchQuery.value.toLowerCase()
  return users.value.filter(user => 
    user.username?.toLowerCase().includes(query) ||
    user.email?.toLowerCase().includes(query)
  )
})

const loadUsers = async () => {
  loading.value = true
  try {
    const response = await api.get('/users/users/')
    users.value = Array.isArray(response) ? response : response.results || []
  } catch (error) {
    console.error('加载用户列表失败:', error)
    ElMessage.error('加载用户列表失败')
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  // 搜索逻辑已通过 computed 自动处理
}

const handleCreate = () => {
  dialogTitle.value = '新建用户'
  form.value = {
    id: null,
    username: '',
    email: '',
    phone: '',
    password: '',
    role: 'user',
    is_active: true
  }
  dialogVisible.value = true
}

const handleEdit = (row) => {
  dialogTitle.value = '编辑用户'
  form.value = {
    id: row.id,
    username: row.username,
    email: row.email,
    phone: row.phone || '',
    password: '',
    role: row.is_superuser ? 'superuser' : (row.is_staff ? 'staff' : 'user'),
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
        username: form.value.username,
        email: form.value.email,
        phone: form.value.phone || '',
        is_active: form.value.is_active,
        is_staff: form.value.role === 'staff' || form.value.role === 'superuser',
        is_superuser: form.value.role === 'superuser'
      }
      
      if (!form.value.id) {
        // 创建用户
        submitData.password = form.value.password
        await api.post('/users/users/', submitData)
        ElMessage.success('创建成功')
      } else {
        // 更新用户
        await api.patch(`/users/users/${form.value.id}/`, submitData)
        ElMessage.success('更新成功')
      }
      
      dialogVisible.value = false
      await loadUsers()
    } catch (error) {
      console.error('提交失败:', error)
      const errorMsg = error.response?.data?.username?.[0] || 
                       error.response?.data?.email?.[0] ||
                       error.response?.data?.detail || 
                       '操作失败'
      ElMessage.error(errorMsg)
    } finally {
      submitting.value = false
    }
  })
}

const handleResetPassword = (row) => {
  resetForm.value = {
    userId: row.id,
    password: '',
    confirmPassword: ''
  }
  resetPasswordVisible.value = true
}

const handleResetPasswordSubmit = async () => {
  if (!resetFormRef.value) return
  
  await resetFormRef.value.validate(async (valid) => {
    if (!valid) return
    
    submitting.value = true
    try {
      await api.patch(`/users/users/${resetForm.value.userId}/`, {
        password: resetForm.value.password
      })
      ElMessage.success('密码重置成功')
      resetPasswordVisible.value = false
    } catch (error) {
      console.error('重置密码失败:', error)
      ElMessage.error(error.response?.data?.detail || '重置密码失败')
    } finally {
      submitting.value = false
    }
  })
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除用户 "${row.username}" 吗？删除后将无法恢复。`,
      '确认删除',
      {
        type: 'warning',
        confirmButtonText: '确定删除',
        cancelButtonText: '取消'
      }
    )
    
    await api.delete(`/users/users/${row.id}/`)
    ElMessage.success('删除成功')
    await loadUsers()
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
  return date.toLocaleString('zh-CN')
}

onMounted(() => {
  loadUsers()
})
</script>

<style scoped>
.user-management-container {
  padding: 24px;
  background-color: #f5f7fa;
  min-height: calc(100vh - 60px);
}

.page-header {
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

.header-right {
  display: flex;
  align-items: center;
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

.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}
</style>




