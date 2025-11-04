<template>
  <div class="executions-container">
    <!-- 顶部导航栏 -->
    <header class="executions-header">
      <div class="header-left">
        <h1 class="title">执行记录</h1>
        <p class="subtitle">查看测试执行历史和结果详情</p>
      </div>

      <div class="header-right">
        <el-select v-model="statusFilter" style="width: 120px" placeholder="状态筛选" clearable>
          <el-option label="全部" value="" />
          <el-option label="待执行" value="pending" />
          <el-option label="执行中" value="running" />
          <el-option label="通过" value="passed" />
          <el-option label="失败" value="failed" />
          <el-option label="跳过" value="skipped" />
        </el-select>
        <el-checkbox v-model="showAll" @change="handleShowAllChange" style="margin-left: 12px">
          显示所有记录（包括子用例）
        </el-checkbox>
        <el-input
          v-model="searchQuery"
          placeholder="搜索执行名称"
          style="width: 200px; margin-left: 12px"
          clearable
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <el-button
          type="danger"
          :disabled="selectedExecutions.length === 0"
          @click="handleBatchDelete"
          style="margin-left: 12px"
        >
          <el-icon><Delete /></el-icon>
          批量删除 ({{ selectedExecutions.length }})
        </el-button>
      </div>
    </header>

    <!-- 统计信息卡片 -->
    <section class="stats-grid">
      <transition-group name="fade-up" tag="div" class="stats-cards">
        <el-card :key="'total'" class="stat-card" shadow="hover">
          <div class="stat-label">总执行数</div>
          <div class="stat-value">{{ stats.total }}</div>
        </el-card>

        <el-card :key="'passed'" class="stat-card" shadow="hover">
          <div class="stat-label">通过</div>
          <div class="stat-value text-success">{{ stats.passed }}</div>
        </el-card>

        <el-card :key="'failed'" class="stat-card" shadow="hover">
          <div class="stat-label">失败</div>
          <div class="stat-value text-danger">{{ stats.failed }}</div>
        </el-card>

        <el-card :key="'rate'" class="stat-card" shadow="hover">
          <div class="stat-label">通过率</div>
          <div class="stat-value text-primary">{{ stats.passRate }}%</div>
        </el-card>
      </transition-group>
    </section>

    <!-- 执行记录列表 -->
    <el-card class="table-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <span class="card-title">执行记录列表</span>
          <span class="card-subtitle">共 {{ total }} 条</span>
        </div>
      </template>

      <el-table
        :data="executions"
        stripe
        style="width: 100%"
        v-loading="loading"
        empty-text="暂无执行记录"
        :row-style="{ height: '50px' }"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column type="expand" width="50">
          <template #default="{ row }">
            <div v-if="row.children && row.children.length > 0" style="padding: 12px 24px; background: #f5f7fa">
              <div style="font-weight: 600; margin-bottom: 12px; color: #606266">
                {{ row.execution_type === 'parameterized' ? '参数化执行详情' : '套件执行详情' }} (共{{ row.children.length }}条)
              </div>
              <el-table :data="row.children" stripe border size="small" :row-style="{ height: '45px' }">
                <el-table-column label="序号" width="80">
                  <template #default="{ $index }">
                    {{ $index + 1 }}
                  </template>
                </el-table-column>
                <el-table-column label="用例名称" min-width="200">
                  <template #default="{ row: child }">
                    {{ child.testcase?.name || child.name || '-' }}
                  </template>
                </el-table-column>
                <el-table-column label="状态" width="100">
                  <template #default="{ row: child }">
                    <el-tag :type="getStatusTagType(child.status)" size="small">
                      {{ getStatusText(child.status) }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column label="执行时长" width="120">
                  <template #default="{ row: child }">
                    <span v-if="child.duration">{{ formatDuration(child.duration) }}</span>
                    <span v-else class="text-gray">-</span>
                  </template>
                </el-table-column>
                <el-table-column label="操作" width="120">
                  <template #default="{ row: child }">
                    <el-button size="small" type="primary" link @click="handleViewChildExecution(child, row.id)">
                      查看详情
                    </el-button>
                  </template>
                </el-table-column>
              </el-table>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="执行名称" min-width="200" show-overflow-tooltip>
          <template #default="{ row }">
            <span v-if="row.execution_type === 'parameterized'">[参数化]</span>
            <span v-else-if="row.execution_type === 'suite'">[套件]</span>
            {{ row.name }}
          </template>
        </el-table-column>
        <el-table-column label="所属项目" width="150">
          <template #default="{ row }">
            {{ row.project?.name || '-' }}
          </template>
        </el-table-column>
        <el-table-column label="测试套件" width="150">
          <template #default="{ row }">
            {{ row.testsuite?.name || '-' }}
          </template>
        </el-table-column>
        <el-table-column label="测试用例" width="150" show-overflow-tooltip>
          <template #default="{ row }">
            {{ row.testcase?.name || '-' }}
          </template>
        </el-table-column>
        <el-table-column label="状态" width="120">
          <template #default="{ row }">
            <el-tag :type="getStatusTagType(row.status)" size="small">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="执行人" width="120">
          <template #default="{ row }">
            {{ row.executor?.username || '-' }}
          </template>
        </el-table-column>
        <el-table-column label="执行时长" width="120">
          <template #default="{ row }">
            <span v-if="row.duration">{{ formatDuration(row.duration) }}</span>
            <span v-else class="text-gray">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="start_time" label="开始时间" width="180">
          <template #default="{ row }">
            <span class="text-gray">{{ formatDate(row.start_time) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="260" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" link @click="handleView(row)">
              查看详情
            </el-button>
            <el-button type="success" size="small" link @click="exportReport(row.id)">
              导出报告
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

    <!-- 详情对话框 -->
    <el-dialog
      v-model="detailDialogVisible"
      title="执行详情"
      width="1200px"
      :before-close="handleDialogBeforeClose"
    >
      <div v-if="selectedExecution">
        <!-- 如果是子用例，显示返回套件详情按钮 -->
        <div v-if="selectedExecution.testsuite && selectedExecution.testcase && parentSuiteExecutionId" style="margin-bottom: 16px">
          <el-button type="primary" link @click="handleReturnToSuite">
            <el-icon style="margin-right: 4px"><ArrowLeft /></el-icon>
            返回套件执行详情
          </el-button>
        </div>

        <!-- 套件执行：显示总体统计信息 -->
        <div v-if="selectedExecution.testsuite && !selectedExecution.testcase && selectedExecution.result?.total !== undefined" class="suite-summary">
          <el-card shadow="never" style="margin-bottom: 16px">
            <template #header>
              <div style="display: flex; justify-content: space-between; align-items: center">
                <span style="font-weight: 600">套件执行概览</span>
                <el-tag :type="getStatusTagType(selectedExecution.status)" size="large">
                  {{ getStatusText(selectedExecution.status) }}
                </el-tag>
              </div>
            </template>
            <el-row :gutter="20">
              <el-col :span="6">
                <div class="summary-item">
                  <div class="summary-label">总用例数</div>
                  <div class="summary-value">{{ selectedExecution.result.total }}</div>
                </div>
              </el-col>
              <el-col :span="6">
                <div class="summary-item">
                  <div class="summary-label">通过</div>
                  <div class="summary-value text-success">{{ selectedExecution.result.passed }}</div>
                </div>
              </el-col>
              <el-col :span="6">
                <div class="summary-item">
                  <div class="summary-label">失败</div>
                  <div class="summary-value text-danger">{{ selectedExecution.result.failed }}</div>
                </div>
              </el-col>
              <el-col :span="6">
                <div class="summary-item">
                  <div class="summary-label">通过率</div>
                  <div class="summary-value text-primary">{{ selectedExecution.result.pass_rate }}%</div>
                </div>
              </el-col>
            </el-row>
          </el-card>
        </div>

        <!-- 基本信息 -->
        <el-descriptions :column="2" border>
          <el-descriptions-item label="执行名称">{{ selectedExecution.name }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="getStatusTagType(selectedExecution.status)">
              {{ getStatusText(selectedExecution.status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="所属项目">{{ selectedExecution.project?.name || '-' }}</el-descriptions-item>
          <el-descriptions-item label="测试套件">{{ selectedExecution.testsuite?.name || '-' }}</el-descriptions-item>
          <el-descriptions-item label="测试用例" v-if="selectedExecution.testcase">{{ selectedExecution.testcase?.name || '-' }}</el-descriptions-item>
          <el-descriptions-item label="执行人">{{ selectedExecution.executor?.username || '-' }}</el-descriptions-item>
          <el-descriptions-item label="开始时间">{{ formatDate(selectedExecution.start_time) }}</el-descriptions-item>
          <el-descriptions-item label="结束时间">{{ formatDate(selectedExecution.end_time) }}</el-descriptions-item>
          <el-descriptions-item label="执行时长" :span="selectedExecution.testcase ? 2 : 2">
            {{ selectedExecution.duration ? formatDuration(selectedExecution.duration) : '-' }}
          </el-descriptions-item>
        </el-descriptions>

        <!-- 套件执行：子用例列表 -->
        <div v-if="selectedExecution.children && selectedExecution.children.length > 0">
          <el-divider>{{ selectedExecution.execution_type === 'parameterized' ? '参数化' : '套件' }}执行详情</el-divider>
          <el-table :data="selectedExecution.children" stripe border :row-style="{ height: '50px' }">
            <el-table-column type="expand" width="50">
              <template #default="{ row }">
                <div class="child-execution-detail">
                  <el-descriptions :column="2" border size="small">
                    <el-descriptions-item label="HTTP请求时间">
                      <span v-if="row.result?.time">{{ Number(row.result.time).toFixed(4) }}ms</span>
                      <span v-else-if="row.duration">{{ (row.duration * 1000).toFixed(4) }}ms</span>
                      <span v-else>-</span>
                    </el-descriptions-item>
                    <el-descriptions-item label="状态">
                      <el-tag :type="getStatusTagType(row.status)" size="small">
                        {{ getStatusText(row.status) }}
                      </el-tag>
                    </el-descriptions-item>
                  </el-descriptions>
                  <div v-if="row.result" style="margin-top: 12px">
                    <div class="result-header" style="margin-bottom: 8px">
                      <span style="font-weight: 600">执行结果</span>
                      <el-tag v-if="row.result.status_code" size="small" :type="row.result.status_code < 300 ? 'success' : 'danger'">
                        HTTP {{ row.result.status_code }}
                      </el-tag>
                      <el-tag v-if="row.result.time" size="small" type="info" style="margin-left: 8px">
                        耗时 {{ Number(row.result.time).toFixed(4) }}ms
                      </el-tag>
                    </div>
                    <pre v-if="row.result.json" class="result-json-small">
{{ JSON.stringify(row.result.json, null, 2) }}
                    </pre>
                    <pre v-else-if="row.result.body" class="result-json-small">
{{ row.result.body }}
                    </pre>
                    <div v-if="row.result.assertions && row.result.assertions.length > 0" style="margin-top: 8px">
                      <div style="font-weight: 600; margin-bottom: 4px">断言结果:</div>
                      <div>
                        <el-tag 
                          v-for="(assertion, idx) in row.result.assertions" 
                          :key="idx"
                          :type="assertion.success ? 'success' : 'danger'"
                          size="small"
                          style="margin: 2px 4px 2px 0"
                        >
                          {{ assertion.message || assertion.description || `断言 ${idx + 1}` }}
                        </el-tag>
                      </div>
                    </div>
                  </div>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="用例名称" min-width="200">
              <template #default="{ row }">
                {{ row.testcase?.name || '-' }}
              </template>
            </el-table-column>
            <el-table-column label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="getStatusTagType(row.status)" size="small">
                  {{ getStatusText(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="HTTP请求时间" width="120">
              <template #default="{ row }">
                <span v-if="row.result?.time">{{ Number(row.result.time).toFixed(4) }}ms</span>
                <span v-else-if="row.duration">{{ (row.duration * 1000).toFixed(4) }}ms</span>
                <span v-else class="text-gray">-</span>
              </template>
            </el-table-column>
            <el-table-column label="HTTP状态" width="100">
              <template #default="{ row }">
                <el-tag v-if="row.result?.status_code" size="small" :type="row.result.status_code < 300 ? 'success' : 'danger'">
                  {{ row.result.status_code }}
                </el-tag>
                <span v-else class="text-gray">-</span>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="120">
              <template #default="{ row }">
                    <el-button size="small" type="primary" link @click="handleViewChildExecution(row, selectedExecution?.id)">
                      查看详情
                    </el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
        
        <el-divider>
          <span>执行结果</span>
          <el-button 
            v-if="selectedExecution.result" 
            type="text" 
            size="small" 
            style="margin-left: 12px"
            @click="showFullResult = !showFullResult"
          >
            {{ showFullResult ? '收起完整结果' : '查看完整结果' }}
          </el-button>
        </el-divider>
        
        <!-- 单个用例或套件未展开时显示结果 -->
        <el-card v-if="selectedExecution.result && (selectedExecution.testcase || !selectedExecution.child_executions || selectedExecution.child_executions.length === 0)">
          <!-- 默认只显示接口返回数据 -->
          <div v-if="!showFullResult">
            <div class="result-header">
              <span class="result-title">接口返回数据</span>
              <el-tag v-if="selectedExecution.result.status_code" size="small" :type="selectedExecution.result.status_code < 300 ? 'success' : 'danger'">
                HTTP {{ selectedExecution.result.status_code }}
              </el-tag>
              <el-tag v-if="selectedExecution.result.time" size="small" type="info" style="margin-left: 8px">
                耗时 {{ Number(selectedExecution.result.time).toFixed(4) }}ms
              </el-tag>
            </div>
            
            <!-- 优先显示JSON响应，如果没有则显示body文本 -->
            <pre v-if="selectedExecution.result.json" class="result-json">
{{ JSON.stringify(selectedExecution.result.json, null, 2) }}
            </pre>
            <pre v-else-if="selectedExecution.result.body" class="result-json">
{{ selectedExecution.result.body }}
            </pre>
            <el-empty v-else description="无返回数据" />
            
            <!-- 断言结果摘要 -->
            <div v-if="selectedExecution.result.assertions && selectedExecution.result.assertions.length > 0" class="assertions-summary">
              <el-divider style="margin: 16px 0" />
              <div class="assertions-header">断言结果</div>
              <div class="assertions-list">
                <el-tag 
                  v-for="(assertion, index) in selectedExecution.result.assertions" 
                  :key="index"
                  :type="assertion.success ? 'success' : 'danger'"
                  size="small"
                  style="margin: 4px 8px 4px 0"
                >
                  {{ assertion.message || assertion.description || `断言 ${index + 1}` }}
                  <el-icon :style="{ marginLeft: '4px' }">
                    <Check v-if="assertion.success" />
                    <Close v-else />
                  </el-icon>
                </el-tag>
              </div>
            </div>
          </div>
          
          <!-- 完整结果（包含所有技术细节） -->
          <div v-else>
            <pre class="result-json">{{ JSON.stringify(selectedExecution.result, null, 2) }}</pre>
          </div>
        </el-card>
        <el-empty v-else description="暂无执行结果" />
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, Check, Close, ArrowLeft, Delete } from '@element-plus/icons-vue'
import { ElMessageBox } from 'element-plus'
import { getExecutions, getExecution, deleteExecution, batchDeleteExecutions } from '../api/executions'

const loading = ref(false)
const searchQuery = ref('')
const statusFilter = ref('')
const showAll = ref(false) // 是否显示所有记录（包括子用例）
const executions = ref([])
const total = ref(0)
const detailDialogVisible = ref(false)
const selectedExecution = ref(null)
const selectedExecutions = ref([]) // 选中的执行记录（用于批量删除）
const showFullResult = ref(false) // 是否显示完整结果
const expandedChildCases = ref({}) // 展开的子用例详情
const parentSuiteExecutionId = ref(null) // 父套件执行ID（用于返回套件详情）

const pagination = ref({
  page: 1,
  pageSize: 20
})

const stats = ref({
  total: 0,
  passed: 0,
  failed: 0,
  passRate: 0
})

const filteredExecutions = computed(() => {
  let filtered = executions.value

  // 状态过滤
  if (statusFilter.value) {
    filtered = filtered.filter((e) => e.status === statusFilter.value)
  }

  // 搜索过滤
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    filtered = filtered.filter((e) =>
      e.name.toLowerCase().includes(query)
    )
  }

  return filtered
})

const loadExecutions = async () => {
  loading.value = true
  try {
    const response = await getExecutions({
      page: pagination.value.page,
      page_size: pagination.value.pageSize,
      show_all: showAll.value
    })
    
    if (response.results) {
      executions.value = response.results
      total.value = response.count || response.results.length
    } else if (Array.isArray(response)) {
      executions.value = response
      total.value = response.length
    }

    calculateStats()
  } catch (error) {
    console.error('加载执行记录失败:', error)
    ElMessage.error('加载执行记录失败')
  } finally {
    loading.value = false
  }
}

const calculateStats = () => {
  const total = executions.value.length
  const passed = executions.value.filter((e) => e.status === 'passed').length
  const failed = executions.value.filter((e) => e.status === 'failed').length
  const passRate = total > 0 ? Math.round((passed / total) * 100) : 0

  stats.value = { total, passed, failed, passRate }
}

const handleView = async (row) => {
  try {
    const execution = await getExecution(row.id)
    selectedExecution.value = execution
    showFullResult.value = false // 重置为简化视图
    expandedChildCases.value = {} // 重置展开状态
    parentSuiteExecutionId.value = null // 清空父套件ID（这是套件级别的查看）
    detailDialogVisible.value = true
  } catch (error) {
    console.error('获取执行详情失败:', error)
    ElMessage.error('获取执行详情失败')
  }
}

const handleViewChildCase = async (childExecution, suiteExecutionId = null) => {
  // 打开子用例的详情对话框（兼容旧代码）
  await handleViewChildExecution(childExecution, suiteExecutionId)
}

const handleViewChildExecution = async (childExecution, parentExecutionId = null) => {
  // 打开子执行记录的详情对话框
  try {
    const execution = await getExecution(childExecution.id || childExecution)
    selectedExecution.value = execution
    showFullResult.value = false
    // 优先使用传入的父执行ID，否则使用后端返回的parent_id
    parentSuiteExecutionId.value = parentExecutionId || execution.parent_id || null
    detailDialogVisible.value = true
  } catch (error) {
    console.error('获取子执行详情失败:', error)
    ElMessage.error('获取子执行详情失败')
  }
}

const handleReturnToSuite = async () => {
  // 返回到套件执行详情
  if (parentSuiteExecutionId.value) {
    try {
      const suiteExecution = await getExecution(parentSuiteExecutionId.value)
      selectedExecution.value = suiteExecution
      showFullResult.value = false
      parentSuiteExecutionId.value = null // 套件详情页面不需要返回按钮
      // 对话框已经打开，直接更新内容即可
    } catch (error) {
      console.error('获取套件执行详情失败:', error)
      ElMessage.error('获取套件执行详情失败')
    }
  }
}

const handleDialogBeforeClose = (done) => {
  // 关闭对话框前的处理
  if (parentSuiteExecutionId.value && selectedExecution.value?.testsuite && selectedExecution.value?.testcase) {
    // 如果是子用例且有父套件ID，自动切换到套件详情（不关闭对话框）
    handleReturnToSuite()
    // 阻止对话框关闭
    done(false)
  } else {
    // 否则正常关闭
    selectedExecution.value = null
    parentSuiteExecutionId.value = null
    done()
  }
}

const handleShowAllChange = () => {
  // 切换显示模式时重新加载数据
  pagination.value.page = 1
  loadExecutions()
}

const handleSizeChange = (size) => {
  pagination.value.pageSize = size
  pagination.value.page = 1
  loadExecutions()
}

const handlePageChange = (page) => {
  pagination.value.page = page
  loadExecutions()
}

const handleSelectionChange = (selection) => {
  selectedExecutions.value = selection
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除执行记录 "${row.name}" 吗？`,
      '确认删除',
      {
        type: 'warning'
      }
    )
    await deleteExecution(row.id)
    ElMessage.success('删除成功')
    await loadExecutions()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
      ElMessage.error(error.response?.data?.detail || '删除失败')
    }
  }
}

const handleBatchDelete = async () => {
  if (selectedExecutions.value.length === 0) {
    ElMessage.warning('请先选择要删除的执行记录')
    return
  }

  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedExecutions.value.length} 条执行记录吗？`,
      '确认批量删除',
      {
        type: 'warning'
      }
    )
    
    const ids = selectedExecutions.value.map(e => e.id)
    await batchDeleteExecutions(ids)
    ElMessage.success(`成功删除 ${ids.length} 条执行记录`)
    selectedExecutions.value = []
    await loadExecutions()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('批量删除失败:', error)
      ElMessage.error(error.response?.data?.error || error.response?.data?.detail || '批量删除失败')
    }
  }
}

const exportReport = async (executionId) => {
  try {
    const url = `/api/executions/executions/${executionId}/export_report/`
    
    // 使用fetch下载文件
    const response = await fetch(url, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      }
    })
    
    if (!response.ok) {
      throw new Error('导出失败')
    }
    
    // 获取文件名
    const contentDisposition = response.headers.get('Content-Disposition')
    let filename = `test_report_${executionId}.html`
    if (contentDisposition) {
      const filenameMatch = contentDisposition.match(/filename="?(.+)"?/)
      if (filenameMatch) {
        filename = filenameMatch[1]
      }
    }
    
    // 获取blob数据
    const blob = await response.blob()
    
    // 创建下载链接
    const downloadUrl = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = downloadUrl
    link.download = filename
    document.body.appendChild(link)
    link.click()
    
    // 清理
    document.body.removeChild(link)
    window.URL.revokeObjectURL(downloadUrl)
    
    ElMessage.success('报告导出成功')
  } catch (error) {
    console.error('导出失败:', error)
    ElMessage.error('导出报告失败')
  }
}

const getStatusTagType = (status) => {
  const types = {
    passed: 'success',
    failed: 'danger',
    running: 'warning',
    pending: 'info',
    skipped: 'info'
  }
  return types[status] || 'info'
}

const getStatusText = (status) => {
  const texts = {
    pending: '待执行',
    running: '执行中',
    passed: '通过',
    failed: '失败',
    skipped: '跳过'
  }
  return texts[status] || status
}

const formatDuration = (duration) => {
  if (!duration && duration !== 0) return '-'
  // 保留4位小数
  return `${Number(duration).toFixed(4)}s`
}

const formatDate = (dateString) => {
  if (!dateString) return '-'
  const date = new Date(dateString)
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  const seconds = String(date.getSeconds()).padStart(2, '0')
  return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`
}

onMounted(() => {
  loadExecutions()
})
</script>

<style scoped>
.executions-container {
  padding: 24px;
  background-color: #f5f7fa;
  min-height: calc(100vh - 60px);
}

.executions-header {
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

.stat-value.text-danger {
  color: #ef4444;
}

.stat-value.text-primary {
  color: #409eff;
}

.table-card {
  margin-bottom: 24px;
}

/* 统一表格行高，确保行间距一致 */
:deep(.el-table .el-table__row) {
  height: 50px !important;
}

:deep(.el-table .el-table__cell) {
  padding: 8px 0 !important;
  line-height: 34px !important;
  white-space: nowrap !important;
  overflow: hidden;
  text-overflow: ellipsis;
}

:deep(.el-table .el-table__body tr) {
  height: 50px !important;
}

/* 确保表格单元格内容不换行 */
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

.result-header {
  display: flex;
  align-items: center;
  margin-bottom: 12px;
  padding-bottom: 12px;
  border-bottom: 1px solid #ebeef5;
}

.result-title {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  margin-right: 12px;
}

.result-json {
  background-color: #f5f7fa;
  padding: 16px;
  border-radius: 4px;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 13px;
  line-height: 1.6;
  overflow-x: auto;
  max-height: 500px;
  overflow-y: auto;
  margin: 0;
  border: 1px solid #e4e7ed;
}

.result-json-small {
  background-color: #f5f7fa;
  padding: 12px;
  border-radius: 4px;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 12px;
  line-height: 1.5;
  overflow-x: auto;
  max-height: 300px;
  overflow-y: auto;
  margin: 0;
  border: 1px solid #e4e7ed;
}

.suite-summary {
  margin-bottom: 16px;
}

.summary-item {
  text-align: center;
  padding: 12px;
}

.summary-label {
  font-size: 14px;
  color: #909399;
  margin-bottom: 8px;
}

.summary-value {
  font-size: 28px;
  font-weight: bold;
  color: #303133;
}

.summary-value.text-success {
  color: #10b981;
}

.summary-value.text-danger {
  color: #ef4444;
}

.summary-value.text-primary {
  color: #409eff;
}

.child-execution-detail {
  padding: 16px;
  background-color: #fafafa;
}

.assertions-summary {
  margin-top: 16px;
}

.assertions-header {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 12px;
}

.assertions-list {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
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

