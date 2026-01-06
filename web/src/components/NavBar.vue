<template>
  <header
    class="bg-white dark:bg-gray-900 shadow-sm border-b border-gray-200 dark:border-gray-700 sticky top-0 z-40"
  >
    <div class="container mx-auto px-4">
      <div class="flex items-center justify-between h-16">
        <!-- 品牌logo -->
        <div class="flex items-center gap-8">
          <RouterLink to="/" class="flex items-center gap-2 hover:opacity-80 transition-opacity">
            <div
              class="w-8 h-8 bg-linear-to-r from-blue-500 to-purple-600 rounded-lg flex items-center justify-center"
            >
              <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"
                ></path>
              </svg>
            </div>
            <span class="text-xl font-bold text-gray-900 dark:text-gray-100">ArchiveNote</span>
          </RouterLink>

          <!-- 主导航 -->
          <nav class="hidden md:flex items-center gap-1">
            <RouterLink
              to="/files"
              class="px-4 py-2 rounded-lg text-sm font-medium transition-colors"
              :class="{
                'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300':
                  $route.path === '/files',
                'text-gray-600 hover:text-gray-900 hover:bg-gray-100 dark:text-gray-300 dark:hover:text-gray-100 dark:hover:bg-gray-800':
                  $route.path !== '/files',
              }"
            >
              <span class="flex items-center gap-2"> 📁 文件管理 </span>
            </RouterLink>
            <RouterLink
              to="/notes"
              class="px-4 py-2 rounded-lg text-sm font-medium transition-colors"
              :class="{
                'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300':
                  $route.path === '/notes',
                'text-gray-600 hover:text-gray-900 hover:bg-gray-100 dark:text-gray-300 dark:hover:text-gray-100 dark:hover:bg-gray-800':
                  $route.path !== '/notes',
              }"
            >
              <span class="flex items-center gap-2"> 📝 笔记管理 </span>
            </RouterLink>
            <RouterLink
              to="/recycle"
              class="px-4 py-2 rounded-lg text-sm font-medium transition-colors"
              :class="{
                'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300':
                  $route.path === '/recycle',
                'text-gray-600 hover:text-gray-900 hover:bg-gray-100 dark:text-gray-300 dark:hover:text-gray-100 dark:hover:bg-gray-800':
                  $route.path !== '/recycle',
              }"
            >
              <span class="flex items-center gap-2"> 🗑️ 回收站 </span>
            </RouterLink>
            <!-- 管理员菜单 -->
            <RouterLink
              v-if="isAdmin"
              to="/admin/storage-backends"
              class="px-4 py-2 rounded-lg text-sm font-medium transition-colors"
              :class="{
                'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300':
                  $route.path.startsWith('/admin'),
                'text-gray-600 hover:text-gray-900 hover:bg-gray-100 dark:text-gray-300 dark:hover:text-gray-100 dark:hover:bg-gray-800':
                  !$route.path.startsWith('/admin'),
              }"
            >
              <span class="flex items-center gap-2"> ⚙️ 系统管理 </span>
            </RouterLink>
          </nav>
        </div>

        <!-- 右侧工具栏 -->
        <div class="flex items-center gap-3">
          <!-- 搜索框 -->
          <div class="relative hidden md:block">
            <div class="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none">
              <svg
                class="w-4 h-4 text-gray-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                ></path>
              </svg>
            </div>
            <input
              v-model="searchQuery"
              @keyup.enter="handleSearch"
              type="text"
              placeholder="搜索文件和笔记..."
              class="w-64 pl-10 pr-4 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-gray-100 placeholder-gray-400"
            />
          </div>

          <!-- 用户认证按钮 -->
          <div class="flex items-center gap-2">
            <template v-if="isLoggedIn">
              <button @click="handleLogout" class="btn btn-sm btn-ghost gap-2">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"
                  ></path>
                </svg>
                退出登录
              </button>
            </template>
            <template v-else>
              <RouterLink to="/auth/login" class="btn btn-sm btn-ghost gap-2">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M11 16l-4-4m0 0l4-4m-4 4h14m-5 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h7a3 3 0 013 3v1"
                  ></path>
                </svg>
                登录
              </RouterLink>
              <RouterLink to="/auth/register" class="btn btn-sm btn-primary gap-2">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z"
                  ></path>
                </svg>
                注册
              </RouterLink>
            </template>
          </div>

          <!-- 移动端菜单按钮 -->
          <button
            @click="showMobileMenu = !showMobileMenu"
            class="md:hidden btn btn-sm btn-ghost btn-circle"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M4 6h16M4 12h16M4 18h16"
              ></path>
            </svg>
          </button>
        </div>
      </div>

      <!-- 移动端菜单 -->
      <div
        v-if="showMobileMenu"
        class="md:hidden py-4 border-t border-gray-200 dark:border-gray-700"
      >
        <div class="space-y-2">
          <RouterLink
            to="/files"
            class="flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-colors"
            :class="{
              'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300':
                $route.path === '/files',
              'text-gray-600 hover:text-gray-900 hover:bg-gray-100 dark:text-gray-300 dark:hover:text-gray-100 dark:hover:bg-gray-800':
                $route.path !== '/files',
            }"
            @click="showMobileMenu = false"
          >
            📁 文件管理
          </RouterLink>
          <RouterLink
            to="/notes"
            class="flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-colors"
            :class="{
              'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300':
                $route.path === '/notes',
              'text-gray-600 hover:text-gray-900 hover:bg-gray-100 dark:text-gray-300 dark:hover:text-gray-100 dark:hover:bg-gray-800':
                $route.path !== '/notes',
            }"
            @click="showMobileMenu = false"
          >
            📝 笔记管理
          </RouterLink>
          <RouterLink
            to="/recycle"
            class="flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-colors"
            :class="{
              'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300':
                $route.path === '/recycle',
              'text-gray-600 hover:text-gray-900 hover:bg-gray-100 dark:text-gray-300 dark:hover:text-gray-100 dark:hover:bg-gray-800':
                $route.path !== '/recycle',
            }"
            @click="showMobileMenu = false"
          >
            🗑️ 回收站
          </RouterLink>
          <!-- 移动端管理员菜单 -->
          <RouterLink
            v-if="isAdmin"
            to="/admin/storage-backends"
            class="flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-colors"
            :class="{
              'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300':
                $route.path.startsWith('/admin'),
              'text-gray-600 hover:text-gray-900 hover:bg-gray-100 dark:text-gray-300 dark:hover:text-gray-100 dark:hover:bg-gray-800':
                !$route.path.startsWith('/admin'),
            }"
            @click="showMobileMenu = false"
          >
            ⚙️ 系统管理
          </RouterLink>

          <!-- 移动端搜索 -->
          <div class="px-4 pt-2">
            <div class="relative">
              <div class="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none">
                <svg
                  class="w-4 h-4 text-gray-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                  ></path>
                </svg>
              </div>
              <input
                v-model="searchQuery"
                @keyup.enter="handleSearch"
                type="text"
                placeholder="搜索..."
                class="w-full pl-10 pr-4 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-gray-100 placeholder-gray-400"
              />
            </div>
          </div>

          <!-- 移动端认证按钮 -->
          <div class="px-4 pt-2 space-y-2">
            <template v-if="isLoggedIn">
              <button
                @click="handleLogout"
                class="w-full flex items-center justify-center gap-2 px-4 py-3 rounded-lg text-sm font-medium text-gray-600 hover:text-gray-900 hover:bg-gray-100 dark:text-gray-300 dark:hover:text-gray-100 dark:hover:bg-gray-800 transition-colors"
              >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"
                  ></path>
                </svg>
                退出登录
              </button>
            </template>
            <template v-else>
              <RouterLink
                to="/login"
                class="w-full flex items-center justify-center gap-2 px-4 py-3 rounded-lg text-sm font-medium text-gray-600 hover:text-gray-900 hover:bg-gray-100 dark:text-gray-300 dark:hover:text-gray-100 dark:hover:bg-gray-800 transition-colors"
                @click="showMobileMenu = false"
              >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M11 16l-4-4m0 0l4-4m-4 4h14m-5 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h7a3 3 0 013 3v1"
                  ></path>
                </svg>
                登录
              </RouterLink>
              <RouterLink
                to="/register"
                class="w-full flex items-center justify-center gap-2 px-4 py-3 rounded-lg text-sm font-medium bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300 hover:bg-blue-200 dark:hover:bg-blue-800 transition-colors"
                @click="showMobileMenu = false"
              >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z"
                  ></path>
                </svg>
                注册
              </RouterLink>
            </template>
          </div>
        </div>
      </div>
    </div>
  </header>
</template>

<script setup>
import { ref, computed } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { logout } from '@/api/authService'

const router = useRouter()
const authStore = useAuthStore()
const searchQuery = ref('')
const showMobileMenu = ref(false)

// 检查是否已登录（直接使用 store 的计算属性）
const isLoggedIn = computed(() => authStore.isAuthenticated)

// 检查是否为管理员
const isAdmin = computed(() => authStore.isAdmin)

const handleSearch = () => {
  if (searchQuery.value.trim()) {
    router.push({ name: 'search', query: { q: searchQuery.value } })
    showMobileMenu.value = false
  }
}

const handleLogout = async () => {
  // 使用 auth store 清除认证信息
  authStore.clearAuth()
  showMobileMenu.value = false
  await logout()
  router.push('/auth/login')
}
</script>
