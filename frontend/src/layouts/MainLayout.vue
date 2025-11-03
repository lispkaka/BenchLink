<template>
  <el-container>
    <el-aside width="200px">
      <!-- 平台标题 -->
      <div class="platform-title">
        <h2>BenchLink 平台</h2>
      </div>
      <el-menu
        :default-active="activeMenu"
        router
        background-color="#545c64"
        text-color="#fff"
        active-text-color="#ffd04b"
      >
        <el-menu-item index="/dashboard">
          <el-icon><DataBoard /></el-icon>
          <span>仪表盘</span>
        </el-menu-item>
        <el-menu-item index="/projects">
          <el-icon><Folder /></el-icon>
          <span>项目</span>
        </el-menu-item>
        <el-menu-item index="/apis">
          <el-icon><Link /></el-icon>
          <span>接口</span>
        </el-menu-item>
        <el-menu-item index="/testcases">
          <el-icon><Document /></el-icon>
          <span>测试用例</span>
        </el-menu-item>
        <el-menu-item index="/testsuites">
          <el-icon><Collection /></el-icon>
          <span>测试套件</span>
        </el-menu-item>
        <el-menu-item index="/executions">
          <el-icon><VideoPlay /></el-icon>
          <span>执行记录</span>
        </el-menu-item>
        <el-menu-item index="/scheduler">
          <el-icon><Clock /></el-icon>
          <span>定时任务</span>
        </el-menu-item>
        <el-sub-menu index="/config">
          <template #title>
            <el-icon><Setting /></el-icon>
            <span>配置管理</span>
          </template>
          <el-menu-item index="/environments">
            <span>环境配置</span>
          </el-menu-item>
          <el-menu-item index="/global-tokens">
            <span>全局 Token</span>
          </el-menu-item>
        </el-sub-menu>
        <el-menu-item index="/settings">
          <el-icon><User /></el-icon>
          <span>设置</span>
        </el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header>
        <div class="header-content">
          <el-button type="danger" @click="handleLogout">退出登录</el-button>
        </div>
      </el-header>
      <el-main>
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '../store'
import { DataBoard, Folder, Link, Document, Collection, VideoPlay, Clock, Setting, User } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

// 计算激活的菜单项（支持子菜单）
const activeMenu = computed(() => {
  // Element Plus 菜单组件的 default-active 应该设置为当前路由路径
  // 对于子菜单项，直接使用子菜单项的路径即可
  return route.path
})

const handleLogout = () => {
  userStore.logout()
  router.push('/login')
}
</script>

<style scoped>
.el-container {
  height: 100vh;
}

.el-aside {
  background-color: #545c64;
}

.platform-title {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #545c64;
  border-bottom: 1px solid #434a50;
  padding: 0;
  margin: 0;
  width: 100%;
}

.platform-title h2 {
  color: #fff;
  font-size: 18px;
  font-weight: 600;
  margin: 0;
  padding: 0 20px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  width: 100%;
  text-align: center;
}

/* 确保菜单与标题对齐 */
.el-menu {
  border-right: none;
}

/* 覆盖 Element Plus 菜单的默认样式，确保右侧对齐 */
:deep(.el-menu) {
  border-right: none;
}

/* 一级菜单项样式 */
:deep(.el-menu-item),
:deep(.el-sub-menu__title) {
  padding-left: 20px !important;
}

/* 子菜单容器样式 */
:deep(.el-sub-menu .el-menu) {
  background-color: transparent;
}

/* 确保图标和文字对齐 */
:deep(.el-menu-item),
:deep(.el-sub-menu__title) {
  display: flex;
  align-items: center;
}

/* 子菜单项样式 - 与一级菜单文字对齐 */
/* Element Plus 菜单组件中，一级菜单项的总 padding-left 是 20px */
/* 但图标区域（包括图标和间距）通常是固定的，约 40px */
/* 为了精确对齐文字，子菜单的 padding-left 应该等于一级菜单的文字起始位置 */
/* 计算：20px(一级菜单padding) + 图标宽度(约16-20px) + 图标与文字间距(约8px) ≈ 44-48px */
/* 使用 44px 可以获得较好的对齐效果 */
:deep(.el-menu--inline .el-menu-item) {
  padding-left: 44px !important;
  display: flex;
  align-items: center;
  /* 移除子菜单的默认缩进 */
  min-width: 0;
}

.el-header {
  background-color: #fff;
  border-bottom: 1px solid #e4e7ed;
}

.header-content {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  height: 100%;
}

.el-main {
  background-color: #f5f7fa;
  padding: 20px;
}
</style>



