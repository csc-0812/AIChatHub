<template>
  <div class="login-container">
    <h1>{{ isRegisterMode ? '注册' : '登录' }}</h1>
    <form @submit.prevent="handleSubmit">
      <div class="form-group">
        <label for="username">用户名</label>
        <input type="text" id="username" v-model="form.username" required />
      </div>
      <div v-if="isRegisterMode" class="form-group">
        <label for="email">邮箱（选填）</label>
        <input type="email" id="email" v-model="form.email" />
      </div>
      <div v-if="isRegisterMode" class="form-group">
        <label for="full_name">全名（选填）</label>
        <input type="text" id="full_name" v-model="form.full_name" />
      </div>
      <div class="form-group">
        <label for="password">密码</label>
        <input type="password" id="password" v-model="form.password" required />
      </div>
      <button type="submit" class="auth-button" :disabled="loading">
        {{ loading ? (isRegisterMode ? '注册中...' : '登录中...') : (isRegisterMode ? '注册' : '登录') }}
      </button>
      <div v-if="error" class="error-message">{{ error }}</div>
    </form>

    <!-- 切换登录/注册 -->
    <div class="switch-mode">
      <span v-if="!isRegisterMode">还没有账号？</span>
      <span v-else>已有账号？</span>
      <a href="#" @click.prevent="isRegisterMode ? switchToLogin() : switchToRegister()">
        {{ isRegisterMode ? '去登录' : '去注册' }}
      </a>
    </div>

    <!-- 成功提示 -->
    <div v-if="showSuccess" class="success-toast">
      <span class="success-icon">✓</span>
      <span>{{ successMessage }}</span>
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
    async handleSubmit() {
      try {
        if (this.isRegisterMode) {
          await this.register()
        } else {
          await this.login(() => {
            this.$emit('login-success')
          })
        }
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
  padding: 40px 36px;
  background: rgba(30, 41, 59, 0.85);
  backdrop-filter: blur(24px) saturate(180%);
  -webkit-backdrop-filter: blur(24px) saturate(180%);
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  box-shadow:
    0 1px 1px rgba(0, 0, 0, 0.2),
    0 4px 8px rgba(0, 0, 0, 0.15),
    0 16px 32px rgba(0, 0, 0, 0.2),
    0 32px 64px rgba(0, 0, 0, 0.15);
  position: relative;
  z-index: 1;
  color: #e2e8f0;
}

.login-container::before {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: 16px;
  padding: 1px;
  background: linear-gradient(135deg, rgba(245, 158, 11, 0.3), rgba(16, 185, 129, 0.15), rgba(245, 158, 11, 0.1));
  -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
  mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
  -webkit-mask-composite: xor;
  mask-composite: exclude;
  pointer-events: none;
}

h1 {
  text-align: center;
  margin-bottom: 8px;
  color: #f1f5f9;
  font-size: 26px;
  font-weight: 600;
  letter-spacing: -0.3px;
}

h1::after {
  content: '';
  display: block;
  width: 32px;
  height: 3px;
  background: linear-gradient(90deg, #f59e0b, #fbbf24);
  border-radius: 2px;
  margin: 16px auto 0;
}

.form-group {
  margin-bottom: 22px;
}

label {
  display: block;
  margin-bottom: 6px;
  font-weight: 500;
  font-size: 13px;
  color: #94a3b8;
  letter-spacing: 0.3px;
  text-transform: uppercase;
}

input {
  width: 100%;
  padding: 12px 16px;
  background: rgba(15, 23, 42, 0.5);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 10px;
  box-sizing: border-box;
  font-size: 15px;
  color: #f1f5f9;
  transition: all 0.2s ease;
  font-family: inherit;
}

input::placeholder {
  color: #64748b;
}

input:focus {
  outline: none;
  border-color: #f59e0b;
  box-shadow: 0 0 0 3px rgba(245, 158, 11, 0.15);
  background: rgba(15, 23, 42, 0.7);
}

.auth-button {
  width: 100%;
  padding: 13px;
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
  color: #0f172a;
  border: none;
  border-radius: 10px;
  cursor: pointer;
  font-size: 15px;
  font-weight: 600;
  letter-spacing: 0.3px;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  margin-top: 14px;
  position: relative;
  overflow: hidden;
}

.auth-button::after {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%);
  opacity: 0;
  transition: opacity 0.25s ease;
}

.auth-button:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 16px rgba(245, 158, 11, 0.3);
}

.auth-button:hover:not(:disabled)::after {
  opacity: 1;
}

.auth-button:active:not(:disabled) {
  transform: translateY(0);
}

.auth-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.error-message {
  margin-top: 14px;
  padding: 10px 14px;
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.2);
  border-radius: 8px;
  color: #fca5a5;
  font-size: 13px;
  text-align: center;
}

/* 切换登录/注册 */
.switch-mode {
  margin-top: 20px;
  text-align: center;
  font-size: 13px;
  color: #94a3b8;
}

.switch-mode a {
  color: #f59e0b;
  text-decoration: none;
  font-weight: 500;
  transition: color 0.2s ease;
}

.switch-mode a:hover {
  color: #fbbf24;
}

/* 成功提示 */
.success-toast {
  position: fixed;
  top: 24px;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(16, 185, 129, 0.95);
  color: white;
  padding: 12px 24px;
  border-radius: 10px;
  box-shadow: 0 8px 24px rgba(16, 185, 129, 0.3);
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 500;
  animation: slideDown 0.35s cubic-bezier(0.4, 0, 0.2, 1), fadeOut 0.3s ease 0.7s forwards;
  z-index: 1000;
}

.success-icon {
  width: 22px;
  height: 22px;
  background-color: rgba(255, 255, 255, 0.25);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateX(-50%) translateY(-16px);
  }
  to {
    opacity: 1;
    transform: translateX(-50%) translateY(0);
  }
}

@keyframes fadeOut {
  from { opacity: 1; }
  to { opacity: 0; }
}

/* 响应式设计 */
@media (max-width: 768px) {
  .login-container {
    padding: 28px 24px;
    margin: 0 12px;
    border-radius: 14px;
  }

  h1 {
    font-size: 22px;
  }

  input {
    padding: 11px 14px;
    font-size: 14px;
  }

  .auth-button {
    padding: 12px;
    font-size: 14px;
  }
}

@media (max-width: 480px) {
  .login-container {
    padding: 24px 20px;
  }

  h1 {
    font-size: 20px;
  }
}
</style>
