import { ref } from 'vue'
import * as authApi from './authApi.js'

export function useAuth() {
  // 状态
  const form = ref({
    username: '',
    password: ''
  })
  const loading = ref(false)
  const error = ref('')
  const showSuccess = ref(false)

  // 登录
  async function login(onSuccess) {
    loading.value = true
    error.value = ''

    try {
      const data = await authApi.login(form.value.username, form.value.password)
      console.log('登录成功:', data)

      // 显示成功提示
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

  // 重置表单
  function resetForm() {
    form.value = {
      username: '',
      password: ''
    }
    error.value = ''
    showSuccess.value = false
  }

  return {
    // 状态
    form,
    loading,
    error,
    showSuccess,
    // 方法
    login,
    resetForm
  }
}
