<template>
  <div class="dashboard-container">
    <!-- 标签页切换 -->
    <el-tabs v-model="activeTab" class="dashboard-tabs">
      <el-tab-pane label="接口测试仪表盘" name="api">
        <ApiDashboard />
      </el-tab-pane>
      <el-tab-pane label="性能测试仪表盘" name="performance">
        <PerformanceDashboard />
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import ApiDashboard from './dashboard/ApiDashboard.vue'
import PerformanceDashboard from './performance/PerformanceDashboard.vue'

const activeTab = ref('api')
</script>

<style scoped>
.dashboard-container {
  padding: 24px;
  background-color: #f5f7fa;
  min-height: calc(100vh - 60px);
}

.dashboard-tabs {
  background: white;
  border-radius: 8px;
  padding: 16px;
}

:deep(.el-tabs__header) {
  margin-bottom: 24px;
}

:deep(.el-tabs__item) {
  font-size: 16px;
  font-weight: 500;
}
</style>
