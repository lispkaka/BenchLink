<template>
  <div class="environments-container">
    <!-- 顶部导航栏 -->
    <header class="environments-header">
      <div class="header-left">
        <h1 class="title">环境配置</h1>
        <p class="subtitle">管理不同环境的配置（基础URL、请求头、变量、钩子函数等）</p>
      </div>

      <div class="header-right">
        <el-select
          v-model="projectFilter"
          style="width: 200px"
          placeholder="筛选项目"
          clearable
          @change="loadEnvironments"
        >
          <el-option
            v-for="project in projects"
            :key="project.id"
            :label="project.name"
            :value="project.id"
          />
        </el-select>
        <el-button type="primary" @click="handleCreate">
          <el-icon><Plus /></el-icon>
          新建配置
        </el-button>
      </div>
    </header>

    <!-- 配置列表 -->
    <el-card class="table-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <span class="card-title">配置列表</span>
          <span class="card-subtitle">共 {{ environments.length }} 个配置</span>
        </div>
      </template>

      <el-table
        :data="environments"
        stripe
        style="width: 100%"
        v-loading="loading"
        empty-text="暂无配置"
      >
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="配置名称" min-width="150" show-overflow-tooltip />
        <el-table-column prop="project.name" label="所属项目" width="120" />
        <el-table-column label="基础URL" min-width="250" show-overflow-tooltip>
          <template #default="{ row }">
            <code class="url-code">{{ row.base_url }}</code>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
              {{ row.is_active ? '激活' : '停用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="handleEdit(row)">
              编辑
            </el-button>
            <el-button type="danger" link size="small" @click="handleDelete(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 新建/编辑对话框 -->
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
            label-width="120px"
            style="margin-top: 20px"
          >
            <el-form-item label="配置名称" prop="name">
              <el-input v-model="form.name" placeholder="请输入配置名称，如：测试环境、生产环境" />
            </el-form-item>
            <el-form-item label="所属项目" prop="project_id">
              <el-select
                v-model="form.project_id"
                placeholder="请选择项目"
                style="width: 100%"
              >
                <el-option
                  v-for="project in projects"
                  :key="project.id"
                  :label="project.name"
                  :value="project.id"
                />
              </el-select>
            </el-form-item>
            <el-form-item label="基础URL" prop="base_url">
              <el-input
                v-model="form.base_url"
                placeholder="例如：https://api.example.com 或 http://localhost:8080"
              />
              <div style="font-size: 12px; color: #909399; margin-top: 5px">
                提示：接口路径会自动拼接到此URL后，如接口路径为 /api/users，完整URL为
                {{ form.base_url }}/api/users
              </div>
            </el-form-item>
            <el-form-item label="配置描述">
              <el-input
                v-model="form.description"
                type="textarea"
                :rows="3"
                placeholder="请输入配置描述"
              />
            </el-form-item>
            <el-form-item label="状态">
              <el-switch v-model="form.is_active" />
              <span style="margin-left: 10px; color: #909399">
                {{ form.is_active ? '激活' : '停用' }}
              </span>
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <!-- 公共请求头 -->
        <el-tab-pane label="公共请求头" name="headers">
          <div style="margin-top: 20px">
            <el-alert
              title="公共请求头说明"
              type="info"
              :closable="false"
              show-icon
              style="margin-bottom: 16px"
            >
              <template #default>
                <div style="font-size: 12px">
                  配置的请求头会在该环境下的所有接口请求中自动添加。例如：Content-Type、Authorization等
                </div>
              </template>
            </el-alert>
            <div style="margin-bottom: 16px">
              <el-button type="primary" size="small" @click="addHeader">
                <el-icon><Plus /></el-icon>
                添加请求头
              </el-button>
            </div>
            <el-table :data="form.headers_array || []" border style="width: 100%">
              <el-table-column label="键" min-width="200">
                <template #default="{ row, $index }">
                  <el-input v-model="row.key" size="small" placeholder="请求头名称" />
                </template>
              </el-table-column>
              <el-table-column label="值" min-width="300">
                <template #default="{ row, $index }">
                  <el-input
                    v-model="row.value"
                    size="small"
                    placeholder="请求头值，支持变量 ${variable}"
                  />
                </template>
              </el-table-column>
              <el-table-column label="操作" width="100">
                <template #default="{ $index }">
                  <el-button
                    type="danger"
                    size="small"
                    link
                    @click="removeHeader($index)"
                  >
                    删除
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-tab-pane>

        <!-- 局部变量 -->
        <el-tab-pane label="局部变量" name="variables">
          <div style="margin-top: 20px">
            <el-alert
              title="局部变量说明"
              type="info"
              :closable="false"
              show-icon
              style="margin-bottom: 16px"
            >
              <template #default>
                <div style="font-size: 12px">
                  环境级别的变量，可以在该环境下的所有测试用例中使用，通过 ${变量名} 引用
                </div>
              </template>
            </el-alert>
            <div style="margin-bottom: 16px">
              <el-button type="primary" size="small" @click="addVariable">
                <el-icon><Plus /></el-icon>
                添加变量
              </el-button>
            </div>
            <el-table :data="form.variables_array || []" border style="width: 100%">
              <el-table-column label="变量名" min-width="200">
                <template #default="{ row, $index }">
                  <el-input v-model="row.key" size="small" placeholder="变量名称" />
                </template>
              </el-table-column>
              <el-table-column label="变量值" min-width="300">
                <template #default="{ row, $index }">
                  <el-input v-model="row.value" size="small" placeholder="变量值" />
                </template>
              </el-table-column>
              <el-table-column label="操作" width="100">
                <template #default="{ $index }">
                  <el-button
                    type="danger"
                    size="small"
                    link
                    @click="removeVariable($index)"
                  >
                    删除
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-tab-pane>

        <!-- 前置钩子 -->
        <el-tab-pane label="前置钩子" name="pre_hook">
          <div style="margin-top: 20px">
            <el-alert
              title="前置钩子说明"
              type="info"
              :closable="false"
              show-icon
              style="margin-bottom: 16px"
            >
              <template #default>
                <div style="font-size: 12px; line-height: 1.6">
                  <p>前置钩子在每个测试用例执行前运行，可以设置全局变量、初始化等。</p>
                  <p><strong>可用函数：</strong> set_variable(name, value), get_variable(name), print(...)</p>
                  <p><strong>可用对象：</strong> variables, testcase, api, environment</p>
                </div>
              </template>
            </el-alert>
            <el-input
              v-model="form.pre_hook"
              type="textarea"
              :rows="15"
              placeholder="请输入前置钩子函数（Python代码）&#10;例如：&#10;# 全局初始化&#10;set_variable('env', 'test')&#10;set_variable('timestamp', 1699000000)"
              style="font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace; font-size: 13px"
            />
          </div>
        </el-tab-pane>

        <!-- 后置钩子 -->
        <el-tab-pane label="后置钩子" name="post_hook">
          <div style="margin-top: 20px">
            <el-alert
              title="后置钩子说明"
              type="info"
              :closable="false"
              show-icon
              style="margin-bottom: 16px"
            >
              <template #default>
                <div style="font-size: 12px; line-height: 1.6">
                  <p>后置钩子在每个测试用例执行后运行，可以统一处理响应、提取数据等。</p>
                  <p><strong>可用函数：</strong> set_variable(name, value), get_variable(name), get_json_value(path), print(...)</p>
                  <p><strong>可用对象：</strong> status_code, headers, body, json, time, response, variables</p>
                </div>
              </template>
            </el-alert>
            <el-input
              v-model="form.post_hook"
              type="textarea"
              :rows="15"
              placeholder="请输入后置钩子函数（Python代码）&#10;例如：&#10;# 统一处理响应&#10;if json and json.get('code') != 0:&#10;    print(f'请求失败: {json.get(&quot;message&quot;)}')"
              style="font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace; font-size: 13px"
            />
          </div>
        </el-tab-pane>

        <!-- 参数化内容 -->
        <el-tab-pane label="参数化内容" name="parameterized">
          <div style="margin-top: 20px">
            <el-alert
              title="参数化内容说明"
              type="info"
              :closable="false"
              show-icon
              style="margin-bottom: 16px"
            >
              <template #default>
                <div style="font-size: 12px">
                  参数化数据列表，用于批量测试。每个元素是一个对象，包含多个变量。
                </div>
              </template>
            </el-alert>
            <div style="margin-bottom: 16px">
              <el-button type="primary" size="small" @click="addParameterizedRow">
                <el-icon><Plus /></el-icon>
                添加参数组
              </el-button>
            </div>
            <el-table :data="form.parameterized_data || []" border style="width: 100%">
              <el-table-column
                v-for="(header, index) in parameterizedHeaders"
                :key="index"
                :label="header"
                min-width="150"
              >
                <template #default="{ row }">
                  <el-input v-model="row[header]" size="small" />
                </template>
              </el-table-column>
              <el-table-column label="操作" width="100" fixed="right">
                <template #default="{ $index }">
                  <el-button
                    type="danger"
                    size="small"
                    link
                    @click="removeParameterizedRow($index)"
                  >
                    删除
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
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
import { Plus } from '@element-plus/icons-vue'
import {
  getEnvironments,
  createEnvironment,
  updateEnvironment,
  deleteEnvironment
} from '../api/environments'
import { getProjects } from '../api/projects'
import api from '../api/index'

// 数据定义
const loading = ref(false)
const projectFilter = ref(null)
const environments = ref([])
const projects = ref([])
const submitting = ref(false)
const dialogVisible = ref(false)
const dialogTitle = ref('新建配置')
const formRef = ref(null)
const activeTab = ref('basic')

const form = ref({
  id: null,
  name: '',
  project_id: null,
  base_url: '',
  description: '',
  headers: {},
  variables: {},
  pre_hook: '',
  post_hook: '',
  parameterized_data: [],
  is_active: true,
  headers_array: [],
  variables_array: []
})

const formRules = {
  name: [{ required: true, message: '请输入配置名称', trigger: 'blur' }],
  project_id: [{ required: true, message: '请选择所属项目', trigger: 'change' }],
  base_url: [{ required: true, message: '请输入基础URL', trigger: 'blur' }]
}

// 计算属性
const filteredEnvironments = computed(() => {
  if (projectFilter.value) {
    return environments.value.filter((e) => e.project?.id === projectFilter.value)
  }
  return environments.value
})

const parameterizedHeaders = computed(() => {
  if (!form.value.parameterized_data || form.value.parameterized_data.length === 0) {
    return []
  }
  return Object.keys(form.value.parameterized_data[0] || {})
})

// 方法
const loadEnvironments = async () => {
  loading.value = true
  try {
    const params = projectFilter.value ? { project_id: projectFilter.value } : {}
    const response = await getEnvironments(params)
    // 响应拦截器已经提取了response.data，所以response就是数据本身
    if (response.results) {
      // 分页响应格式 {count, next, previous, results: [...]}
      environments.value = response.results
    } else if (Array.isArray(response)) {
      // 数组格式
      environments.value = response
    } else {
      environments.value = []
    }
  } catch (error) {
    console.error('加载配置失败:', error)
    const errorMsg = error.response?.data?.detail || error.response?.data?.error || error.message || '加载配置失败'
    ElMessage.error(errorMsg)
  } finally {
    loading.value = false
  }
}

const loadProjects = async () => {
  try {
    const response = await getProjects()
    // 响应拦截器已经提取了response.data
    if (response.results) {
      projects.value = response.results
    } else if (Array.isArray(response)) {
      projects.value = response
    } else {
      projects.value = []
    }
  } catch (error) {
    console.error('加载项目失败:', error)
  }
}

const handleCreate = () => {
  dialogTitle.value = '新建配置'
  form.value = {
    id: null,
    name: '',
    project_id: null,
    base_url: '',
    description: '',
    headers: {},
    variables: {},
    pre_hook: '',
    post_hook: '',
    parameterized_data: [],
    is_active: true,
    headers_array: [],
    variables_array: []
  }
  activeTab.value = 'basic'
  dialogVisible.value = true
}

const handleEdit = (row) => {
  dialogTitle.value = '编辑配置'
  form.value = {
    id: row.id,
    name: row.name,
    project_id: row.project?.id || row.project,
    base_url: row.base_url,
    description: row.description || '',
    headers: row.headers || {},
    variables: row.variables || {},
    pre_hook: row.pre_hook || '',
    post_hook: row.post_hook || '',
    parameterized_data: row.parameterized_data || [],
    is_active: row.is_active !== false,
    headers_array: Object.keys(row.headers || {}).map((key) => ({
      key,
      value: row.headers[key]
    })),
    variables_array: Object.keys(row.variables || {}).map((key) => ({
      key,
      value: row.variables[key]
    }))
  }
  activeTab.value = 'basic'
  dialogVisible.value = true
}

const handleSubmit = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (valid) {
      submitting.value = true
      try {
        // 转换数组格式为对象格式
        const headers = {}
        form.value.headers_array.forEach((item) => {
          if (item.key) {
            headers[item.key] = item.value || ''
          }
        })

        const variables = {}
        form.value.variables_array.forEach((item) => {
          if (item.key) {
            variables[item.key] = item.value || ''
          }
        })

        const submitData = {
          ...form.value,
          headers,
          variables,
          headers_array: undefined,
          variables_array: undefined
        }
        delete submitData.headers_array
        delete submitData.variables_array

        if (form.value.id) {
          await updateEnvironment(form.value.id, submitData)
          ElMessage.success('更新成功')
        } else {
          await createEnvironment(submitData)
          ElMessage.success('创建成功')
        }
        dialogVisible.value = false
        await loadEnvironments()
      } catch (error) {
        console.error('提交失败:', error)
        ElMessage.error(error.response?.data?.detail || error.response?.data?.error || '操作失败')
      } finally {
        submitting.value = false
      }
    }
  })
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(`确定要删除配置 "${row.name}" 吗？`, '确认删除', {
      type: 'warning'
    })
    await deleteEnvironment(row.id)
    ElMessage.success('删除成功')
    await loadEnvironments()
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

const addHeader = () => {
  if (!form.value.headers_array) {
    form.value.headers_array = []
  }
  form.value.headers_array.push({ key: '', value: '' })
}

const removeHeader = (index) => {
  form.value.headers_array.splice(index, 1)
}

const addVariable = () => {
  if (!form.value.variables_array) {
    form.value.variables_array = []
  }
  form.value.variables_array.push({ key: '', value: '' })
}

const removeVariable = (index) => {
  form.value.variables_array.splice(index, 1)
}

const addParameterizedRow = () => {
  if (!form.value.parameterized_data) {
    form.value.parameterized_data = []
  }
  const newRow = {}
  if (form.value.parameterized_data.length > 0) {
    Object.keys(form.value.parameterized_data[0]).forEach((key) => {
      newRow[key] = ''
    })
  } else {
    newRow['key1'] = ''
    newRow['key2'] = ''
  }
  form.value.parameterized_data.push(newRow)
}

const removeParameterizedRow = (index) => {
  form.value.parameterized_data.splice(index, 1)
}

// 生命周期
onMounted(() => {
  loadProjects()
  loadEnvironments()
})
</script>

<style scoped>
.environments-container {
  padding: 24px;
}

.environments-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.header-left .title {
  font-size: 24px;
  font-weight: 600;
  margin: 0 0 8px 0;
  color: #303133;
}

.header-left .subtitle {
  font-size: 14px;
  color: #909399;
  margin: 0;
}

.header-right {
  display: flex;
  gap: 12px;
}

.table-card {
  margin-top: 16px;
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
  font-weight: 600;
  font-size: 16px;
}

.card-subtitle {
  color: #909399;
  font-size: 14px;
}

.url-code {
  background: #f5f7fa;
  padding: 2px 6px;
  border-radius: 3px;
  font-size: 12px;
  color: #606266;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  display: inline-block;
  max-width: 100%;
}

</style>




