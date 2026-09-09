<template>
  <div class="layout-container">
    <el-container>
      <el-aside width="220px" class="sidebar">
        <div class="logo">
          <div class="logo-icon">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/>
            </svg>
          </div>
          <h3>房东端</h3>
        </div>
        <el-menu
          :default-active="activeMenu"
          router
          background-color="transparent"
          text-color="#a0aec0"
          active-text-color="#fff"
        >
          <el-menu-item index="/landlord/statistics">
            <el-icon><TrendCharts /></el-icon>
            <span>数据统计</span>
          </el-menu-item>
          <el-menu-item index="/landlord/apartments">
            <el-icon><House /></el-icon>
            <span>我的公寓</span>
          </el-menu-item>
          <el-menu-item index="/landlord/appointments">
            <el-icon><Calendar /></el-icon>
            <span>看房预约</span>
          </el-menu-item>
          <el-menu-item index="/landlord/contracts">
            <el-icon><Document /></el-icon>
            <span>合同管理</span>
          </el-menu-item>
          <el-menu-item index="/landlord/payments">
            <el-icon><Money /></el-icon>
            <span>支付管理</span>
          </el-menu-item>
          <el-menu-item index="/landlord/repairs">
            <el-icon><Tools /></el-icon>
            <span>报障处理</span>
          </el-menu-item>
          <el-menu-item index="/landlord/messages">
            <el-icon><Bell /></el-icon>
            <span>消息中心</span>
          </el-menu-item>
          <el-menu-item index="/landlord/profile">
            <el-icon><User /></el-icon>
            <span>个人中心</span>
          </el-menu-item>
        </el-menu>
        <div class="sidebar-footer">
          <div class="user-card">
            <div class="user-avatar">{{ realName?.charAt(0) || 'L' }}</div>
            <div class="user-details">
              <span class="user-name">{{ realName }}</span>
              <span class="user-role">ID: {{ userId }}</span>
            </div>
          </div>
        </div>
      </el-aside>
      <el-container>
        <el-header>
          <div class="header-content">
            <div class="header-left">
              <h1 class="title">{{ pageTitle }}</h1>
              <span class="breadcrumb">房东端 / {{ pageTitle }}</span>
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
import { TrendCharts, House, Calendar, Document, Money, Tools, Bell, User, SwitchButton } from '@element-plus/icons-vue'

export default {
  name: 'LandlordLayout',
  components: { TrendCharts, House, Calendar, Document, Money, Tools, Bell, User, SwitchButton },
  computed: {
    activeMenu() {
      return this.$route.path
    },
    pageTitle() {
      const titles = {
        '/landlord/statistics': '数据统计',
        '/landlord/apartments': '我的公寓',
        '/landlord/appointments': '看房预约',
        '/landlord/contracts': '合同管理',
        '/landlord/payments': '支付管理',
        '/landlord/repairs': '报障处理',
        '/landlord/messages': '消息中心',
        '/landlord/profile': '个人中心'
      }
      return titles[this.$route.path] || '房东端'
    },
    realName() {
      return localStorage.getItem('realName') || '房东'
    },
    userId() {
      return localStorage.getItem('userId') || '-'
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
  overflow-y: auto;
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
  background: linear-gradient(135deg, #10b981, #34d399);
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
  background: rgba(16, 185, 129, 0.15);
}

:deep(.el-menu-item.is-active) {
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.3), rgba(52, 211, 153, 0.3));
  box-shadow: 0 4px 15px rgba(16, 185, 129, 0.3);
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
  background: linear-gradient(135deg, #10b981, #34d399);
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
  color: #10b981;
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
