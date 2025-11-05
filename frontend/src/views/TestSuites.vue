<template>
  <div class="testsuites-container">
    <!-- 顶部导航栏 -->
    <header class="testsuites-header">
      <div class="header-left">
        <h1 class="title">测试套件管理</h1>
        <p class="subtitle">组织和管理测试用例集合</p>
      </div>

      <div class="header-right">
        <el-input
          v-model="searchQuery"
          placeholder="搜索套件名称"
          style="width: 200px"
          clearable
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <el-button type="primary" @click="handleCreate">
          <el-icon><Plus /></el-icon>
          新建套件
        </el-button>
      </div>
    </header>

    <!-- 统计信息卡片 -->
    <section class="stats-grid">
      <transition-group name="fade-up" tag="div" class="stats-cards">
        <el-card :key="'total'" class="stat-card" shadow="hover">
          <div class="stat-label">套件总数</div>
          <div class="stat-value">{{ stats.total }}</div>
        </el-card>

        <el-card :key="'active'" class="stat-card" shadow="hover">
          <div class="stat-label">活跃套件</div>
          <div class="stat-value text-success">{{ stats.active }}</div>
        </el-card>

        <el-card :key="'cases'" class="stat-card" shadow="hover">
          <div class="stat-label">用例总数</div>
          <div class="stat-value text-primary">{{ stats.totalCases }}</div>
        </el-card>

        <el-card :key="'avg'" class="stat-card" shadow="hover">
          <div class="stat-label">平均用例数</div>
          <div class="stat-value text-info">{{ stats.avgCases }}</div>
        </el-card>
      </transition-group>
    </section>

    <!-- 测试套件列表 -->
    <el-card class="table-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <span class="card-title">测试套件列表</span>
          <span class="card-subtitle">共 {{ total }} 个</span>
        </div>
      </template>

      <el-table
        :data="testSuites"
        stripe
        style="width: 100%"
        v-loading="loading"
        empty-text="暂无测试套件"
      >
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="套件名称" min-width="200" show-overflow-tooltip />
        <el-table-column label="所属项目" width="150">
          <template #default="{ row }">
            {{ row.project?.name || '-' }}
          </template>
        </el-table-column>
        <el-table-column label="用例数量" width="120">
          <template #default="{ row }">
            <el-tag type="info" size="small">
              {{ row.testcases_with_order?.length || row.testcases?.length || 0 }} 个
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="测试环境" width="120">
          <template #default="{ row }">
            {{ row.environment?.name || '-' }}
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
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" link @click="handleEdit(row)">
              编辑
            </el-button>
            <el-button type="success" size="small" link @click="handleExecute(row)" :loading="row.executing">
              执行
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
        <el-form-item label="套件名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入套件名称" />
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
            <el-form-item label="测试环境">
              <el-select v-model="form.environment" placeholder="请选择环境" style="width: 100%" clearable>
                <el-option
                  v-for="env in environments"
                  :key="env.id"
                  :label="env.name"
                  :value="env.id"
                />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="测试用例" prop="testcases_order">
          <div class="testcases-management">
            <!-- 已选测试用例表格 -->
            <el-table
              :data="form.testcases_order"
              border
              style="width: 100%; margin-bottom: 10px"
              max-height="300"
            >
              <el-table-column label="" width="50" align="center">
                <template #default>
                  <span class="drag-handle">⋮⋮</span>
                </template>
              </el-table-column>
              <el-table-column label="执行顺序" width="100" align="center">
                <template #default="{ row, $index }">
                  <el-input-number
                    v-model="row.order"
                    :min="1"
                    :max="form.testcases_order.length"
                    size="small"
                    @change="handleOrderChange"
                  />
                </template>
              </el-table-column>
              <el-table-column label="用例名称" min-width="200">
                <template #default="{ row }">
                  {{ getTestCaseName(row.id) }}
                </template>
              </el-table-column>
              <el-table-column label="操作" width="80" align="center">
                <template #default="{ $index }">
                  <el-button
                    type="danger"
                    size="small"
                    link
                    @click="removeTestCase($index)"
                  >
                    移除
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
            
            <!-- 搜索并添加测试用例 -->
            <div class="add-testcase-row">
              <el-select
                v-model="selectedTestCaseToAdd"
                placeholder="搜索并添加测试用例..."
                style="width: 70%"
                filterable
                clearable
              >
                <el-option
                  v-for="testcase in availableTestCases"
                  :key="testcase.id"
                  :label="testcase.name"
                  :value="testcase.id"
                />
              </el-select>
              <el-button
                type="success"
                style="width: 28%"
                @click="addTestCase"
                :disabled="!selectedTestCaseToAdd"
              >
                + 添加用例
              </el-button>
            </div>
          </div>
        </el-form-item>
        <el-form-item label="套件描述">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="3"
            placeholder="请输入套件描述"
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
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Plus } from '@element-plus/icons-vue'
import { getTestSuites, createTestSuite, updateTestSuite, deleteTestSuite, executeTestSuite, reorderTestCases } from '../api/testsuites'
import api from '../api/index'
import Sortable from 'sortablejs'

const loading = ref(false)
const searchQuery = ref('')
const testSuites = ref([])
const projects = ref([])
const testcases = ref([])
const environments = ref([])
const total = ref(0)
const submitting = ref(false)
const dialogVisible = ref(false)
const dialogTitle = ref('新建套件')
const formRef = ref(null)

const pagination = ref({
  page: 1,
  pageSize: 20
})

const stats = ref({
  total: 0,
  active: 0,
  totalCases: 0,
  avgCases: 0
})

const form = ref({
  id: null,
  name: '',
  project: null,
  environment: null,
  testcases_order: [],  // 格式：[{id: 1, order: 1}, {id: 2, order: 2}]
  description: '',
  is_active: true
})

const selectedTestCaseToAdd = ref(null)
let sortableInstance = null  // Sortable实例

const formRules = {
  name: [{ required: true, message: '请输入套件名称', trigger: 'blur' }],
  project: [{ required: true, message: '请选择所属项目', trigger: 'change' }],
  testcases_order: [{ 
    required: true, 
    message: '请至少添加一个测试用例', 
    trigger: 'change',
    validator: (rule, value, callback) => {
      if (!value || value.length === 0) {
        callback(new Error('请至少添加一个测试用例'))
      } else {
        callback()
      }
    }
  }]
}

// 获取可用的测试用例（排除已添加的）
const availableTestCases = computed(() => {
  const selectedIds = form.value.testcases_order.map(tc => tc.id)
  return testcases.value.filter(tc => !selectedIds.includes(tc.id))
})

const filteredTestSuites = computed(() => {
  if (!searchQuery.value) return testSuites.value
  return testSuites.value.filter((t) =>
    t.name.toLowerCase().includes(searchQuery.value.toLowerCase())
  )
})

const loadTestSuites = async () => {
  loading.value = true
  try {
    const response = await getTestSuites({
      page: pagination.value.page,
      page_size: pagination.value.pageSize
    })
    
    if (response.results) {
      testSuites.value = response.results
      total.value = response.count || response.results.length
    } else if (Array.isArray(response)) {
      testSuites.value = response
      total.value = response.length
    }

    calculateStats()
  } catch (error) {
    console.error('加载测试套件列表失败:', error)
    ElMessage.error('加载测试套件列表失败')
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

const loadTestCases = async () => {
  try {
    const response = await api.get('/testcases/testcases/', {
      params: { page_size: 10000 }  // 加载所有测试用例
    })
    testcases.value = Array.isArray(response) ? response : response.results || []
  } catch (error) {
    console.error('加载测试用例列表失败:', error)
  }
}

// 根据ID获取测试用例名称
const getTestCaseName = (id) => {
  const testcase = testcases.value.find(tc => tc.id === id)
  return testcase ? testcase.name : '未知用例'
}

// 添加测试用例
const addTestCase = () => {
  if (!selectedTestCaseToAdd.value) return
  
  // 添加到列表末尾，order为当前长度+1
  form.value.testcases_order.push({
    id: selectedTestCaseToAdd.value,
    order: form.value.testcases_order.length + 1
  })
  
  // 清空选择
  selectedTestCaseToAdd.value = null
  
  // 重新初始化拖拽
  nextTick(() => initSortable())
}

// 移除测试用例
const removeTestCase = (index) => {
  form.value.testcases_order.splice(index, 1)
  // 重新编号
  updateOrderNumbers()
  
  // 重新初始化拖拽
  nextTick(() => initSortable())
}

// 更新所有顺序号（使其连续）
const updateOrderNumbers = () => {
  form.value.testcases_order.forEach((item, index) => {
    item.order = index + 1
  })
}

// 初始化拖拽排序
const initSortable = async () => {
  await nextTick()
  
  // 销毁旧实例
  if (sortableInstance) {
    sortableInstance.destroy()
  }
  
  // 找到表格的tbody元素
  const tableEl = document.querySelector('.testcases-management .el-table__body tbody')
  if (!tableEl) return
  
  // 创建Sortable实例
  sortableInstance = Sortable.create(tableEl, {
    handle: '.drag-handle',  // 拖拽句柄
    animation: 150,
    onEnd: (evt) => {
      const { oldIndex, newIndex } = evt
      if (oldIndex === newIndex) return
      
      // 更新数组顺序
      const movedItem = form.value.testcases_order.splice(oldIndex, 1)[0]
      form.value.testcases_order.splice(newIndex, 0, movedItem)
      
      // 重新编号
      updateOrderNumbers()
      
      // 如果是编辑模式，保存新顺序
      if (form.value.id) {
        saveTestCasesOrder()
      }
    }
  })
}

// 保存测试用例顺序到后端
const saveTestCasesOrder = async () => {
  if (!form.value.id) return
  
  try {
    const testcase_orders = form.value.testcases_order.map((item) => ({
      testcase_id: item.id,
      order: item.order
    }))
    
    await reorderTestCases(form.value.id, testcase_orders)
    ElMessage.success('顺序已保存')
  } catch (error) {
    console.error('保存顺序失败:', error)
    ElMessage.error('保存顺序失败')
  }
}

// 手动修改顺序号后，重新排序
const handleOrderChange = () => {
  // 按order字段排序
  form.value.testcases_order.sort((a, b) => a.order - b.order)
  // 重新编号
  updateOrderNumbers()
  // 如果是编辑模式，保存新顺序
  if (form.value.id) {
    saveTestCasesOrder()
  }
}

const loadEnvironments = async () => {
  try {
    const response = await api.get('/environments/environments/')
    environments.value = Array.isArray(response) ? response : response.results || []
  } catch (error) {
    console.error('加载环境列表失败:', error)
  }
}

const calculateStats = () => {
  const total = testSuites.value.length
  const active = testSuites.value.filter((t) => t.is_active).length
  const totalCases = testSuites.value.reduce((sum, t) => {
    const count = t.testcases_with_order?.length || t.testcases?.length || 0
    return sum + count
  }, 0)
  const avgCases = total > 0 ? Math.round(totalCases / total) : 0

  stats.value = { total, active, totalCases, avgCases }
}

const handleCreate = () => {
  dialogTitle.value = '新建套件'
  form.value = {
    id: null,
    name: '',
    project: null,
    environment: null,
    testcases_order: [],
    description: '',
    is_active: true
  }
  selectedTestCaseToAdd.value = null
  dialogVisible.value = true
  
  // 初始化拖拽
  nextTick(() => initSortable())
}

const handleEdit = (row) => {
  dialogTitle.value = '编辑套件'
  
  // 将testcases_with_order转换为testcases_order格式
  let testcasesOrder = []
  if (row.testcases_with_order && Array.isArray(row.testcases_with_order)) {
    testcasesOrder = row.testcases_with_order.map(tc => ({
      id: tc.id,
      order: tc.order || 0
    }))
  } else if (row.testcases && Array.isArray(row.testcases)) {
    // 兼容旧格式（没有order字段）
    testcasesOrder = row.testcases.map((tc, index) => ({
      id: tc.id,
      order: index + 1
    }))
  }
  
  form.value = {
    id: row.id,
    name: row.name,
    project: row.project?.id || row.project,
    environment: row.environment?.id || row.environment,
    testcases_order: testcasesOrder,
    description: row.description || '',
    is_active: row.is_active
  }
  selectedTestCaseToAdd.value = null
  dialogVisible.value = true
  
  // 初始化拖拽
  nextTick(() => initSortable())
}

const handleSubmit = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (valid) {
      submitting.value = true
      try {
        // 构建提交数据
        const submitData = {
          name: form.value.name,
          project_id: form.value.project,
          environment_id: form.value.environment || null,
          testcases_order: form.value.testcases_order,  // 发送带order的用例列表
          description: form.value.description,
          is_active: form.value.is_active
        }
        
        if (form.value.id) {
          await updateTestSuite(form.value.id, submitData)
          ElMessage.success('更新成功')
        } else {
          await createTestSuite(submitData)
          ElMessage.success('创建成功')
        }
        dialogVisible.value = false
        await loadTestSuites()
      } catch (error) {
        console.error('提交失败:', error)
        ElMessage.error(error.response?.data?.detail || error.response?.data?.error || '操作失败')
      } finally {
        submitting.value = false
      }
    }
  })
}

const handleDialogClose = () => {
  formRef.value?.resetFields()
}

const handleExecute = async (row) => {
  try {
    row.executing = true
    await executeTestSuite(row.id)
    ElMessage.success('执行成功')
    await loadTestSuites()
  } catch (error) {
    console.error('执行失败:', error)
    ElMessage.error(error.response?.data?.detail || '执行失败')
  } finally {
    row.executing = false
  }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(`确定要删除套件 "${row.name}" 吗？`, '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    await deleteTestSuite(row.id)
    ElMessage.success('删除成功')
    await loadTestSuites()
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
  loadTestSuites()
}

const handlePageChange = (page) => {
  pagination.value.page = page
  loadTestSuites()
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
  loadTestSuites()
  loadProjects()
  loadTestCases()
  loadEnvironments()
})
</script>

<style scoped>
.testsuites-container {
  padding: 24px;
  background-color: #f5f7fa;
  min-height: calc(100vh - 60px);
}

.testsuites-header {
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

/* 测试用例管理样式 */
.testcases-management {
  width: 100%;
}

.drag-handle {
  cursor: move;
  color: #999;
  font-size: 18px;
  user-select: none;
}

.drag-handle:hover {
  color: #333;
}

.add-testcase-row {
  display: flex;
  gap: 10px;
  align-items: center;
}
</style>
