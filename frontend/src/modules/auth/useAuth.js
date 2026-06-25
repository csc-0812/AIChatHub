import { ref } from 'vue'
import * as authApi from './authApi.js'

export function useAuth() {
  // 状态
  const isRegisterMode = ref(false)
  const form = ref({
    username: '',
    password: '',
    email: '',
    full_name: '',
    captcha: ''
  })
  const loading = ref(false)
  const error = ref('')
  const showSuccess = ref(false)
  const successMessage = ref('')
  // 验证码状态
  const captchaId = ref('')
  const captchaText = ref('')
  const captchaLoading = ref(false)

  // 获取验证码
  async function fetchCaptcha() {
    captchaLoading.value = true
    try {
      const data = await authApi.getCaptcha()
      captchaId.value = data.captcha_id
      captchaText.value = data.captcha_text
    } catch (err) {
      error.value = err.message
    } finally {
      captchaLoading.value = false
    }
  }

  // 登录
  async function login(onSuccess) {
    loading.value = true
    error.value = ''

    try {
      const data = await authApi.login(form.value.username, form.value.password)
      console.log('登录成功:', data)

      // 显示成功提示
      successMessage.value = '登录成功！'
      showSuccess.value = true

      // 1秒后自动关闭提示并触发登录成功事件
      setTimeout(() => {
        showSuccess.value = false
        onSuccess?.()
      }, 1000)

      return data
    } catch (err) {
      error.value = err.message
      console.error('登录失败:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  // 注册
  async function register() {
    loading.value = true
    error.value = ''

    try {
      const data = await authApi.register(
        form.value.username,
        form.value.password,
        form.value.email || undefined,
        form.value.full_name || undefined,
        captchaId.value,
        form.value.captcha
      )
      console.log('注册成功:', data)

      // 显示成功提示，然后切换到登录模式
      successMessage.value = data.message || '注册成功！请等待管理员启用后登录。'
      showSuccess.value = true

      setTimeout(() => {
        showSuccess.value = false
        switchToLogin()
      }, 2000)

      return data
    } catch (err) {
      error.value = err.message
      console.error('注册失败:', err)
      // 注册失败时刷新验证码
      fetchCaptcha()
      form.value.captcha = ''
      throw err
    } finally {
      loading.value = false
    }
  }

  // 切换到注册模式
  function switchToRegister() {
    isRegisterMode.value = true
    resetForm()
    fetchCaptcha()
  }

  // 切换到登录模式
  function switchToLogin() {
    isRegisterMode.value = false
    resetForm()
  }

  // 重置表单
  function resetForm() {
    form.value = {
      username: '',
      password: '',
      email: '',
      full_name: '',
      captcha: ''
    }
    error.value = ''
    showSuccess.value = false
  }

  return {
    // 状态
    isRegisterMode,
    form,
    loading,
    error,
    showSuccess,
    successMessage,
    captchaId,
    captchaText,
    captchaLoading,
    // 方法
    login,
    register,
    fetchCaptcha,
    switchToRegister,
    switchToLogin,
    resetForm
  }
}
