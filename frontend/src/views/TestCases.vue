<template>
  <div class="testcases-container">
    <!-- 顶部导航栏 -->
    <header class="testcases-header">
      <div class="header-left">
        <h1 class="title">接口测试用例</h1>
        <p class="subtitle">集中管理与执行测试用例</p>
      </div>

      <div class="header-right">
        <el-select v-model="statusFilter" style="width: 120px" placeholder="状态筛选">
          <el-option label="全部" value="全部" />
          <el-option label="通过" value="通过" />
          <el-option label="失败" value="失败" />
          <el-option label="未执行" value="未执行" />
        </el-select>
        <el-input
          v-model="searchQuery"
          placeholder="搜索用例名称"
          style="width: 200px"
          clearable
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <el-button type="primary" @click="handleCreate">
          <el-icon><Plus /></el-icon>
          新建用例
        </el-button>
      </div>
    </header>

    <!-- 统计信息卡片 -->
    <section class="stats-grid">
      <transition-group name="fade-up" tag="div" class="stats-cards">
        <el-card :key="'total'" class="stat-card" shadow="hover">
          <div class="stat-label">用例总数</div>
          <div class="stat-value">{{ stats.total }}</div>
        </el-card>

        <el-card :key="'today'" class="stat-card" shadow="hover">
          <div class="stat-label">今日执行</div>
          <div class="stat-value text-primary">{{ stats.todayExecuted }}</div>
        </el-card>

        <el-card :key="'rate'" class="stat-card" shadow="hover">
          <div class="stat-label">通过率</div>
          <div class="stat-value text-success">{{ stats.passRate }}%</div>
        </el-card>

        <el-card :key="'duration'" class="stat-card" shadow="hover">
          <div class="stat-label">平均耗时</div>
          <div class="stat-value text-info">{{ stats.avgDuration }}</div>
        </el-card>
      </transition-group>
    </section>

    <!-- 测试用例列表 -->
    <el-card class="table-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <span class="card-title">测试用例列表</span>
          <span class="card-subtitle">共 {{ total }} 条</span>
        </div>
      </template>

      <el-table
        :data="testCases"
        stripe
        style="width: 100%"
        v-loading="loading"
        empty-text="暂无测试用例"
      >
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="名称" min-width="180" show-overflow-tooltip />
        <el-table-column label="方法" width="100">
          <template #default="{ row }">
            <el-tag :type="getMethodTagType(row.api?.method)" size="small">
              {{ row.api?.method || '-' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="接口路径" min-width="250" show-overflow-tooltip>
          <template #default="{ row }">
            <code class="endpoint-code">{{ row.api?.url || '-' }}</code>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="120">
          <template #default="{ row }">
            <el-tag :type="getStatusTagType(row.status)" size="small">
              {{ row.status || '未执行' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="duration" label="耗时" width="100">
          <template #default="{ row }">
            <span v-if="row.duration">{{ row.duration }}</span>
            <span v-else class="text-gray">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="updated_at" label="更新时间" width="180">
          <template #default="{ row }">
            <span class="text-gray">{{ formatDate(row.updated_at) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button
              type="primary"
              size="small"
              link
              @click="handleEdit(row)"
            >
              编辑
            </el-button>
            <el-button
              type="success"
              size="small"
              link
              @click="handleExecute(row)"
              :loading="row.executing"
            >
              执行
            </el-button>
            <el-button
              type="danger"
              size="small"
              link
              @click="handleDelete(row)"
            >
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

    <!-- 页脚说明 -->
    <footer class="testcases-footer">
      注：此页面展示接口测试用例功能，可扩展断言、Mock 数据、报告查看等能力。
    </footer>

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
          <el-form
            ref="formRef"
            :model="form"
            :rules="formRules"
            label-width="100px"
            style="margin-top: 20px"
          >
            <el-form-item label="用例名称" prop="name">
              <el-input v-model="form.name" placeholder="请输入用例名称" />
            </el-form-item>
            <el-form-item label="所属项目" prop="project">
              <el-select
                v-model="form.project"
                placeholder="请选择项目"
                style="width: 100%"
                @change="handleProjectChange"
              >
                <el-option
                  v-for="project in projects"
                  :key="project.id"
                  :label="project.name"
                  :value="project.id"
                />
              </el-select>
            </el-form-item>
            <el-form-item label="关联接口" prop="api">
              <el-select
                v-model="form.api"
                placeholder="请先选择项目，再选择接口"
                style="width: 100%"
                filterable
                :disabled="!form.project"
              >
                <el-option
                  v-for="apiItem in apis"
                  :key="apiItem.id"
                  :label="`[${apiItem.method}] ${apiItem.name}`"
                  :value="apiItem.id"
                >
                  <div style="display: flex; justify-content: space-between;">
                    <span><el-tag size="small" :type="getMethodTagType(apiItem.method)">{{ apiItem.method }}</el-tag> {{ apiItem.name }}</span>
                    <span style="color: #8492a6; font-size: 12px;">{{ apiItem.url }}</span>
                  </div>
                </el-option>
              </el-select>
            </el-form-item>
            <el-form-item label="测试环境" prop="environment">
              <el-select
                v-model="form.environment"
                placeholder="请选择环境"
                style="width: 100%"
                clearable
              >
                <el-option
                  v-for="env in environments"
                  :key="env.id"
                  :label="env.name"
                  :value="env.id"
                />
              </el-select>
            </el-form-item>
            <el-form-item label="用例描述" prop="description">
              <el-input
                v-model="form.description"
                type="textarea"
                :rows="3"
                placeholder="请输入用例描述"
              />
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <!-- 前后置脚本 -->
        <el-tab-pane label="前后置脚本" name="scripts">
          <div style="margin-top: 20px">
            <el-tabs type="border-card">
              <!-- 前置脚本 -->
              <el-tab-pane label="前置脚本" name="pre_script">
                <div style="margin-bottom: 10px">
                  <el-alert
                    title="前置脚本说明"
                    type="info"
                    :closable="false"
                    show-icon
                  >
                    <template #default>
                      <div style="font-size: 12px; line-height: 1.6">
                        <p>前置脚本在发送请求前执行，可以设置变量供请求使用。</p>
                        <p><strong>可用函数：</strong></p>
                        <ul style="margin: 8px 0; padding-left: 20px">
                          <li><code>set_variable(name, value)</code> - 设置变量</li>
                          <li><code>get_variable(name)</code> - 获取变量</li>
                          <li><code>print(...)</code> - 打印日志</li>
                        </ul>
                        <p><strong>可用对象：</strong> variables, testcase, api, environment</p>
                      </div>
                    </template>
                  </el-alert>
                </div>
                <el-input
                  v-model="form.pre_script"
                  type="textarea"
                  :rows="12"
                  placeholder="请输入前置脚本（Python代码）&#10;例如：&#10;set_variable('user_id', 123)&#10;set_variable('timestamp', 1699000000)"
                  style="font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace; font-size: 13px"
                />
              </el-tab-pane>

              <!-- 后置脚本 -->
              <el-tab-pane label="后置脚本" name="post_script">
                <div style="margin-bottom: 10px">
                  <el-alert
                    title="后置脚本说明"
                    type="info"
                    :closable="false"
                    show-icon
                  >
                    <template #default>
                      <div style="font-size: 12px; line-height: 1.6">
                        <p>后置脚本在收到响应后执行，可以从响应中提取数据。</p>
                        <p><strong>可用函数：</strong></p>
                        <ul style="margin: 8px 0; padding-left: 20px">
                          <li><code>set_variable(name, value)</code> - 设置变量</li>
                          <li><code>get_variable(name)</code> - 获取变量</li>
                          <li><code>get_json_value(path)</code> - 从JSON中提取值</li>
                          <li><code>print(...)</code> - 打印日志</li>
                        </ul>
                        <p><strong>可用对象：</strong></p>
                        <ul style="margin: 8px 0; padding-left: 20px">
                          <li><code>status_code</code> - 响应状态码</li>
                          <li><code>headers</code> - 响应头</li>
                          <li><code>body</code> - 响应体文本</li>
                          <li><code>json</code> - 响应JSON对象（如果是JSON格式）</li>
                          <li><code>time</code> - 响应时间（毫秒）</li>
                          <li><code>response</code> - requests响应对象</li>
                          <li><code>variables</code> - 变量字典</li>
                        </ul>
                      </div>
                    </template>
                  </el-alert>
                </div>
                <el-input
                  v-model="form.post_script"
                  type="textarea"
                  :rows="12"
                  placeholder="请输入后置脚本（Python代码）&#10;例如：&#10;if json:&#10;    set_variable('user_id', json.get('userId'))&#10;    set_variable('post_id', json.get('id'))&#10;set_variable('status_code', status_code)"
                  style="font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace; font-size: 13px"
                />
              </el-tab-pane>
            </el-tabs>
          </div>
        </el-tab-pane>

        <!-- 参数覆盖（方案A） -->
        <el-tab-pane label="参数覆盖" name="override">
          <div style="margin-top: 20px">
            <el-alert
              title="参数覆盖说明"
              type="info"
              :closable="false"
              show-icon
              style="margin-bottom: 16px"
            >
              <template #default>
                <div style="font-size: 12px; line-height: 1.6">
                  <p>参数覆盖用于在用例层面覆盖接口定义的参数。优先级：用例覆盖 > 接口定义</p>
                  <p>💡 支持变量替换，使用 ${variable} 格式</p>
                  <p>💡 留空则使用接口定义的原始值</p>
                </div>
              </template>
            </el-alert>

            <el-form :model="form" label-width="140px">
              <el-form-item label="URL覆盖">
                <el-input
                  v-model="form.url_override"
                  placeholder="留空则使用接口定义的URL，支持变量如：/posts/${post_id}"
                  clearable
                />
              </el-form-item>

              <el-form-item label="请求头覆盖">
                <el-input
                  v-model="headersOverrideText"
                  type="textarea"
                  :rows="6"
                  placeholder='输入JSON格式的请求头，例如：&#10;{&#10;  "Authorization": "Bearer ${token}"&#10;}'
                  style="font-family: monospace; font-size: 13px"
                  @blur="parseHeadersOverride"
                />
              </el-form-item>

              <el-form-item label="查询参数覆盖">
                <el-input
                  v-model="paramsOverrideText"
                  type="textarea"
                  :rows="6"
                  placeholder='输入JSON格式的查询参数，例如：&#10;{&#10;  "page": "${page}",&#10;  "size": 10&#10;}'
                  style="font-family: monospace; font-size: 13px"
                  @blur="parseParamsOverride"
                />
              </el-form-item>

              <el-form-item label="请求体覆盖">
                <el-input
                  v-model="bodyOverrideText"
                  type="textarea"
                  :rows="8"
                  placeholder='输入JSON格式的请求体，例如：&#10;{&#10;  "title": "测试标题",&#10;  "userId": "${userId}"&#10;}'
                  style="font-family: monospace; font-size: 13px"
                  @blur="parseBodyOverride"
                />
              </el-form-item>
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
                  💡 启用后，用例将使用参数化数据循环执行多次（每次执行都会创建独立的执行记录）
                </div>
              </el-form-item>

              <el-form-item v-if="form.parameterized_mode === 'enabled'" label="参数化数据">
                <el-input
                  v-model="parameterizedDataText"
                  type="textarea"
                  :rows="12"
                  placeholder='输入JSON数组格式的参数化数据，例如：&#10;[&#10;  {"username": "admin", "password": "admin123"},&#10;  {"username": "user1", "password": "password123"},&#10;  {"username": "test", "password": "test123"}&#10;]&#10;&#10;每个对象代表一组参数，会依次替换用例中的${变量名}（支持在URL覆盖、请求头、查询参数、请求体中使用变量）'
                  style="font-family: monospace; font-size: 13px"
                  @blur="parseParameterizedData"
                />
                <div style="margin-top: 8px; font-size: 12px; color: #909399">
                  💡 格式：JSON数组，每个元素是一个对象，对象的key对应用例中的变量名（如${username}），value为要替换的值<br/>
                  💡 参数化执行时，每次执行都会创建独立的执行记录，可以在"执行记录"页面查看每次执行的详情
                </div>
              </el-form-item>
            </el-form>
          </div>
        </el-tab-pane>

        <!-- 断言配置 -->
        <el-tab-pane label="断言配置" name="assertions">
          <div style="margin-top: 20px">
            <div style="margin-bottom: 16px">
              <el-button type="primary" size="small" @click="addAssertion">
                <el-icon><Plus /></el-icon>
                添加断言
              </el-button>
            </div>

            <!-- 断言列表 -->
            <el-table :data="form.assertions || []" border style="width: 100%">
              <el-table-column label="类型" width="120">
                <template #default="{ row }">
                  <el-select v-model="row.type" size="small" style="width: 100%">
                    <el-option label="状态码" value="status_code" />
                    <el-option label="响应时间" value="response_time" />
                    <el-option label="包含文本" value="contains" />
                    <el-option label="JSON路径" value="json_path" />
                    <el-option label="相等断言" value="equals" />
                  </el-select>
                </template>
              </el-table-column>
              <el-table-column label="描述/路径" min-width="200">
                <template #default="{ row, $index }">
                  <el-input
                    v-if="row.type === 'json_path' || row.type === 'equals'"
                    v-model="row.json_path"
                    size="small"
                    placeholder="JSON路径，如: data.user.id"
                  />
                  <el-input
                    v-else-if="row.type === 'manual'"
                    v-model="row.description"
                    size="small"
                    placeholder="断言描述"
                  />
                  <span v-else>{{ getAssertionLabel(row) }}</span>
                </template>
              </el-table-column>
              <el-table-column label="期望值" min-width="150">
                <template #default="{ row }">
                  <el-input
                    v-if="row.type === 'json_path'"
                    v-model="row.value"
                    size="small"
                    placeholder="期望值"
                  />
                  <el-input
                    v-else-if="row.type !== 'manual'"
                    v-model="row.expected"
                    size="small"
                    placeholder="期望值"
                  />
                  <span v-else class="text-gray">手动脚本</span>
                </template>
              </el-table-column>
              <el-table-column label="操作" width="100">
                <template #default="{ $index }">
                  <el-button
                    type="danger"
                    size="small"
                    link
                    @click="removeAssertion($index)"
                  >
                    删除
                  </el-button>
                </template>
              </el-table-column>
            </el-table>

            <!-- 手动断言脚本编辑器 -->
            <div
              v-for="(assertion, index) in manualAssertions"
              :key="index"
              style="margin-top: 16px; border: 1px solid #dcdfe6; border-radius: 4px; padding: 16px"
            >
              <div style="display: flex; justify-content: space-between; margin-bottom: 8px">
                <span style="font-weight: 600">手动断言脚本 #{{ index + 1 }}</span>
                <el-button
                  type="danger"
                  size="small"
                  link
                  @click="removeManualAssertion(index)"
                >
                  删除
                </el-button>
              </div>
              <el-input
                v-model="assertion.description"
                placeholder="断言描述（可选）"
                style="margin-bottom: 8px"
              />
              <el-input
                v-model="assertion.script"
                type="textarea"
                :rows="8"
                placeholder="输入Python断言脚本，可以使用以下变量和函数：&#10;- status_code: 响应状态码&#10;- headers: 响应头字典&#10;- body: 响应体文本&#10;- json: JSON响应（如果可用）&#10;- time: 响应时间（毫秒）&#10;- assert_equal(actual, expected, message): 相等断言&#10;- assert_contains(container, item, message): 包含断言&#10;- assert_true(condition, message): 真值断言&#10;&#10;示例：&#10;assert_equal(status_code, 200, '状态码应为200')&#10;assert_equal(json['code'], 0, '返回码应为0')&#10;assert_contains(body, 'success', '响应应包含success')"
                style="font-family: monospace"
              />
            </div>

            <div style="margin-top: 16px">
              <el-button type="primary" size="small" @click="addManualAssertion">
                <el-icon><Plus /></el-icon>
                添加手动断言脚本
              </el-button>
            </div>
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
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Plus } from '@element-plus/icons-vue'
import { getTestCases, createTestCase, updateTestCase, deleteTestCase, executeTestCase, getTestCaseStatistics } from '../api/testcases'
import api from '../api/index'

// 数据定义
const loading = ref(false)
const searchQuery = ref('')
const statusFilter = ref('全部')
const testCases = ref([])
const total = ref(0)
const submitting = ref(false)
const dialogVisible = ref(false)
const dialogTitle = ref('新建用例')
const formRef = ref(null)
const activeTab = ref('basic')
const manualAssertions = ref([])

const projects = ref([])
const apis = ref([])
const environments = ref([])

const pagination = ref({
  page: 1,
  pageSize: 20
})

const stats = ref({
  total: 0,
  todayExecuted: 0,
  passRate: 0,
  avgDuration: '-'
})

const headersOverrideText = ref('{}')
const paramsOverrideText = ref('{}')
const bodyOverrideText = ref('{}')
const parameterizedDataText = ref('[]')

const form = ref({
  id: null,
  name: '',
  project: null,
  api: null,
  environment: null,
  description: '',
  pre_script: '',
  post_script: '',
  assertions: [],
  // 方案A：参数覆盖字段
  url_override: '',
  headers_override: {},
  body_override: {},
  params_override: {},
  // 参数化功能
  parameterized_mode: 'disabled',
  parameterized_data: []
})

const formRules = {
  name: [{ required: true, message: '请输入用例名称', trigger: 'blur' }],
  project: [{ required: true, message: '请选择所属项目', trigger: 'change' }],
  api: [{ required: true, message: '请选择关联接口', trigger: 'change' }]
}

// 计算属性
const filteredTestCases = computed(() => {
  let filtered = testCases.value

  // 搜索过滤
  if (searchQuery.value) {
    filtered = filtered.filter((t) =>
      t.name.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
      t.id.toString().includes(searchQuery.value)
    )
  }

  // 状态过滤
  if (statusFilter.value !== '全部') {
    filtered = filtered.filter((t) => (t.status || '未执行') === statusFilter.value)
  }

  return filtered
})

// 方法
const loadTestCases = async () => {
  loading.value = true
  try {
    const response = await getTestCases({
      page: pagination.value.page,
      page_size: pagination.value.pageSize
    })
    
    // 根据API响应结构调整
    if (response.results) {
      testCases.value = response.results
      total.value = response.count || response.results.length
    } else if (Array.isArray(response)) {
      testCases.value = response
      total.value = response.length
    }

    // 计算统计数据
    calculateStats()
  } catch (error) {
    console.error('加载测试用例失败:', error)
    ElMessage.error('加载测试用例失败')
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

const loadApis = async (projectId = null) => {
  try {
    const params = {
      page_size: 10000  // 设置足够大的page_size以获取所有接口
    }
    
    // 加载所有接口（不限制项目），让用户可以选择任何接口
    // 这样可以处理接口未设置项目的情况
    const response = await api.get('/apis/apis/', { params })
    const allApis = Array.isArray(response) ? response : response.results || []
    
    // 如果选择了项目，优先显示该项目的接口，其他接口放在后面
    if (projectId) {
      const projectApis = allApis.filter(api => api.project?.id === projectId || api.project === projectId)
      const otherApis = allApis.filter(api => api.project?.id !== projectId && api.project !== projectId)
      apis.value = [...projectApis, ...otherApis]
      console.log(`已加载接口：项目接口 ${projectApis.length} 个，其他接口 ${otherApis.length} 个，合计 ${allApis.length} 个`)
    } else {
      apis.value = allApis
      console.log(`已加载所有接口：${apis.value.length} 个`)
    }
  } catch (error) {
    console.error('加载接口列表失败:', error)
    apis.value = []
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

const calculateStats = async () => {
  try {
    // 从后端API获取统计数据
    const statistics = await getTestCaseStatistics()
    stats.value = {
      total: statistics.total || testCases.value.length,
      todayExecuted: statistics.today_executed || 0,
      passRate: statistics.pass_rate || 0,
      avgDuration: statistics.avg_duration || '-'
    }
  } catch (error) {
    console.error('获取统计数据失败:', error)
    // 如果API调用失败，使用本地计算
    const total = testCases.value.length
    const passedCases = testCases.value.filter((t) => t.status === '通过')
    const passRate = total > 0 ? Math.round((passedCases.length / total) * 100) : 0

    stats.value = {
      total,
      todayExecuted: 0,
      passRate,
      avgDuration: '-'
    }
  }
}

// 项目改变时，重新加载该项目的接口
const handleProjectChange = (projectId) => {
  // 清空已选择的接口
  form.value.api = null
  // 加载该项目的接口
  if (projectId) {
    loadApis(projectId)
  } else {
    apis.value = []
  }
}

const handleCreate = () => {
  dialogTitle.value = '新建用例'
  form.value = {
    id: null,
    name: '',
    project: null,
    api: null,
    environment: null,
    description: '',
    pre_script: '',
    post_script: '',
    assertions: [],
    url_override: '',
    headers_override: {},
    body_override: {},
    params_override: {},
    parameterized_mode: 'disabled',
    parameterized_data: []
  }
  headersOverrideText.value = '{}'
  paramsOverrideText.value = '{}'
  bodyOverrideText.value = '{}'
  parameterizedDataText.value = '[]'
  manualAssertions.value = []
  activeTab.value = 'basic'
  dialogVisible.value = true
}

const handleEdit = (row) => {
  dialogTitle.value = '编辑用例'
  
  // 分离常规断言和手动断言
  const assertions = row.assertions || []
  const regularAssertions = assertions.filter(a => a.type !== 'manual' && a.type !== 'script')
  const manual = assertions.filter(a => a.type === 'manual' || a.type === 'script')
  
  form.value = {
    id: row.id,
    name: row.name,
    project: row.project?.id || row.project,
    api: row.api?.id || row.api,
    environment: row.environment?.id || row.environment,
    description: row.description || '',
    pre_script: row.pre_script || '',
    post_script: row.post_script || '',
    assertions: regularAssertions,
    url_override: row.url_override || '',
    headers_override: row.headers_override || {},
    body_override: row.body_override || {},
    params_override: row.params_override || {},
    parameterized_mode: row.parameterized_mode || 'disabled',
    parameterized_data: row.parameterized_data || []
  }
  
  // 加载该项目的接口列表
  if (form.value.project) {
    loadApis(form.value.project)
  }
  
  headersOverrideText.value = JSON.stringify(form.value.headers_override || {}, null, 2)
  paramsOverrideText.value = JSON.stringify(form.value.params_override || {}, null, 2)
  bodyOverrideText.value = JSON.stringify(form.value.body_override || {}, null, 2)
  parameterizedDataText.value = JSON.stringify(row.parameterized_data || [], null, 2)
  manualAssertions.value = manual.length > 0 ? manual : []
  activeTab.value = 'basic'
  dialogVisible.value = true
}

const parseHeadersOverride = () => {
  try {
    if (!headersOverrideText.value.trim()) {
      form.value.headers_override = {}
      return
    }
    form.value.headers_override = JSON.parse(headersOverrideText.value)
  } catch (error) {
    ElMessage.warning('请求头覆盖格式错误，请检查JSON格式')
  }
}

const parseParamsOverride = () => {
  try {
    if (!paramsOverrideText.value.trim()) {
      form.value.params_override = {}
      return
    }
    form.value.params_override = JSON.parse(paramsOverrideText.value)
  } catch (error) {
    ElMessage.warning('查询参数覆盖格式错误，请检查JSON格式')
  }
}

const parseBodyOverride = () => {
  try {
    if (!bodyOverrideText.value.trim()) {
      form.value.body_override = {}
      return
    }
    form.value.body_override = JSON.parse(bodyOverrideText.value)
  } catch (error) {
    ElMessage.warning('请求体覆盖格式错误，请检查JSON格式')
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

const handleSubmit = async () => {
  if (!formRef.value) return
  
  // 解析覆盖字段
  parseHeadersOverride()
  parseParamsOverride()
  parseBodyOverride()
  // 解析参数化数据
  parseParameterizedData()

  await formRef.value.validate(async (valid) => {
    if (valid) {
      submitting.value = true
      try {
        // 合并所有断言（常规断言 + 手动断言）
        const allAssertions = [
          ...(form.value.assertions || []),
          ...manualAssertions.value.map(a => ({
            type: 'manual',
            description: a.description || '',
            script: a.script || ''
          }))
        ]
        
        // 构建提交数据，转换字段名
        const submitData = {
          ...form.value,
          project_id: form.value.project,
          api_id: form.value.api,
          environment_id: form.value.environment || null,
          assertions: allAssertions,
          project: undefined,
          api: undefined,
          environment: undefined
        }
        delete submitData.project
        delete submitData.api
        delete submitData.environment
        
        if (form.value.id) {
          await updateTestCase(form.value.id, submitData)
          ElMessage.success('更新成功')
        } else {
          await createTestCase(submitData)
          ElMessage.success('创建成功')
        }
        dialogVisible.value = false
        await loadTestCases()
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
  manualAssertions.value = []
}

const addAssertion = () => {
  if (!form.value.assertions) {
    form.value.assertions = []
  }
  form.value.assertions.push({
    type: 'status_code',
    expected: '',
    json_path: '',
    value: '',
    description: ''
  })
}

const removeAssertion = (index) => {
  form.value.assertions.splice(index, 1)
}

const addManualAssertion = () => {
  manualAssertions.value.push({
    type: 'manual',
    description: '',
    script: ''
  })
}

const removeManualAssertion = (index) => {
  manualAssertions.value.splice(index, 1)
}

const getAssertionLabel = (assertion) => {
  const labels = {
    status_code: '状态码断言',
    response_time: '响应时间断言',
    contains: '包含文本断言',
    json_path: 'JSON路径断言',
    equals: '相等断言'
  }
  return labels[assertion.type] || assertion.type
}

const handleExecute = async (row) => {
  try {
    row.executing = true
    
    // 检查是否是参数化用例
    const parameterized_mode = row.parameterized_mode || 'disabled'
    const parameterized_data = row.parameterized_data || []
    
    // 构建请求数据
    const requestData = {}
    if (parameterized_mode === 'enabled' && parameterized_data && parameterized_data.length > 0) {
      requestData.parameterized_mode = 'enabled'
      requestData.parameterized_data = parameterized_data
    }
    
    const result = await executeTestCase(row.id, requestData)
    
    // 检查是否是参数化结果
    if (result.parameterized) {
      ElMessage.success(`参数化执行完成：${result.passed}通过，${result.failed}失败`)
      // TODO: 可以显示参数化结果对话框
    } else {
      if (result.status === 'failed') {
        ElMessage.error(result.error || '执行失败')
      } else {
        ElMessage.success('执行成功')
      }
    }
    
    // 重新加载测试用例列表和统计数据
    await loadTestCases()
    await calculateStats()
  } catch (error) {
    console.error('执行失败:', error)
    const errorMsg = error.response?.data?.error || error.response?.data?.detail || '执行失败'
    ElMessage.error(errorMsg)
  } finally {
    row.executing = false
  }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(`确定要删除用例 "${row.name}" 吗？`, '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    await deleteTestCase(row.id)
    ElMessage.success('删除成功')
    await loadTestCases()
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
  loadTestCases()
}

const handlePageChange = (page) => {
  pagination.value.page = page
  loadTestCases()
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

const getStatusTagType = (status) => {
  const types = {
    通过: 'success',
    失败: 'danger',
    未执行: 'info'
  }
  return types[status] || 'info'
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
  loadTestCases()
  loadProjects()
  loadApis()
  loadEnvironments()
})
</script>

<style scoped>
.testcases-container {
  padding: 24px;
  background-color: #f5f7fa;
  min-height: calc(100vh - 60px);
}

.testcases-header {
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

.testcases-footer {
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px solid #e4e7ed;
  font-size: 12px;
  color: #c0c4cc;
  text-align: center;
}

/* 动画效果 */
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
