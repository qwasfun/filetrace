<script setup>
import { ref } from 'vue'
import { register as registerApi } from '@/api/authService'
import { useAuthStore } from '@/stores/auth'
import router from '@/router'

const authStore = useAuthStore()

const form = ref({
  username: '',
  password: '',
  confirmPassword: '',
})
const loading = ref(false)
const errorMsg = ref('')

const submit = async () => {
  if (!form.value.username || !form.value.password) return
  if (form.value.password !== form.value.confirmPassword) {
    errorMsg.value = '两次输入的密码不一致'
    return
  }

  loading.value = true
  errorMsg.value = ''

  try {
    const params = {
      username: form.value.username,
      password: form.value.password,
    }
    const res = await registerApi(params)

    // 使用 auth store 保存认证信息
    authStore.setAuth(res)

    router.push('/')
  } catch (err) {
    console.error(err)
    errorMsg.value = err.response?.data?.detail || '注册失败，请稍后重试'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div
    class="min-h-[calc(100vh-4rem)] flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8 bg-gray-50 dark:bg-gray-900"
  >
    <div
      class="max-w-md w-full space-y-8 bg-white dark:bg-gray-800 p-8 rounded-xl shadow-lg border border-gray-100 dark:border-gray-700"
    >
      <div>
        <h2 class="mt-6 text-center text-3xl font-extrabold text-gray-900 dark:text-white">
          创建账户
        </h2>
        <p class="mt-2 text-center text-sm text-gray-600 dark:text-gray-400">
          加入我们，开始您的文件管理之旅
        </p>
      </div>
      <form class="mt-8 space-y-6" @submit.prevent="submit">
        <div class="rounded-md shadow-sm -space-y-px">
          <div class="form-control w-full">
            <label class="label">
              <span class="label-text">用户名</span>
            </label>
            <input
              v-model="form.username"
              type="text"
              required
              class="input input-bordered w-full focus:input-primary"
              placeholder="请输入用户名"
              autocomplete="username"
            />
          </div>
          <div class="form-control w-full mt-4">
            <label class="label">
              <span class="label-text">密码</span>
            </label>
            <input
              v-model="form.password"
              type="password"
              required
              class="input input-bordered w-full focus:input-primary"
              placeholder="请输入密码"
              autocomplete="new-password"
            />
          </div>
          <div class="form-control w-full mt-4">
            <label class="label">
              <span class="label-text">确认密码</span>
            </label>
            <input
              v-model="form.confirmPassword"
              type="password"
              required
              class="input input-bordered w-full focus:input-primary"
              placeholder="请再次输入密码"
              autocomplete="new-password"
            />
          </div>
        </div>

        <div v-if="errorMsg" class="alert alert-error text-sm py-2">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            class="stroke-current shrink-0 h-6 w-6"
            fill="none"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          <span>{{ errorMsg }}</span>
        </div>

        <div>
          <button
            type="submit"
            class="btn btn-primary w-full text-white bg-linear-to-r from-blue-500 to-indigo-600 hover:from-blue-600 hover:to-indigo-700 border-none"
            :class="{ loading: loading }"
            :disabled="loading"
          >
            {{ loading ? '注册中...' : '注册' }}
          </button>
        </div>

        <div class="text-center mt-4">
          <span class="text-sm text-gray-600 dark:text-gray-400">已有账号？</span>
          <RouterLink to="/auth/login" class="link link-primary text-sm ml-1 font-medium">
            立即登录
          </RouterLink>
        </div>
      </form>
    </div>
  </div>
</template>
