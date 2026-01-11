import { createRouter, createWebHashHistory } from 'vue-router'
import HomeView from '../views/index/HomeView.vue'
import FilesView from '../views/files/FilesView.vue'
import NotesView from '../views/notes/NotesView.vue'
import LoginView from '../views/auth/LoginView.vue'
import RegisterView from '../views/auth/RegisterView.vue'
import { useAuthStore } from '../stores/auth'

const router = createRouter({
  history: createWebHashHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView,
    },
    {
      path: '/auth/register',
      name: 'RegisterView',
      component: RegisterView,
    },
    {
      path: '/auth/login',
      name: 'LoginView',
      component: LoginView,
    },
    {
      path: '/files',
      name: 'files',
      component: FilesView,
    },
    {
      path: '/file/:id',
      name: 'file-detail',
      component: () => import('../views/files/FileDetailView.vue'),
    },
    {
      path: '/recycle',
      name: 'recycle',
      component: () => import('../views/files/RecycleBinView.vue'),
    },
    {
      path: '/notes',
      name: 'notes',
      component: NotesView,
    },
    {
      path: '/note/:id',
      name: 'note-detail',
      component: () => import('../views/notes/NoteDetailView.vue'),
    },
    {
      path: '/search',
      name: 'search',
      component: () => import('../views/index/SearchView.vue'),
    },
    {
      path: '/admin/storage-backends',
      name: 'storage-backends',
      component: () => import('../views/admin/StorageBackendsView.vue'),
      meta: { requiresAdmin: true },
    },
  ],
})

// 路由守卫：检查管理员权限
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()

  // 检查是否需要管理员权限
  if (to.meta.requiresAdmin) {
    if (!authStore.isAuthenticated) {
      // 未登录，跳转到登录页
      next({ name: 'LoginView', query: { redirect: to.fullPath } })
    } else if (!authStore.isAdmin) {
      // 已登录但不是管理员，显示错误或跳转到首页
      alert('只有管理员才能访问此页面')
      next({ name: 'home' })
    } else {
      // 是管理员，允许访问
      next()
    }
  } else {
    // 不需要管理员权限，正常访问
    next()
  }
})

export default router
