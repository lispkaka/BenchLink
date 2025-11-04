<template>
  <router-view />
</template>

<script setup>
</script>

<style>
/* 全局样式重置 */
* {
  box-sizing: border-box;
}

html, body {
  margin: 0;
  padding: 0;
  width: 100%;
  height: 100%;
  overflow: hidden;
}

/* 浅色主题（默认） */
html.light,
body.light {
  color-scheme: light;
  background-color: #ffffff;
  color: #303133;
}

/* 深色主题 */
html.dark,
body.dark {
  color-scheme: dark;
  background-color: #1d1e1f;
  color: #e5eaf3;
}

html.dark .el-card {
  background-color: #2d2d2d;
  border-color: #404040;
}

html.dark .el-card__header {
  border-bottom-color: #404040;
}

html.dark .el-input__inner,
html.dark .el-textarea__inner {
  background-color: #2d2d2d;
  border-color: #404040;
  color: #e5eaf3;
}

html.dark .el-menu {
  background-color: #2d2d2d;
  border-color: #404040;
}

html.dark .el-menu-item {
  color: #e5eaf3;
}

html.dark .el-menu-item:hover {
  background-color: #404040;
}

html.dark .el-menu-item.is-active {
  background-color: #409eff;
}

#app {
  width: 100%;
  height: 100vh;
  margin: 0;
  padding: 0;
  position: relative;
  overflow: auto;
}

/* 确保按钮和可点击元素可以正常交互 */
button,
.el-button,
a,
[role="button"],
.el-menu-item {
  pointer-events: auto !important;
  cursor: pointer !important;
}

/* 确保输入框和表单元素可以正常交互 */
input,
textarea,
select,
.el-input,
.el-select,
.el-textarea {
  pointer-events: auto !important;
  cursor: text !important;
}

/* 确保没有全局遮罩层阻止点击 */
body::before,
body::after,
#app::before,
#app::after {
  display: none !important;
  pointer-events: none !important;
}
</style>



