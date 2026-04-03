<template>
  <div class="login-container">
    <h1>登录</h1>
    <form @submit.prevent="handleLogin">
      <div class="form-group">
        <label for="username">用户名</label>
        <input type="text" id="username" v-model="form.username" required />
      </div>
      <div class="form-group">
        <label for="password">密码</label>
        <input type="password" id="password" v-model="form.password" required />
      </div>
      <button type="submit" class="login-button" :disabled="loading">
        {{ loading ? '登录中...' : '登录' }}
      </button>
      <div v-if="error" class="error-message">{{ error }}</div>
    </form>
    
    <!-- 成功提示 -->
    <div v-if="showSuccess" class="success-toast">
      <span class="success-icon">✓</span>
      <span>登录成功！</span>
    </div>
  </div>
</template>

<script>
import { useAuth } from './useAuth.js'

export default {
  name: 'Login',
  setup() {
    const auth = useAuth()
    return {
      ...auth
    }
  },
  methods: {
    async handleLogin() {
      try {
        await this.login(() => {
          this.$emit('login-success')
        })
      } catch (error) {
        // 错误已在useAuth中处理
      }
    }
  }
}
</script>

<style scoped>
.login-container {
  max-width: 400px;
  width: 100%;
  padding: 30px;
  background-color: rgba(255, 255, 255, 0.9);
  border-radius: 12px;
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.15);
  backdrop-filter: blur(10px);
}

h1 {
  text-align: center;
  margin-bottom: 30px;
  color: #333;
  font-size: 24px;
  font-weight: 600;
}

.form-group {
  margin-bottom: 20px;
}

label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
  color: #555;
}

input {
  width: 100%;
  padding: 12px 15px;
  border: 1px solid #ddd;
  border-radius: 6px;
  box-sizing: border-box;
  font-size: 16px;
  transition: border-color 0.3s ease;
}

input:focus {
  outline: none;
  border-color: #4CAF50;
  box-shadow: 0 0 0 2px rgba(76, 175, 80, 0.2);
}

.login-button {
  width: 100%;
  padding: 12px;
  background-color: #4CAF50;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 16px;
  font-weight: 500;
  transition: background-color 0.3s ease;
  margin-top: 10px;
}

.login-button:hover {
  background-color: #45a049;
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(76, 175, 80, 0.3);
}

.login-button:active {
  transform: translateY(0);
}

.error-message {
  margin-top: 15px;
  color: #f44336;
  font-size: 14px;
  text-align: center;
}

/* 成功提示 */
.success-toast {
  position: fixed;
  top: 20px;
  left: 50%;
  transform: translateX(-50%);
  background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
  color: white;
  padding: 12px 24px;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(76, 175, 80, 0.4);
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 500;
  animation: slideDown 0.3s ease, fadeOut 0.3s ease 0.7s;
  z-index: 1000;
}

.success-icon {
  width: 20px;
  height: 20px;
  background-color: rgba(255, 255, 255, 0.2);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateX(-50%) translateY(-20px);
  }
  to {
    opacity: 1;
    transform: translateX(-50%) translateY(0);
  }
}

@keyframes fadeOut {
  from {
    opacity: 1;
  }
  to {
    opacity: 0;
  }
}

/* 响应式设计 */
@media (max-width: 768px) {
  .login-container {
    padding: 20px;
    margin: 0 10px;
  }
  
  h1 {
    font-size: 20px;
    margin-bottom: 20px;
  }
  
  input {
    padding: 10px 12px;
    font-size: 14px;
  }
  
  .login-button {
    padding: 10px;
    font-size: 14px;
  }
}

@media (max-width: 480px) {
  .login-container {
    padding: 15px;
  }
  
  h1 {
    font-size: 18px;
  }
}
</style>
