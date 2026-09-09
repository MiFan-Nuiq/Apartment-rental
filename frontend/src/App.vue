<template>
  <router-view />
</template>

<script>
export default {
  name: 'App'
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body, #app {
  height: 100%;
  font-family: 'Microsoft YaHei', sans-serif;
}

/* 按钮样式 - 浅背景深字体 */
.el-button.is-link {
  background: rgba(99, 102, 241, 0.08) !important;
  color: #6366f1 !important;
  padding: 4px 12px !important;
  border-radius: 6px !important;
}

.el-button.is-link:hover {
  background: rgba(99, 102, 241, 0.15) !important;
}

.el-button.el-button--danger.is-link {
  background: rgba(239, 68, 68, 0.08) !important;
  color: #ef4444 !important;
}

.el-button.el-button--danger.is-link:hover {
  background: rgba(239, 68, 68, 0.15) !important;
}

.el-button.el-button--warning.is-link {
  background: rgba(245, 158, 11, 0.08) !important;
  color: #f59e0b !important;
}

.el-button.el-button--warning.is-link:hover {
  background: rgba(245, 158, 11, 0.15) !important;
}

.el-button.el-button--success.is-link {
  background: rgba(16, 185, 129, 0.08) !important;
  color: #10b981 !important;
}

.el-button.el-button--success.is-link:hover {
  background: rgba(16, 185, 129, 0.15) !important;
}

.el-button.el-button--primary.is-link {
  background: rgba(99, 102, 241, 0.08) !important;
  color: #6366f1 !important;
}

.el-button.el-button--primary.is-link:hover {
  background: rgba(99, 102, 241, 0.15) !important;
}

/* 表格宽度顶边 */
.el-card__body {
  padding: 20px !important;
}

.el-table {
  width: 100% !important;
  margin: 0 !important;
}

.el-table__body-wrapper,
.el-table__header-wrapper {
  width: 100% !important;
}

.el-scrollbar {
  width: 100% !important;
}

.el-card {
  overflow: visible !important;
}
</style>
