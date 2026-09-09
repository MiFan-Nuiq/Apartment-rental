<template>
  <div class="layout-container">
    <el-container>
      <el-aside width="220px" class="sidebar">
        <div class="logo">
          <div class="logo-icon">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"/>
            </svg>
          </div>
          <h3>管理员端</h3>
        </div>
        <el-menu
          :default-active="activeMenu"
          router
          background-color="transparent"
          text-color="#a0aec0"
          active-text-color="#fff"
        >
          <el-menu-item index="/admin/statistics">
            <el-icon><TrendCharts /></el-icon>
            <span>数据统计</span>
          </el-menu-item>
          <el-menu-item index="/admin/dashboard">
            <el-icon><DataAnalysis /></el-icon>
            <span>数据概览</span>
          </el-menu-item>
          <el-menu-item index="/admin/users">
            <el-icon><User /></el-icon>
            <span>用户管理</span>
          </el-menu-item>
          <el-menu-item index="/admin/apartments">
            <el-icon><House /></el-icon>
            <span>公寓管理</span>
          </el-menu-item>
          <el-menu-item index="/admin/contracts">
            <el-icon><Document /></el-icon>
            <span>合同管理</span>
          </el-menu-item>
          <el-menu-item index="/admin/reviews">
            <el-icon><ChatDotRound /></el-icon>
            <span>评价管理</span>
          </el-menu-item>
          <el-menu-item index="/admin/complaints">
            <el-icon><Warning /></el-icon>
            <span>投诉管理</span>
          </el-menu-item>
          <el-menu-item index="/admin/messages">
            <el-icon><Bell /></el-icon>
            <span>消息发布</span>
          </el-menu-item>
        </el-menu>
        <div class="sidebar-footer">
          <div class="user-card">
            <div class="user-avatar">{{ realName?.charAt(0) || 'A' }}</div>
            <div class="user-details">
              <span class="user-name">{{ realName }}</span>
              <span class="user-role">管理员</span>
            </div>
          </div>
        </div>
      </el-aside>
      <el-container>
        <el-header>
          <div class="header-content">
            <div class="header-left">
              <h1 class="title">{{ pageTitle }}</h1>
              <span class="breadcrumb">{{ pageTitle }}</span>
            </div>
            <div class="header-right">
              <el-button type="text" class="logout-btn" @click="handleLogout">
                <el-icon><SwitchButton /></el-icon>
                退出登录
              </el-button>
            </div>
          </div>
        </el-header>
        <el-main>
          <transition name="page" mode="out-in">
            <router-view />
          </transition>
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script>
import { TrendCharts, DataAnalysis, User, House, Document, ChatDotRound, Warning, Bell, SwitchButton } from '@element-plus/icons-vue'

export default {
  name: 'AdminLayout',
  components: { TrendCharts, DataAnalysis, User, House, Document, ChatDotRound, Warning, Bell, SwitchButton },
  computed: {
    activeMenu() {
      return this.$route.path
    },
    pageTitle() {
      const titles = {
        '/admin/statistics': '数据统计',
        '/admin/dashboard': '数据概览',
        '/admin/users': '用户管理',
        '/admin/apartments': '公寓管理',
        '/admin/contracts': '合同管理',
        '/admin/reviews': '评价管理',
        '/admin/complaints': '投诉管理',
        '/admin/messages': '消息发布'
      }
      return titles[this.$route.path] || '管理员端'
    },
    realName() {
      return localStorage.getItem('realName') || '管理员'
    }
  },
  methods: {
    handleLogout() {
      localStorage.clear()
      this.$router.push('/login')
    }
  }
}
</script>

<style scoped>
.layout-container {
  height: 100vh;
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
}

.el-container {
  height: 100%;
}

.sidebar {
  background: linear-gradient(180deg, #1e1e2f 0%, #151521 100%);
  display: flex;
  flex-direction: column;
  box-shadow: 4px 0 20px rgba(0, 0, 0, 0.3);
}

.logo {
  height: 70px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 0 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.logo-icon {
  width: 36px;
  height: 36px;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.05); }
}

.logo h3 {
  color: #fff;
  font-size: 18px;
  font-weight: 600;
  background: linear-gradient(135deg, #fff, #a0aec0);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.el-menu {
  border-right: none;
  flex: 1;
  padding: 10px;
}

:deep(.el-menu-item) {
  border-radius: 10px;
  margin: 4px 0;
  transition: all 0.3s ease;
}

:deep(.el-menu-item:hover) {
  background: rgba(99, 102, 241, 0.15);
}

:deep(.el-menu-item.is-active) {
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.3), rgba(139, 92, 246, 0.3));
  box-shadow: 0 4px 15px rgba(99, 102, 241, 0.3);
}

.sidebar-footer {
  padding: 15px;
  border-top: 1px solid rgba(255, 255, 255, 0.05);
}

.user-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 12px;
}

.user-avatar {
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: 600;
  font-size: 16px;
}

.user-details {
  display: flex;
  flex-direction: column;
}

.user-name {
  color: #fff;
  font-size: 14px;
  font-weight: 500;
}

.user-role {
  color: #6366f1;
  font-size: 12px;
}

.el-header {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  box-shadow: 0 2px 20px rgba(0, 0, 0, 0.08);
  padding: 0 30px;
  height: 70px !important;
}

.header-content {
  height: 100%;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  flex-direction: column;
}

.title {
  font-size: 20px;
  font-weight: 600;
  color: #1a1a2e;
  margin: 0;
}

.breadcrumb {
  font-size: 12px;
  color: #888;
  margin-top: 2px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 15px;
}

.logout-btn {
  color: #ef4444;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 6px;
}

.logout-btn:hover {
  color: #dc2626;
}

.el-main {
  background-color: #f8fafc;
  padding: 24px;
  overflow-y: auto;
}

.page-enter-active,
.page-leave-active {
  transition: all 0.3s ease;
}

.page-enter-from {
  opacity: 0;
  transform: translateY(10px);
}

.page-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}
</style>
