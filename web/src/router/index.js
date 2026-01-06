import { createRouter, createWebHashHistory } from 'vue-router'
import HomeView from '../views/index/HomeView.vue'
import FilesView from '../views/files/FilesView.vue'
import NotesView from '../views/notes/NotesView.vue'
import LoginView from '../views/auth/LoginView.vue'
import RegisterView from '../views/auth/RegisterView.vue'

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
      path: '/search',
      name: 'search',
      component: () => import('../views/index/SearchView.vue'),
    },
    {
      path: '/admin/storage-backends',
      name: 'storage-backends',
      component: () => import('../views/admin/StorageBackendsView.vue'),
    },
  ],
})

export default router
