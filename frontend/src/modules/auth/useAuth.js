import { ref } from 'vue'
import * as authApi from './authApi.js'

export function useAuth() {
  // 状态
  const isRegisterMode = ref(false)
  const form = ref({
    username: '',
    password: '',
    email: '',
    full_name: ''
  })
  const loading = ref(false)
  const error = ref('')
  const showSuccess = ref(false)
  const successMessage = ref('')

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
        form.value.full_name || undefined
      )
      console.log('注册成功:', data)

      // 显示成功提示，然后切换到登录模式
      successMessage.value = '注册成功！请登录'
      showSuccess.value = true

      setTimeout(() => {
        showSuccess.value = false
        switchToLogin()
      }, 1500)

      return data
    } catch (err) {
      error.value = err.message
      console.error('注册失败:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  // 切换到注册模式
  function switchToRegister() {
    isRegisterMode.value = true
    resetForm()
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
      full_name: ''
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
    // 方法
    login,
    register,
    switchToRegister,
    switchToLogin,
    resetForm
  }
}
