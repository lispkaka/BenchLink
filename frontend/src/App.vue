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



