<template>
  <div class="scheduler-container">
    <!-- 顶部导航栏 -->
    <header class="scheduler-header">
      <div class="header-left">
        <h1 class="title">定时任务</h1>
        <p class="subtitle">管理自动化测试定时执行任务</p>
      </div>

      <div class="header-right">
        <el-select v-model="statusFilter" style="width: 120px" placeholder="状态筛选" clearable>
          <el-option label="全部" value="" />
          <el-option label="激活" value="active" />
          <el-option label="停用" value="inactive" />
        </el-select>
        <el-input
          v-model="searchQuery"
          placeholder="搜索任务名称"
          style="width: 200px"
          clearable
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <el-button type="primary" @click="handleCreate">
          <el-icon><Plus /></el-icon>
          新建任务
        </el-button>
      </div>
    </header>

    <!-- 统计信息卡片 -->
    <section class="stats-grid">
      <transition-group name="fade-up" tag="div" class="stats-cards">
        <el-card :key="'total'" class="stat-card" shadow="hover">
          <div class="stat-label">任务总数</div>
          <div class="stat-value">{{ stats.total }}</div>
        </el-card>

        <el-card :key="'active'" class="stat-card" shadow="hover">
          <div class="stat-label">激活任务</div>
          <div class="stat-value text-success">{{ stats.active }}</div>
        </el-card>

        <el-card :key="'inactive'" class="stat-card" shadow="hover">
          <div class="stat-label">停用任务</div>
          <div class="stat-value text-info">{{ stats.inactive }}</div>
        </el-card>

        <el-card :key="'next'" class="stat-card" shadow="hover">
          <div class="stat-label">下次执行</div>
          <div class="stat-value text-primary">{{ stats.nextRun }}</div>
        </el-card>
      </transition-group>
    </section>

    <!-- 定时任务列表 -->
    <el-card class="table-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <span class="card-title">定时任务列表</span>
          <span class="card-subtitle">共 {{ total }} 个</span>
        </div>
      </template>

      <el-table
        :data="schedules"
        stripe
        style="width: 100%"
        v-loading="loading"
        empty-text="暂无定时任务"
      >
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="任务名称" min-width="200" show-overflow-tooltip />
        <el-table-column label="所属项目" width="150">
          <template #default="{ row }">
            {{ row.project?.name || '-' }}
          </template>
        </el-table-column>
        <el-table-column label="测试套件" width="180" show-overflow-tooltip>
          <template #default="{ row }">
            {{ row.testsuite?.name || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="cron_expression" label="Cron表达式" width="150">
          <template #default="{ row }">
            <code class="cron-code">{{ row.cron_expression }}</code>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'active' ? 'success' : 'info'" size="small">
              {{ row.status === 'active' ? '激活' : '停用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="最后执行" width="180">
          <template #default="{ row }">
            <span class="text-gray">{{ formatDate(row.last_run_time) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="下次执行" width="180">
          <template #default="{ row }">
            <span class="text-gray">{{ formatDate(row.next_run_time) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button
              :type="row.status === 'active' ? 'warning' : 'success'"
              size="small"
              link
              @click="handleToggleStatus(row)"
            >
              {{ row.status === 'active' ? '停用' : '激活' }}
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
      width="800px"
      @close="handleDialogClose"
    >
      <el-form ref="formRef" :model="form" :rules="formRules" label-width="100px">
        <el-form-item label="任务名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入任务名称" />
        </el-form-item>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="所属项目" prop="project">
              <el-select v-model="form.project" placeholder="请选择项目" style="width: 100%">
                <el-option
                  v-for="project in projects"
                  :key="project.id"
                  :label="project.name"
                  :value="project.id"
                />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="测试套件" prop="testsuite">
              <el-select v-model="form.testsuite" placeholder="请选择测试套件" style="width: 100%">
                <el-option
                  v-for="testsuite in testSuites"
                  :key="testsuite.id"
                  :label="testsuite.name"
                  :value="testsuite.id"
                />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="Cron表达式" prop="cron_expression">
          <el-input v-model="form.cron_expression" placeholder="例如: 0 0 * * * (每天0点执行)">
            <template #append>
              <el-button @click="showCronHelp = true">帮助</el-button>
            </template>
          </el-input>
        </el-form-item>
        <el-form-item label="任务描述">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="3"
            placeholder="请输入任务描述"
          />
        </el-form-item>
        <el-form-item label="状态">
          <el-switch
            v-model="form.status"
            active-value="active"
            inactive-value="inactive"
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

    <!-- Cron表达式帮助对话框 -->
    <el-dialog v-model="showCronHelp" title="Cron表达式帮助" width="600px">
      <div class="cron-help">
        <p>Cron表达式由5个字段组成，用空格分隔：</p>
        <el-table :data="cronExamples" border>
          <el-table-column prop="expression" label="表达式" width="150" />
          <el-table-column prop="description" label="说明" />
        </el-table>
        <p style="margin-top: 16px; color: #909399; font-size: 12px;">
          <strong>字段说明：</strong>分钟(0-59) 小时(0-23) 日期(1-31) 月份(1-12) 星期(0-7，0和7都表示星期日)
        </p>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Plus } from '@element-plus/icons-vue'
import { getSchedules, createSchedule, updateSchedule, deleteSchedule, toggleSchedule } from '../api/scheduler'
import api from '../api/index'

const loading = ref(false)
const searchQuery = ref('')
const statusFilter = ref('')
const schedules = ref([])
const projects = ref([])
const testSuites = ref([])
const total = ref(0)
const submitting = ref(false)
const dialogVisible = ref(false)
const dialogTitle = ref('新建任务')
const showCronHelp = ref(false)
const formRef = ref(null)

const pagination = ref({
  page: 1,
  pageSize: 20
})

const stats = ref({
  total: 0,
  active: 0,
  inactive: 0,
  nextRun: 0
})

const form = ref({
  id: null,
  name: '',
  project: null,
  testsuite: null,
  cron_expression: '',
  description: '',
  status: 'active'
})

const formRules = {
  name: [{ required: true, message: '请输入任务名称', trigger: 'blur' }],
  project: [{ required: true, message: '请选择所属项目', trigger: 'change' }],
  testsuite: [{ required: true, message: '请选择测试套件', trigger: 'change' }],
  cron_expression: [{ required: true, message: '请输入Cron表达式', trigger: 'blur' }]
}

const cronExamples = [
  { expression: '0 0 * * *', description: '每天0点执行' },
  { expression: '0 */2 * * *', description: '每2小时执行一次' },
  { expression: '0 0 * * 1', description: '每周一0点执行' },
  { expression: '0 0 1 * *', description: '每月1号0点执行' },
  { expression: '*/30 * * * *', description: '每30分钟执行一次' }
]

const filteredSchedules = computed(() => {
  let filtered = schedules.value

  // 状态过滤
  if (statusFilter.value) {
    filtered = filtered.filter((s) => s.status === statusFilter.value)
  }

  // 搜索过滤
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    filtered = filtered.filter((s) =>
      s.name.toLowerCase().includes(query)
    )
  }

  return filtered
})

const loadSchedules = async () => {
  loading.value = true
  try {
    const response = await getSchedules({
      page: pagination.value.page,
      page_size: pagination.value.pageSize
    })
    
    if (response.results) {
      schedules.value = response.results
      total.value = response.count || response.results.length
    } else if (Array.isArray(response)) {
      schedules.value = response
      total.value = response.length
    }

    calculateStats()
  } catch (error) {
    console.error('加载定时任务失败:', error)
    ElMessage.error('加载定时任务失败')
  } finally {
    loading.value = false
  }
}

const loadProjects = async () => {
  try {
    const response = await api.get('/projects/projects/')
    projects.value = Array.isArray(response) ? response : response.results || []
  } catch (error) {
    console.error('加载项目列表失败:', error)
  }
}

const loadTestSuites = async () => {
  try {
    const response = await api.get('/testsuites/testsuites/')
    testSuites.value = Array.isArray(response) ? response : response.results || []
  } catch (error) {
    console.error('加载测试套件列表失败:', error)
  }
}

const calculateStats = () => {
  const total = schedules.value.length
  const active = schedules.value.filter((s) => s.status === 'active').length
  const inactive = total - active
  const nextRun = schedules.value.filter((s) => s.next_run_time && new Date(s.next_run_time) > new Date()).length

  stats.value = { total, active, inactive, nextRun }
}

const handleCreate = () => {
  dialogTitle.value = '新建任务'
  form.value = {
    id: null,
    name: '',
    project: null,
    testsuite: null,
    cron_expression: '',
    description: '',
    status: 'active'
  }
  dialogVisible.value = true
}

const handleEdit = (row) => {
  dialogTitle.value = '编辑任务'
  form.value = {
    id: row.id,
    name: row.name,
    project: row.project?.id || row.project,
    testsuite: row.testsuite?.id || row.testsuite,
    cron_expression: row.cron_expression,
    description: row.description || '',
    status: row.status
  }
  dialogVisible.value = true
}

const handleSubmit = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (valid) {
      submitting.value = true
      try {
        if (form.value.id) {
          await updateSchedule(form.value.id, form.value)
          ElMessage.success('更新成功')
        } else {
          await createSchedule(form.value)
          ElMessage.success('创建成功')
        }
        dialogVisible.value = false
        await loadSchedules()
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

const handleToggleStatus = async (row) => {
  const newStatus = row.status === 'active' ? 'inactive' : 'active'
  try {
    await toggleSchedule(row.id, newStatus)
    ElMessage.success('状态更新成功')
    await loadSchedules()
  } catch (error) {
    console.error('更新状态失败:', error)
    ElMessage.error(error.response?.data?.detail || '更新状态失败')
  }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(`确定要删除任务 "${row.name}" 吗？`, '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    await deleteSchedule(row.id)
    ElMessage.success('删除成功')
    await loadSchedules()
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
  loadSchedules()
}

const handlePageChange = (page) => {
  pagination.value.page = page
  loadSchedules()
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
  loadSchedules()
  loadProjects()
  loadTestSuites()
})
</script>

<style scoped>
.scheduler-container {
  padding: 24px;
  background-color: #f5f7fa;
  min-height: calc(100vh - 60px);
}

.scheduler-header {
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

.cron-code {
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 12px;
  color: #606266;
  background-color: #f5f7fa;
  padding: 2px 6px;
  border-radius: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  display: inline-block;
  max-width: 100%;
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

.cron-help {
  padding: 8px 0;
}

.cron-help p {
  margin: 0 0 12px 0;
  color: #606266;
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
