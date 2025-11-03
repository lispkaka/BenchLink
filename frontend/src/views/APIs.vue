<template>
  <div class="apis-container">
    <!-- 顶部导航栏 -->
    <header class="apis-header">
      <div class="header-left">
        <h1 class="title">接口管理</h1>
        <p class="subtitle">管理和测试 API 接口</p>
      </div>

      <div class="header-right">
        <el-select v-model="methodFilter" style="width: 120px" placeholder="方法筛选" clearable>
          <el-option label="GET" value="GET" />
          <el-option label="POST" value="POST" />
          <el-option label="PUT" value="PUT" />
          <el-option label="DELETE" value="DELETE" />
        </el-select>
        <el-input
          v-model="searchQuery"
          placeholder="搜索接口名称或路径"
          style="width: 200px"
          clearable
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <el-button type="primary" @click="handleCreate">
          <el-icon><Plus /></el-icon>
          新建接口
        </el-button>
      </div>
    </header>

    <!-- 统计信息卡片 -->
    <section class="stats-grid">
      <transition-group name="fade-up" tag="div" class="stats-cards">
        <el-card :key="'total'" class="stat-card" shadow="hover">
          <div class="stat-label">接口总数</div>
          <div class="stat-value">{{ stats.total }}</div>
        </el-card>

        <el-card :key="'get'" class="stat-card" shadow="hover">
          <div class="stat-label">GET</div>
          <div class="stat-value text-primary">{{ stats.get }}</div>
        </el-card>

        <el-card :key="'post'" class="stat-card" shadow="hover">
          <div class="stat-label">POST</div>
          <div class="stat-value text-success">{{ stats.post }}</div>
        </el-card>

        <el-card :key="'others'" class="stat-card" shadow="hover">
          <div class="stat-label">其他方法</div>
          <div class="stat-value text-info">{{ stats.others }}</div>
        </el-card>
      </transition-group>
    </section>

    <!-- 接口列表 -->
    <el-card class="table-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <span class="card-title">接口列表</span>
          <span class="card-subtitle">共 {{ filteredAPIs.length }} 个</span>
        </div>
      </template>

      <el-table
        :data="filteredAPIs"
        stripe
        style="width: 100%"
        v-loading="loading"
        empty-text="暂无接口"
      >
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="接口名称" min-width="180" show-overflow-tooltip />
        <el-table-column label="方法" width="100">
          <template #default="{ row }">
            <el-tag :type="getMethodTagType(row.method)" size="small">
              {{ row.method }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="接口路径" min-width="300" show-overflow-tooltip>
          <template #default="{ row }">
            <code class="endpoint-code">{{ row.url }}</code>
          </template>
        </el-table-column>
        <el-table-column label="所属项目" width="150">
          <template #default="{ row }">
            {{ row.project?.name || '-' }}
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
      width="900px"
      @close="handleDialogClose"
    >
      <el-tabs v-model="activeTab" type="border-card">
        <!-- 基本信息 -->
        <el-tab-pane label="基本信息" name="basic">
          <el-form ref="formRef" :model="form" :rules="formRules" label-width="100px" style="margin-top: 20px">
            <el-form-item label="接口名称" prop="name">
              <el-input v-model="form.name" placeholder="请输入接口名称" />
            </el-form-item>
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="请求方法" prop="method">
                  <el-select v-model="form.method" placeholder="请选择方法" style="width: 100%">
                    <el-option label="GET" value="GET" />
                    <el-option label="POST" value="POST" />
                    <el-option label="PUT" value="PUT" />
                    <el-option label="PATCH" value="PATCH" />
                    <el-option label="DELETE" value="DELETE" />
                  </el-select>
                </el-form-item>
              </el-col>
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
            </el-row>
            <el-form-item label="接口路径" prop="url">
              <el-input v-model="form.url" placeholder="例如: /api/users/login 或 https://api.example.com/login" />
            </el-form-item>
            <el-form-item label="接口描述">
              <el-input
                v-model="form.description"
                type="textarea"
                :rows="3"
                placeholder="请输入接口描述"
              />
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <!-- 请求参数 -->
        <el-tab-pane label="请求参数" name="params">
          <div style="margin-top: 20px">
            <!-- 查询参数 -->
            <el-card shadow="never" style="margin-bottom: 16px">
              <template #header>
                <span style="font-weight: 600">查询参数 (Query Parameters)</span>
              </template>
              <el-input
                v-model="paramsText"
                type="textarea"
                :rows="6"
                placeholder='输入JSON格式的查询参数，例如：&#10;{&#10;  "page": 1,&#10;  "size": 20&#10;}'
                style="font-family: monospace"
                @blur="parseParams"
              />
            </el-card>

            <!-- 请求头 -->
            <el-card shadow="never" style="margin-bottom: 16px">
              <template #header>
                <span style="font-weight: 600">请求头 (Headers)</span>
              </template>
              <el-input
                v-model="headersText"
                type="textarea"
                :rows="6"
                placeholder='输入JSON格式的请求头，例如：&#10;{&#10;  "Content-Type": "application/json",&#10;  "User-Agent": "BenchLink/1.0"&#10;}'
                style="font-family: monospace"
                @blur="parseHeaders"
              />
            </el-card>

            <!-- 请求体 (POST/PUT/PATCH) -->
            <el-card v-if="['POST', 'PUT', 'PATCH'].includes(form.method)" shadow="never">
              <template #header>
                <span style="font-weight: 600">请求体 (Request Body)</span>
              </template>
              <el-input
                v-model="bodyText"
                type="textarea"
                :rows="10"
                placeholder='输入JSON格式的请求体，例如：&#10;{&#10;  "username": "admin",&#10;  "password": "123456"&#10;}'
                style="font-family: monospace"
                @blur="parseBody"
              />
              <div style="margin-top: 8px; font-size: 12px; color: #909399">
                💡 提示：支持变量替换，使用 ${variable} 格式
              </div>
            </el-card>
            <el-alert
              v-else
              title="GET/DELETE 请求通常不需要请求体"
              type="info"
              :closable="false"
            />
          </div>
        </el-tab-pane>

        <!-- 认证配置 -->
        <el-tab-pane label="认证配置" name="auth">
          <div style="margin-top: 20px">
            <el-form :model="form" label-width="120px">
              <el-form-item label="认证类型">
                <el-select v-model="form.auth_type" placeholder="请选择认证类型" style="width: 300px" clearable>
                  <el-option label="Bearer Token" value="bearer" />
                  <el-option label="Basic Auth" value="basic" />
                </el-select>
              </el-form-item>

              <!-- Bearer Token 配置 -->
              <template v-if="form.auth_type === 'bearer'">
                <el-form-item label="Token">
                  <el-input
                    v-model="authConfig.token"
                    type="textarea"
                    :rows="3"
                    placeholder="输入Token，支持变量：${token}"
                  />
                </el-form-item>
              </template>

              <!-- Basic Auth 配置 -->
              <template v-if="form.auth_type === 'basic'">
                <el-form-item label="用户名">
                  <el-input
                    v-model="authConfig.username"
                    placeholder="输入用户名，支持变量：${username}"
                  />
                </el-form-item>
                <el-form-item label="密码">
                  <el-input
                    v-model="authConfig.password"
                    type="password"
                    show-password
                    placeholder="输入密码，支持变量：${password}"
                  />
                </el-form-item>
              </template>
            </el-form>
          </div>
        </el-tab-pane>

        <!-- 参数化配置 -->
        <el-tab-pane label="参数化配置" name="parameterized">
          <div style="margin-top: 20px">
            <el-form :model="form" label-width="120px">
              <el-form-item label="参数化模式">
                <el-radio-group v-model="form.parameterized_mode">
                  <el-radio label="disabled">禁用</el-radio>
                  <el-radio label="enabled">启用</el-radio>
                </el-radio-group>
                <div style="font-size: 12px; color: #909399; margin-top: 8px">
                  💡 启用后，接口将使用参数化数据循环执行多次
                </div>
              </el-form-item>

              <el-form-item v-if="form.parameterized_mode === 'enabled'" label="参数化数据">
                <el-input
                  v-model="parameterizedDataText"
                  type="textarea"
                  :rows="10"
                  placeholder='输入JSON数组格式的参数化数据，例如：&#10;[&#10;  {"post_id": 1},&#10;  {"post_id": 2},&#10;  {"post_id": 3}&#10;]&#10;&#10;每个对象代表一组参数，会依次替换接口URL/Body中的变量'
                  style="font-family: monospace; font-size: 13px"
                  @blur="parseParameterizedData"
                />
                <div style="margin-top: 8px; font-size: 12px; color: #909399">
                  💡 格式：JSON数组，每个元素是一个对象，对象的key对应接口中的变量名（如${post_id}），value为要替换的值
                </div>
              </el-form-item>
            </el-form>
          </div>
        </el-tab-pane>
      </el-tabs>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">
          确定
        </el-button>
      </template>
    </el-dialog>

    <!-- 执行结果对话框 -->
    <el-dialog
      v-model="executeResultDialog"
      title="执行结果"
      width="900px"
    >
      <div v-if="executeResult">
        <!-- 参数化结果 -->
        <div v-if="executeResult.parameterized">
          <el-alert
            :title="`参数化执行完成：共${executeResult.total}次，${executeResult.passed}次通过，${executeResult.failed}次失败，总耗时${executeResult.total_time}ms`"
            :type="executeResult.failed > 0 ? 'warning' : 'success'"
            :closable="false"
            style="margin-bottom: 20px"
          />
          
          <el-table :data="executeResult.results" stripe style="width: 100%">
            <el-table-column prop="index" label="序号" width="80" />
            <el-table-column label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="row.success ? 'success' : 'danger'" size="small">
                  {{ row.success ? '通过' : '失败' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="status_code" label="状态码" width="100" />
            <el-table-column prop="url" label="请求URL" min-width="300" show-overflow-tooltip />
            <el-table-column prop="time" label="耗时(ms)" width="100" />
            <el-table-column label="操作" width="100">
              <template #default="{ row }">
                <el-button type="primary" size="small" link @click="viewResultDetail(row)">
                  查看详情
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
        
        <!-- 单次执行结果 -->
        <div v-else>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="状态">
              <el-tag :type="executeResult.success ? 'success' : 'danger'" size="small">
                {{ executeResult.success ? '成功' : '失败' }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="状态码">{{ executeResult.status_code }}</el-descriptions-item>
            <el-descriptions-item label="请求URL" :span="2">
              <code style="font-size: 12px">{{ executeResult.url }}</code>
            </el-descriptions-item>
            <el-descriptions-item label="耗时">{{ executeResult.time }}ms</el-descriptions-item>
            <el-descriptions-item label="错误信息" v-if="executeResult.error" :span="2">
              <el-text type="danger">{{ executeResult.error }}</el-text>
            </el-descriptions-item>
          </el-descriptions>
          
          <el-divider>响应内容</el-divider>
          <el-input
            v-model="executeResult.body"
            type="textarea"
            :rows="15"
            readonly
            style="font-family: monospace; font-size: 13px"
          />
        </div>
      </div>
      
      <template #footer>
        <el-button type="primary" @click="executeResultDialog = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Plus } from '@element-plus/icons-vue'
import { getAPIs, createAPI, updateAPI, deleteAPI, executeAPI } from '../api/apis'
import api from '../api/index'

const loading = ref(false)
const searchQuery = ref('')
const methodFilter = ref('')
const apis = ref([])
const projects = ref([])
const total = ref(0)
const submitting = ref(false)
const dialogVisible = ref(false)
const dialogTitle = ref('新建接口')
const formRef = ref(null)
const activeTab = ref('basic')

// JSON编辑器文本（用于显示和编辑）
const paramsText = ref('{}')
const headersText = ref('{}')
const bodyText = ref('{}')
const parameterizedDataText = ref('[]')
const authConfig = ref({
  token: '',
  username: '',
  password: ''
})

const pagination = ref({
  page: 1,
  pageSize: 20
})

const stats = ref({
  total: 0,
  get: 0,
  post: 0,
  others: 0
})

const form = ref({
  id: null,
  name: '',
  method: 'GET',
  url: '',
  project: null,
  description: '',
  headers: {},
  params: {},
  body: {},
  auth_type: '',
  auth_config: {},
  parameterized_mode: 'disabled',
  parameterized_data: []
})

const formRules = {
  name: [{ required: true, message: '请输入接口名称', trigger: 'blur' }],
  method: [{ required: true, message: '请选择请求方法', trigger: 'change' }],
  url: [{ required: true, message: '请输入接口路径', trigger: 'blur' }],
  project: [{ required: true, message: '请选择所属项目', trigger: 'change' }]
}

const filteredAPIs = computed(() => {
  let filtered = apis.value

  // 方法过滤
  if (methodFilter.value) {
    filtered = filtered.filter((a) => a.method === methodFilter.value)
  }

  // 搜索过滤
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    filtered = filtered.filter(
      (a) =>
        a.name.toLowerCase().includes(query) ||
        a.url.toLowerCase().includes(query)
    )
  }

  return filtered
})

const loadAPIs = async () => {
  loading.value = true
  try {
    const response = await getAPIs({
      page: pagination.value.page,
      page_size: pagination.value.pageSize
    })
    
    if (response.results) {
      apis.value = response.results
      total.value = response.count || response.results.length
    } else if (Array.isArray(response)) {
      apis.value = response
      total.value = response.length
    }

    calculateStats()
  } catch (error) {
    console.error('加载接口列表失败:', error)
    ElMessage.error('加载接口列表失败')
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

const calculateStats = () => {
  const total = apis.value.length
  const get = apis.value.filter((a) => a.method === 'GET').length
  const post = apis.value.filter((a) => a.method === 'POST').length
  const others = total - get - post

  stats.value = { total, get, post, others }
}

const handleCreate = () => {
  dialogTitle.value = '新建接口'
  form.value = {
    id: null,
    name: '',
    method: 'GET',
    url: '',
    project: null,
    description: '',
    headers: {},
    params: {},
    body: {},
    auth_type: '',
    auth_config: {},
    parameterized_mode: 'disabled',
    parameterized_data: []
  }
  paramsText.value = '{}'
  headersText.value = '{}'
  bodyText.value = '{}'
  parameterizedDataText.value = '[]'
  authConfig.value = { token: '', username: '', password: '' }
  activeTab.value = 'basic'
  dialogVisible.value = true
}

const handleEdit = (row) => {
  dialogTitle.value = '编辑接口'
  form.value = {
    id: row.id,
    name: row.name,
    method: row.method,
    url: row.url,
    project: row.project?.id || row.project,
    description: row.description || '',
    headers: row.headers || {},
    params: row.params || {},
    body: row.body || {},
    auth_type: row.auth_type || '',
    auth_config: row.auth_config || {},
    parameterized_mode: row.parameterized_mode || 'disabled',
    parameterized_data: row.parameterized_data || []
  }
  
  // 将JSON对象转换为文本
  paramsText.value = JSON.stringify(form.value.params, null, 2)
  headersText.value = JSON.stringify(form.value.headers, null, 2)
  bodyText.value = JSON.stringify(form.value.body, null, 2)
  parameterizedDataText.value = JSON.stringify(form.value.parameterized_data, null, 2)
  
  // 设置认证配置
  authConfig.value = {
    token: form.value.auth_config.token || '',
    username: form.value.auth_config.username || '',
    password: form.value.auth_config.password || ''
  }
  
  activeTab.value = 'basic'
  dialogVisible.value = true
}

// 修复JSON格式（自动添加双引号到键名）
const fixJSONFormat = (text) => {
  if (!text || text.trim() === '' || text.trim() === '{}') {
    return text
  }
  
  try {
    // 尝试直接解析，如果成功则不需要修复
    JSON.parse(text)
    return text
  } catch (e) {
    // 如果解析失败，尝试修复常见的JavaScript对象字面量格式
    // 匹配 {key: value} 格式，将 key 添加双引号
    let fixed = text.trim()
    
    // 处理对象键名：将 {key: 或 ,key: 转换为 {"key": 或 ,"key":
    fixed = fixed.replace(/([{,]\s*)([a-zA-Z_$][a-zA-Z0-9_$]*)\s*:/g, '$1"$2":')
    
    // 再次尝试解析
    try {
      JSON.parse(fixed)
      return fixed
    } catch (e2) {
      // 如果还是失败，返回原文本让错误处理
      return text
    }
  }
}

// 解析JSON文本
const parseParams = () => {
  try {
    // 先尝试修复格式
    const fixedText = fixJSONFormat(paramsText.value || '{}')
    form.value.params = JSON.parse(fixedText)
    
    // 如果修复后的文本与原始文本不同，更新显示
    if (fixedText !== paramsText.value && fixedText !== '{}') {
      paramsText.value = JSON.stringify(form.value.params, null, 2)
      ElMessage.success('已自动修复JSON格式（添加了键名的双引号）')
    }
  } catch (e) {
    ElMessage.error(`查询参数JSON格式错误：${e.message}。提示：JSON格式要求键名必须用双引号括起来，例如：{"key": "value"}`)
    paramsText.value = '{}'
    form.value.params = {}
  }
}

const parseHeaders = () => {
  try {
    const fixedText = fixJSONFormat(headersText.value || '{}')
    form.value.headers = JSON.parse(fixedText)
    
    if (fixedText !== headersText.value && fixedText !== '{}') {
      headersText.value = JSON.stringify(form.value.headers, null, 2)
      ElMessage.success('已自动修复JSON格式（添加了键名的双引号）')
    }
  } catch (e) {
    ElMessage.error(`请求头JSON格式错误：${e.message}。提示：JSON格式要求键名必须用双引号括起来，例如：{"Content-Type": "application/json"}`)
    headersText.value = '{}'
    form.value.headers = {}
  }
}

const parseBody = () => {
  try {
    const fixedText = fixJSONFormat(bodyText.value || '{}')
    form.value.body = JSON.parse(fixedText)
    
    if (fixedText !== bodyText.value && fixedText !== '{}') {
      bodyText.value = JSON.stringify(form.value.body, null, 2)
      ElMessage.success('已自动修复JSON格式（添加了键名的双引号）')
    }
  } catch (e) {
    ElMessage.error(`请求体JSON格式错误：${e.message}。提示：JSON格式要求键名必须用双引号括起来，例如：{"username": "admin", "password": "123456"}`)
    bodyText.value = '{}'
    form.value.body = {}
  }
}

const handleSubmit = async () => {
  if (!formRef.value) return

  // 验证基本信息（只在基本信息标签页时验证）
  if (activeTab.value === 'basic') {
    await formRef.value.validate(async (valid) => {
      if (valid) {
        await submitForm()
      }
    })
  } else {
    await submitForm()
  }
}

const submitForm = async () => {
  submitting.value = true
  try {
    // 确保JSON已解析
    parseParams()
    parseHeaders()
    if (['POST', 'PUT', 'PATCH'].includes(form.value.method)) {
      parseBody()
    }
    
    // 构建认证配置
    if (form.value.auth_type) {
      if (form.value.auth_type === 'bearer') {
        form.value.auth_config = { token: authConfig.value.token }
      } else if (form.value.auth_type === 'basic') {
        form.value.auth_config = {
          username: authConfig.value.username,
          password: authConfig.value.password
        }
      }
    }
    
    // 确保参数化数据已解析
    parseParameterizedData()
    
    // 构建提交数据，将 project 转换为 project_id
    const submitData = {
      ...form.value,
      project_id: form.value.project,
      project: undefined  // 删除 project 字段，使用 project_id
    }
    delete submitData.project
    
    if (form.value.id) {
      await updateAPI(form.value.id, submitData)
      ElMessage.success('更新成功')
    } else {
      await createAPI(submitData)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    await loadAPIs()
  } catch (error) {
    console.error('提交失败:', error)
    ElMessage.error(error.response?.data?.detail || error.response?.data?.error || '操作失败')
  } finally {
    submitting.value = false
  }
}

const parseParameterizedData = () => {
  try {
    if (!parameterizedDataText.value.trim()) {
      form.value.parameterized_data = []
      return
    }
    const parsed = JSON.parse(parameterizedDataText.value)
    if (Array.isArray(parsed)) {
      form.value.parameterized_data = parsed
    } else {
      ElMessage.warning('参数化数据必须是JSON数组格式')
      parameterizedDataText.value = '[]'
      form.value.parameterized_data = []
    }
  } catch (error) {
    ElMessage.warning('参数化数据格式错误，请检查JSON格式')
  }
}

const handleDialogClose = () => {
  formRef.value?.resetFields()
  paramsText.value = '{}'
  headersText.value = '{}'
  bodyText.value = '{}'
  parameterizedDataText.value = '[]'
  authConfig.value = { token: '', username: '', password: '' }
  activeTab.value = 'basic'
}

const executeResultDialog = ref(false)
const executeResult = ref(null)

const handleExecute = async (row) => {
  try {
    row.executing = true
    const result = await executeAPI(row.id)
    
    // 检查是否是参数化结果
    if (result.parameterized) {
      executeResult.value = result
      executeResultDialog.value = true
      ElMessage.success(`参数化执行完成：${result.passed}通过，${result.failed}失败`)
    } else {
      executeResult.value = result
      executeResultDialog.value = true
      ElMessage.success('执行成功')
    }
  } catch (error) {
    console.error('执行失败:', error)
    ElMessage.error(error.response?.data?.detail || '执行失败')
  } finally {
    row.executing = false
  }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(`确定要删除接口 "${row.name}" 吗？`, '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    await deleteAPI(row.id)
    ElMessage.success('删除成功')
    await loadAPIs()
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
  loadAPIs()
}

const handlePageChange = (page) => {
  pagination.value.page = page
  loadAPIs()
}

const getMethodTagType = (method) => {
  const types = {
    POST: 'success',
    GET: 'primary',
    PUT: 'warning',
    PATCH: 'warning',
    DELETE: 'danger'
  }
  return types[method] || ''
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

const viewResultDetail = (row) => {
  // 临时显示单个结果的详情
  executeResult.value = row
  executeResult.value.parameterized = false
}

onMounted(() => {
  loadAPIs()
  loadProjects()
})
</script>

<style scoped>
.apis-container {
  padding: 24px;
  background-color: #f5f7fa;
  min-height: calc(100vh - 60px);
}

.apis-header {
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

.endpoint-code {
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
