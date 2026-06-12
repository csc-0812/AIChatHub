<script>
import Login from './modules/auth/Login.vue'
import Chat from './modules/chat/Chat.vue'
import Admin from './modules/admin/Admin.vue'
import { API_CONFIG } from './utils/config.js'

export default {
  name: 'App',
  components: {
    Login,
    Chat,
    Admin
  },
  data() {
    return {
      isLoggedIn: false,
      currentView: 'chat'  // 'chat' 或 'admin'
    }
  },
  async mounted() {
    // 检查本地存储中是否有token，并验证有效性
    const token = localStorage.getItem('token');
    if (token) {
      // 验证token是否有效（检查是否被挤出或过期）
      try {
        const response = await fetch(`${API_CONFIG.API_BASE_URL}/auth/me`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        if (response.ok) {
          this.isLoggedIn = true;
        } else {
          // token无效，清除本地存储
          this.handleLogout();
        }
      } catch (error) {
        console.error('验证登录状态失败:', error);
        this.handleLogout();
      }
    }
  },
  methods: {
    handleLoginSuccess() {
      this.isLoggedIn = true;
      // 检查用户角色，管理员默认进入管理员界面
      const role = localStorage.getItem('role');
      if (role === 'admin' || role === 'super_admin') {
        this.currentView = 'admin';
      } else {
        this.currentView = 'chat';
      }
    },
    handleLogout() {
      localStorage.removeItem('token');
      localStorage.removeItem('username');
      localStorage.removeItem('role');
      this.isLoggedIn = false;
      this.currentView = 'chat';
    },
    goToAdmin() {
      this.currentView = 'admin';
    },
    goToChat() {
      this.currentView = 'chat';
    }
  }
}
</script>

<template>
  <div v-if="!isLoggedIn" class="app-container">
    <Login @login-success="handleLoginSuccess" />
  </div>
  <div v-else>
    <Chat 
      v-if="currentView === 'chat'" 
      @logout="handleLogout" 
      @go-admin="goToAdmin"
    />
    <Admin 
      v-else-if="currentView === 'admin'" 
      @logout="handleLogout"
      @back="goToChat"
    />
  </div>
</template>

<style>
/* 全局样式重置 */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body {
  height: 100%;
  width: 100%;
}

#app {
  height: 100%;
  width: 100%;
}
</style>

<style scoped>
.app-container {
  min-height: 100vh;
  min-width: 100vw;
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: var(--app-bg);
  background-image:
    radial-gradient(circle at 20% 35%, rgba(45, 107, 255, 0.08) 0%, transparent 50%),
    radial-gradient(circle at 80% 20%, rgba(30, 80, 229, 0.06) 0%, transparent 40%),
    radial-gradient(circle at 50% 80%, rgba(110, 168, 255, 0.05) 0%, transparent 50%),
    linear-gradient(180deg, var(--app-bg) 0%, var(--app-bg-secondary) 100%);
  position: relative;
  padding: 20px;
  margin: 0;
  overflow: hidden;
}

.app-container::before {
  content: '';
  position: absolute;
  inset: 0;
  background-image: url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.03'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E");
  opacity: 0.6;
  pointer-events: none;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .app-container {
    padding: 16px;
  }
}
</style>
