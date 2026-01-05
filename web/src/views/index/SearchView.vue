<template>
  <div class="bg-gray-50 dark:bg-gray-900">
    <div class="container mx-auto px-4 py-8">
      <!-- 搜索头部 -->
      <div
        class="bg-white dark:bg-gray-800 rounded-2xl shadow-sm p-8 mb-8 border border-gray-200 dark:border-gray-700"
      >
        <div class="text-center">
          <h1 class="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-4">
            <span v-if="query">搜索结果</span>
            <span v-else>全局搜索</span>
          </h1>
          <p v-if="query" class="text-gray-600 dark:text-gray-400 mb-6">
            搜索关键词："<span class="font-semibold text-blue-600">{{ query }}</span
            >"
          </p>

          <!-- 重新搜索 -->
          <div class="max-w-2xl mx-auto">
            <div class="relative">
              <div class="absolute inset-y-0 left-0 flex items-center pl-4 pointer-events-none">
                <svg
                  class="w-5 h-5 text-gray-400"
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
                v-model="searchInput"
                @keyup.enter="performSearch"
                type="text"
                placeholder="搜索文件名、笔记内容..."
                class="w-full pl-12 pr-16 py-4 text-lg border border-gray-300 dark:border-gray-600 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-gray-100"
              />
              <button
                @click="performSearch"
                class="absolute right-2 top-1/2 transform -translate-y-1/2 btn btn-primary btn-sm"
                :disabled="loading"
              >
                <span v-if="loading" class="loading loading-spinner loading-xs"></span>
                <span v-else>搜索</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- 搜索结果统计 -->
      <div v-if="hasResults" class="mb-8">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-4 text-sm text-gray-600 dark:text-gray-400">
            <span
              >找到 <strong>{{ totalResults }}</strong> 个结果</span
            >
            <span v-if="searchTime">耗时 {{ searchTime }}ms</span>
          </div>

          <!-- 结果类型筛选 -->
          <div class="flex gap-2">
            <button
              @click="activeTab = 'all'"
              :class="['btn btn-sm', activeTab === 'all' ? 'btn-primary' : 'btn-ghost']"
            >
              全部 ({{ totalResults }})
            </button>
            <button
              @click="activeTab = 'files'"
              :class="['btn btn-sm', activeTab === 'files' ? 'btn-primary' : 'btn-ghost']"
            >
              文件 ({{ files.length }})
            </button>
            <button
              @click="activeTab = 'notes'"
              :class="['btn btn-sm', activeTab === 'notes' ? 'btn-primary' : 'btn-ghost']"
            >
              笔记 ({{ notes.length }})
            </button>
          </div>
        </div>
      </div>

      <!-- 搜索结果内容 -->
      <div v-if="loading" class="flex justify-center py-12">
        <div class="text-center">
          <span class="loading loading-spinner loading-lg text-blue-500"></span>
          <p class="text-gray-500 mt-4">正在搜索...</p>
        </div>
      </div>

      <div v-else-if="!hasResults && query" class="text-center py-12">
        <div
          class="bg-white dark:bg-gray-800 rounded-2xl shadow-sm p-12 border border-gray-200 dark:border-gray-700"
        >
          <div class="text-6xl mb-6">🔍</div>
          <h3 class="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-2">
            未找到相关结果
          </h3>
          <p class="text-gray-500 dark:text-gray-400 mb-6">
            尝试使用不同的关键词，或检查拼写是否正确
          </p>
          <div class="space-y-2 text-sm text-gray-600 dark:text-gray-400">
            <p>• 使用更简短的关键词</p>
            <p>• 检查拼写和空格</p>
            <p>• 尝试相关的同义词</p>
          </div>
        </div>
      </div>

      <div v-else-if="hasResults" class="space-y-8">
        <!-- 文件搜索结果 -->
        <div v-if="(activeTab === 'all' || activeTab === 'files') && files.length > 0">
          <div
            class="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden"
          >
            <div class="p-6 border-b border-gray-200 dark:border-gray-700">
              <div class="flex items-center gap-3">
                <div
                  class="w-8 h-8 bg-blue-100 dark:bg-blue-900 rounded-lg flex items-center justify-center"
                >
                  <svg
                    class="w-4 h-4 text-blue-600 dark:text-blue-300"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"
                    ></path>
                  </svg>
                </div>
                <h2 class="text-lg font-semibold text-gray-900 dark:text-gray-100">
                  文件结果 ({{ files.length }})
                </h2>
              </div>
            </div>
            <div class="p-6">
              <FileGrid
                :files="files"
                @delete-file="handleDelete"
                @preview-file="handlePreview"
                @manage-notes="handleManageNotes"
              />
            </div>
          </div>
        </div>

        <!-- 笔记搜索结果 -->
        <div v-if="(activeTab === 'all' || activeTab === 'notes') && notes.length > 0">
          <div
            class="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden"
          >
            <div class="p-6 border-b border-gray-200 dark:border-gray-700">
              <div class="flex items-center gap-3">
                <div
                  class="w-8 h-8 bg-green-100 dark:bg-green-900 rounded-lg flex items-center justify-center"
                >
                  <svg
                    class="w-4 h-4 text-green-600 dark:text-green-300"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                    ></path>
                  </svg>
                </div>
                <h2 class="text-lg font-semibold text-gray-900 dark:text-gray-100">
                  笔记结果 ({{ notes.length }})
                </h2>
              </div>
            </div>
            <div class="p-6">
              <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                <div
                  v-for="note in notes"
                  :key="note.id"
                  class="bg-gray-50 dark:bg-gray-700 rounded-xl p-6 hover:shadow-md transition-shadow cursor-pointer border border-gray-200 dark:border-gray-600"
                  @click="openNote(note)"
                >
                  <div class="flex items-start justify-between mb-3">
                    <h3 class="font-semibold text-gray-900 dark:text-gray-100 line-clamp-1">
                      {{ note.title || '无标题' }}
                    </h3>
                    <div class="shrink-0 ml-2">
                      <button
                        @click.stop="editNote(note)"
                        class="btn btn-xs btn-ghost text-gray-400 hover:text-blue-500"
                      >
                        <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path
                            stroke-linecap="round"
                            stroke-linejoin="round"
                            stroke-width="2"
                            d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
                          ></path>
                        </svg>
                      </button>
                    </div>
                  </div>
                  <p
                    class="text-sm text-gray-600 dark:text-gray-300 line-clamp-3 mb-4"
                    v-html="highlightText(note.content, query)"
                  ></p>
                  <div class="flex items-center justify-between text-xs text-gray-500">
                    <span>{{ formatDate(note.updated_at) }}</span>
                    <div v-if="note.files && note.files.length > 0" class="flex items-center gap-1">
                      <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path
                          stroke-linecap="round"
                          stroke-linejoin="round"
                          stroke-width="2"
                          d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.586-6.586a2 2 0 00-2.828-2.828l-6.586 6.586a2 2 0 102.828 2.828L19 9"
                        ></path>
                      </svg>
                      {{ note.files.length }}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 空状态 -->
      <div v-else-if="!query" class="text-center py-12">
        <div
          class="bg-white dark:bg-gray-800 rounded-2xl shadow-sm p-12 border border-gray-200 dark:border-gray-700"
        >
          <div class="text-6xl mb-6">🔍</div>
          <h3 class="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-2">开始搜索</h3>
          <p class="text-gray-500 dark:text-gray-400">输入关键词来搜索您的文件和笔记</p>
        </div>
      </div>
    </div>

    <!-- 文件预览模态框 -->
    <FilePreview
      :file="previewFile"
      @close="closePreview"
      @add-note="(file) => handleManageNotes(file, 'file')"
    />

    <!-- 统一笔记管理模态框 -->
    <UnifiedNotes
      :is-open="showNotes"
      :item="notesItem"
      :item-type="notesItemType"
      @close="closeNotes"
    />
  </div>
</template>

<script setup>
import { ref, watch, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import fileService from '../../api/fileService.js'
import noteService from '../../api/noteService.js'
import FileGrid from '../../components/FileGrid.vue'
import FilePreview from '../../components/FilePreview.vue'
import UnifiedNotes from '../../components/UnifiedNotes.vue'

const route = useRoute()
const router = useRouter()

const query = ref('')
const searchInput = ref('')
const files = ref([])
const notes = ref([])
const loading = ref(false)
const searchTime = ref(0)
const activeTab = ref('all')
const previewFile = ref(null)
const notesItem = ref(null)
const notesItemType = ref('file')
const showNotes = ref(false)

// 计算属性
const totalResults = computed(() => files.value.length + notes.value.length)
const hasResults = computed(() => totalResults.value > 0)

// 格式化日期
const formatDate = (dateString) => {
  const date = new Date(dateString)
  const now = new Date()
  const diff = now - date
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))

  if (days === 0) return '今天'
  if (days === 1) return '昨天'
  if (days < 7) return `${days}天前`
  return date.toLocaleDateString()
}

// 高亮搜索文本
const highlightText = (text, searchQuery) => {
  if (!searchQuery || !text) return text

  // 简单高亮实现，实际项目中可能需要更复杂的处理
  const regex = new RegExp(`(${searchQuery})`, 'gi')
  return text.replace(regex, '<mark class="bg-yellow-200 dark:bg-yellow-600">$1</mark>')
}

// 执行搜索
const performSearch = async () => {
  const searchQuery = searchInput.value.trim() || query.value.trim()
  if (!searchQuery) return

  // 更新URL
  if (searchQuery !== route.query.q) {
    router.push({ query: { q: searchQuery } })
    return
  }

  loading.value = true
  const startTime = Date.now()

  try {
    const [filesRes, notesRes] = await Promise.all([
      fileService.getFiles({ q: searchQuery }),
      noteService.getNotes({ q: searchQuery }),
    ])

    files.value = filesRes.data || []
    notes.value = notesRes.data || []

    searchTime.value = Date.now() - startTime
  } catch (error) {
    console.error('Search failed', error)
  } finally {
    loading.value = false
  }
}

// 事件处理
const handleDelete = async (id) => {
  if (!confirm('确定要删除这个文件吗？')) return
  try {
    await fileService.deleteFile(id)
    files.value = files.value.filter((file) => file.id !== id)
  } catch (error) {
    console.error('Failed to delete file', error)
  }
}

const handlePreview = (file) => {
  previewFile.value = file
}

const closePreview = () => {
  previewFile.value = null
}

const handleManageNotes = (item, type) => {
  notesItem.value = item
  notesItemType.value = type
  showNotes.value = true
  previewFile.value = null
}

const closeNotes = () => {
  showNotes.value = false
  notesItem.value = null
}

const openNote = (note) => {
  router.push({ path: '/notes', query: { note: note.id } })
}

const editNote = (note) => {
  router.push({ path: '/notes', query: { edit: note.id } })
}

// 监听路由查询参数变化
watch(
  () => route.query.q,
  (newQ) => {
    query.value = newQ || ''
    searchInput.value = newQ || ''
    if (newQ) {
      performSearch()
    } else {
      files.value = []
      notes.value = []
    }
  },
  { immediate: true },
)
</script>
