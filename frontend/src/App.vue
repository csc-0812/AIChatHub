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
  background-image: url('https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=modern%20abstract%20background%20with%20soft%20blue%20and%20purple%20gradients%2C%20professional%20tech%20style&image_size=landscape_16_9');
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
  padding: 20px;
  margin: 0;
  overflow: hidden;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .app-container {
    padding: 10px;
  }
}
</style>
