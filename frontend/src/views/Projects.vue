<template>
  <div class="projects-container">
    <!-- 顶部导航栏 -->
    <header class="projects-header">
      <div class="header-left">
        <h1 class="title">项目管理</h1>
        <p class="subtitle">创建和管理测试项目，组织测试资源</p>
      </div>

      <div class="header-right">
        <el-input
          v-model="searchQuery"
          placeholder="搜索项目名称"
          style="width: 200px"
          clearable
          @clear="handleSearch"
          @keyup.enter="handleSearch"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <el-button @click="handleSearch" style="margin-left: 8px">
          查询
        </el-button>
        <el-button type="primary" @click="handleCreate">
          <el-icon><Plus /></el-icon>
          新建项目
        </el-button>
      </div>
    </header>

    <!-- 统计信息卡片 -->
    <section class="stats-grid">
      <transition-group name="fade-up" tag="div" class="stats-cards">
        <el-card :key="'total'" class="stat-card" shadow="hover">
          <div class="stat-label">项目总数</div>
          <div class="stat-value">{{ stats.total }}</div>
        </el-card>

        <el-card :key="'active'" class="stat-card" shadow="hover">
          <div class="stat-label">活跃项目</div>
          <div class="stat-value text-success">{{ stats.active }}</div>
        </el-card>

        <el-card :key="'apis'" class="stat-card" shadow="hover">
          <div class="stat-label">接口总数</div>
          <div class="stat-value text-primary">{{ stats.totalApis }}</div>
        </el-card>

        <el-card :key="'cases'" class="stat-card" shadow="hover">
          <div class="stat-label">测试用例</div>
          <div class="stat-value text-info">{{ stats.totalCases }}</div>
        </el-card>

        <el-card :key="'suites'" class="stat-card" shadow="hover">
          <div class="stat-label">测试套件</div>
          <div class="stat-value text-warning">{{ stats.totalSuites }}</div>
        </el-card>
      </transition-group>
    </section>

    <!-- 项目列表 -->
    <el-card class="table-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <span class="card-title">项目列表</span>
          <span class="card-subtitle">共 {{ total }} 个</span>
        </div>
      </template>

      <el-table
        :data="projects"
        stripe
        style="width: 100%"
        v-loading="loading"
        empty-text="暂无项目"
      >
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="项目名称" min-width="200" show-overflow-tooltip />
        <el-table-column prop="description" label="描述" min-width="250" show-overflow-tooltip />
        <el-table-column label="负责人" width="120">
          <template #default="{ row }">
            {{ row.owner?.username || '-' }}
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
              {{ row.is_active ? '激活' : '停用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            <span class="text-gray">{{ formatDate(row.created_at) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" link @click="handleEdit(row)">
              编辑
            </el-button>
            <el-button type="success" size="small" link @click="handleView(row)">
              查看
            </el-button>
            <el-button type="danger" size="small" link @click="handleDelete(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-container" v-if="total > 0">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>

    <!-- 创建/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="600px"
      @close="handleDialogClose"
    >
      <el-form ref="formRef" :model="form" :rules="formRules" label-width="100px">
        <el-form-item label="项目名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入项目名称" />
        </el-form-item>
        <el-form-item label="项目描述" prop="description">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="4"
            placeholder="请输入项目描述"
          />
        </el-form-item>
        <el-form-item label="状态">
          <el-switch
            v-model="form.is_active"
            active-text="激活"
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
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Plus } from '@element-plus/icons-vue'
import { getProjects, createProject, updateProject, deleteProject, getProjectStatistics } from '../api/projects'

const loading = ref(false)
const searchQuery = ref('')
const projects = ref([])
const total = ref(0)
const submitting = ref(false)
const dialogVisible = ref(false)
const dialogTitle = ref('新建项目')
const formRef = ref(null)

const pagination = ref({
  page: 1,
  pageSize: 20
})

const stats = ref({
  total: 0,
  active: 0,
  totalApis: 0,
  totalCases: 0,
  totalSuites: 0
})

const form = ref({
  id: null,
  name: '',
  description: '',
  is_active: true
})

const formRules = {
  name: [{ required: true, message: '请输入项目名称', trigger: 'blur' }]
}

const filteredProjects = computed(() => {
  // 由于后端已经支持按名称搜索，这里直接返回projects
  // 搜索功能通过后端API实现
  return projects.value
})

const loadProjects = async () => {
  loading.value = true
  try {
    // 构建查询参数
    const params = {
      page: pagination.value.page,
      page_size: pagination.value.pageSize
    }
    // 如果搜索框有内容，添加到查询参数
    if (searchQuery.value) {
      params.name = searchQuery.value
    }
    
    const response = await getProjects(params)
    
    if (response.results) {
      projects.value = response.results
      total.value = response.count || response.results.length
    } else if (Array.isArray(response)) {
      projects.value = response
      total.value = response.length
    }

    // 加载统计数据（根据当前查询条件）
    await loadStatistics()
  } catch (error) {
    console.error('加载项目列表失败:', error)
    ElMessage.error('加载项目列表失败')
  } finally {
    loading.value = false
  }
}

const loadStatistics = async () => {
  try {
    // 构建统计查询参数（包含搜索条件）
    const params = {}
    if (searchQuery.value) {
      params.name = searchQuery.value
    }
    
    const response = await getProjectStatistics(params)
    stats.value = {
      total: response.total || 0,
      active: response.active || 0,
      totalApis: response.total_apis || 0,
      totalCases: response.total_cases || 0,
      totalSuites: response.total_suites || 0
    }
  } catch (error) {
    console.error('加载统计数据失败:', error)
    // 如果统计API失败，使用本地计算
    calculateStats()
  }
}

const calculateStats = () => {
  const total = projects.value.length
  const active = projects.value.filter((p) => p.is_active).length
  
  stats.value = {
    total,
    active,
    totalApis: 0,
    totalCases: 0,
    totalSuites: 0
  }
}

const handleCreate = () => {
  dialogTitle.value = '新建项目'
  form.value = {
    id: null,
    name: '',
    description: '',
    is_active: true
  }
  dialogVisible.value = true
}

const handleEdit = (row) => {
  dialogTitle.value = '编辑项目'
  form.value = {
    id: row.id,
    name: row.name,
    description: row.description || '',
    is_active: row.is_active
  }
  dialogVisible.value = true
}

const handleView = (row) => {
  ElMessage.info(`查看项目: ${row.name}`)
  // TODO: 跳转到项目详情页
}

const handleSubmit = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (valid) {
      submitting.value = true
      try {
        if (form.value.id) {
          await updateProject(form.value.id, form.value)
          ElMessage.success('更新成功')
        } else {
          await createProject(form.value)
          ElMessage.success('创建成功')
        }
        dialogVisible.value = false
        await loadProjects()
      } catch (error) {
        console.error('提交失败:', error)
        ElMessage.error(error.response?.data?.detail || '操作失败')
      } finally {
        submitting.value = false
      }
    }
  })
}

const handleDialogClose = () => {
  formRef.value?.resetFields()
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(`确定要删除项目 "${row.name}" 吗？`, '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    await deleteProject(row.id)
    ElMessage.success('删除成功')
    await loadProjects()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
      ElMessage.error(error.response?.data?.detail || '删除失败')
    }
  }
}

const handleSizeChange = (size) => {
  pagination.value.pageSize = size
  pagination.value.page = 1
  loadProjects()
}

const handlePageChange = (page) => {
  pagination.value.page = page
  loadProjects()
}

const handleSearch = () => {
  // 搜索时重置到第一页
  pagination.value.page = 1
  loadProjects()
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
  // 初始化时也加载统计数据
  loadStatistics()
})
</script>

<style scoped>
.projects-container {
  padding: 24px;
  background-color: #f5f7fa;
  min-height: calc(100vh - 60px);
}

.projects-header {
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

.stats-grid {
  margin-bottom: 24px;
}

.stats-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 16px;
}

.stat-card {
  transition: transform 0.2s;
}

.stat-card:hover {
  transform: translateY(-2px);
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-bottom: 8px;
}

.stat-value {
  font-size: 32px;
  font-weight: bold;
  color: #303133;
}

.stat-value.text-success {
  color: #10b981;
}

.stat-value.text-primary {
  color: #409eff;
}

.stat-value.text-info {
  color: #909399;
}

.stat-value.text-warning {
  color: #e6a23c;
}

.table-card {
  margin-bottom: 24px;
}

/* 统一表格单元格不换行 */
:deep(.el-table .el-table__cell) {
  white-space: nowrap !important;
  overflow: hidden;
}

:deep(.el-table td),
:deep(.el-table th) {
  white-space: nowrap !important;
  overflow: hidden;
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

.text-gray {
  color: #909399;
  font-size: 12px;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.fade-up-enter-active,
.fade-up-leave-active {
  transition: all 0.3s ease;
}

.fade-up-enter-from {
  opacity: 0;
  transform: translateY(10px);
}

.fade-up-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}
</style>
