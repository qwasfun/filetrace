<script setup>
import { ref, onMounted, computed } from 'vue'
import fileService from '../api/fileService'
import folderService from '../api/folderService'
import { getFileIcon } from '@/utils/file'

const props = defineProps({
  excludeFileIds: {
    type: Array,
    default: () => [],
  },
  excludeFolderIds: {
    type: Array,
    default: () => [],
  },
  mode: {
    type: String,
    default: 'both', // 'files', 'folders', 'both'
  },
})

const emit = defineEmits(['select', 'cancel'])

const files = ref([])
const folders = ref([])
const loading = ref(false)
const selectedFiles = ref([])
const selectedFolders = ref([])

// Navigation state
const currentFolderId = ref(null)
const breadcrumbs = ref([{ id: null, name: '根目录' }])

// Pagination and Search state
const searchQuery = ref('')
const pageSize = ref(12)

const currentFilePage = ref(1)
const totalFiles = ref(0)
const totalFilesPages = ref(0)

const currentFolderPage = ref(1)
const totalFolders = ref(0)
const totalFoldersPages = ref(0)

const showFiles = computed(() => props.mode === 'files' || props.mode === 'both')
const showFolders = computed(() => props.mode === 'folders' || props.mode === 'both')

const totalSelected = computed(() => selectedFiles.value.length + selectedFolders.value.length)

const loadData = async () => {
  loading.value = true
  try {
    const promises = []

    // Load folders if needed
    if (showFolders.value) {
      const folderParams = {
        page: currentFolderPage.value,
        page_size: pageSize.value,
        q: searchQuery.value || undefined,
      }
      if (currentFolderId.value) {
        folderParams.parent_id = currentFolderId.value
      }
      promises.push(folderService.getFolders(folderParams))
    } else {
      promises.push(Promise.resolve([]))
    }

    // Load files if needed
    if (showFiles.value) {
      const fileParams = {
        page: currentFilePage.value,
        page_size: pageSize.value,
        q: searchQuery.value || undefined,
      }
      if (currentFolderId.value) {
        fileParams.folder_id = currentFolderId.value
      }
      promises.push(fileService.getFiles(fileParams))
    } else {
      promises.push(Promise.resolve({ data: [], total: 0, total_pages: 0 }))
    }

    const [foldersRes, filesRes] = await Promise.all(promises)
    folders.value = foldersRes.data || []
    totalFolders.value = foldersRes.total || 0
    totalFoldersPages.value = foldersRes.total_pages || 0

    files.value = filesRes.data || []
    totalFiles.value = filesRes.total || 0
    totalFilesPages.value = filesRes.total_pages || 0
  } catch (error) {
    console.error('Failed to load data', error)
  } finally {
    loading.value = false
  }
}

const enterFolder = (folder) => {
  currentFolderId.value = folder.id
  breadcrumbs.value.push({ id: folder.id, name: folder.name })
  currentFolderPage.value = 1
  currentFilePage.value = 1
  loadData()
}

const navigateBreadcrumb = (index) => {
  const target = breadcrumbs.value[index]
  currentFolderId.value = target.id
  breadcrumbs.value = breadcrumbs.value.slice(0, index + 1)
  currentFolderPage.value = 1
  currentFilePage.value = 1
  loadData()
}

const toggleFileSelection = (fileId) => {
  if (selectedFiles.value.includes(fileId)) {
    selectedFiles.value = selectedFiles.value.filter((id) => id !== fileId)
  } else {
    selectedFiles.value.push(fileId)
  }
}

const toggleFolderSelection = (folderId) => {
  if (selectedFolders.value.includes(folderId)) {
    selectedFolders.value = selectedFolders.value.filter((id) => id !== folderId)
  } else {
    selectedFolders.value.push(folderId)
  }
}

const changeFolderPage = (page) => {
  if (page < 1 || page > totalFoldersPages.value) return
  currentFilePage.value = page
  loadData()
}

const changeFilePage = (page) => {
  if (page < 1 || page > totalFilesPages.value) return
  currentFilePage.value = page
  loadData()
}

const handleConfirm = () => {
  emit('select', {
    files: selectedFiles.value,
    folders: selectedFolders.value,
  })
}

const isImage = (mimeType) => mimeType?.startsWith('image/')

let searchTimeout
const handleSearch = () => {
  if (searchTimeout) clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    currentFilePage.value = 1
    loadData()
  }, 300)
}

onMounted(() => {
  loadData()
})
</script>

<template>
  <div class="flex flex-col h-full">
    <!-- 头部：搜索和面包屑 -->
    <div class="mb-4 space-y-3">
      <!-- 搜索框 -->
      <div class="relative">
        <svg
          class="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400"
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
        <input
          v-model="searchQuery"
          @input="handleSearch"
          type="text"
          placeholder="搜索文件..."
          class="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary bg-white dark:bg-gray-800"
        />
      </div>

      <!-- Breadcrumb -->
      <div class="text-sm breadcrumbs">
        <ul>
          <li
            v-for="(crumb, index) in breadcrumbs"
            :key="index"
            class="cursor-pointer hover:text-primary"
            @click="navigateBreadcrumb(index)"
          >
            {{ crumb.name }}
          </li>
        </ul>
      </div>
    </div>

    <!-- 内容区域 -->
    <div v-if="loading" class="flex-1 flex justify-center items-center">
      <span class="loading loading-spinner loading-lg"></span>
    </div>

    <div v-else class="flex-1 overflow-y-auto">
      <!-- 文件夹列表 -->
      <div v-if="showFolders && folders.length > 0" class="mb-4">
        <h3 class="text-sm font-medium text-gray-600 dark:text-gray-400 mb-2 flex items-center">
          <span class="mr-2">📁</span> 文件夹
        </h3>
        <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
          <div
            v-for="folder in folders"
            :key="folder.id"
            class="relative flex items-center gap-3 p-3 bg-base-200 border-2 rounded-lg cursor-pointer transition-colors"
            :class="
              selectedFolders.includes(folder.id)
                ? 'border-primary'
                : 'border-transparent hover:border-base-300'
            "
          >
            <div class="flex-none">
              <input
                type="checkbox"
                class="checkbox checkbox-primary"
                :checked="
                  selectedFolders.includes(folder.id) || props.excludeFolderIds.includes(folder.id)
                "
                :disabled="props.excludeFolderIds.includes(folder.id)"
                @click.stop="toggleFolderSelection(folder.id)"
              />
            </div>
            <div class="flex-1 flex items-center gap-3" @click="enterFolder(folder)">
              <div class="text-2xl">📁</div>
              <div class="flex-1">
                <h4 class="font-medium text-sm">{{ folder.name }}</h4>
                <p class="text-xs text-base-content/60">
                  {{ new Date(folder.updated_at).toLocaleDateString() }}
                </p>
              </div>
              <div class="text-base-content/40">→</div>
            </div>
          </div>
        </div>
      </div>
      <!-- 文件夹底部：分页和操作 -->
      <div class="mt-4 pt-4 border-t border-base-200 space-y-3">
        <!-- 分页 -->
        <div v-if="showFolders && totalFoldersPages > 1" class="flex justify-center">
          <div class="join">
            <button
              class="join-item btn btn-sm"
              :disabled="currentFolderPage === 1"
              @click="changeFolderPage(currentFolderPage - 1)"
            >
              «
            </button>
            <button class="join-item btn btn-sm">
              Page {{ currentFolderPage }} / {{ totalFoldersPages || 1 }}
            </button>
            <button
              class="join-item btn btn-sm"
              :disabled="currentFolderPage >= totalFoldersPages"
              @click="changeFolderPage(currentFolderPage + 1)"
            >
              »
            </button>
          </div>
        </div>
      </div>

      <!-- 文件列表 -->
      <div v-if="showFiles && files.length > 0">
        <h3
          v-if="showFolders"
          class="text-sm font-medium text-gray-600 dark:text-gray-400 mb-2 flex items-center"
        >
          <span class="mr-2">📄</span> 文件
        </h3>
        <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
          <div
            v-for="file in files"
            :key="file.id"
            class="card bg-base-200 border-2 cursor-pointer relative h-32"
            :class="
              selectedFiles.includes(file.id)
                ? 'border-primary'
                : 'border-transparent hover:border-base-300'
            "
            @click="toggleFileSelection(file.id)"
          >
            <div
              v-if="props.excludeFileIds.includes(file.id)"
              class="absolute inset-0 bg-base-300/50 cursor-not-allowed z-10 flex items-center justify-center rounded-lg"
            >
              <span class="badge">已关联</span>
            </div>

            <figure class="h-20 flex items-center justify-center bg-base-300 overflow-hidden">
              <img
                v-if="isImage(file.mime_type)"
                :src="file.preview_url"
                class="w-full h-full object-cover opacity-80"
              />
              <span v-else class="text-3xl">{{ getFileIcon(file.mime_type) }}</span>
            </figure>
            <div class="p-2 text-xs truncate font-medium text-center">
              {{ file.filename }}
            </div>

            <!-- v-if="selectedFiles.includes(file.id)" -->
            <div class="absolute top-2 left-2">
              <input
                type="checkbox"
                class="checkbox checkbox-primary"
                :checked="selectedFiles.includes(file.id) || props.excludeFileIds.includes(file.id)"
                :disabled="props.excludeFolderIds.includes(file.id)"
              />
              <!-- @click.stop="toggleFileSelection(file.id)" -->
            </div>
          </div>
        </div>
      </div>

      <!-- 空状态 -->
      <div
        v-if="folders.length === 0 && files.length === 0"
        class="text-center py-12 text-base-content/50"
      >
        <svg
          class="w-16 h-16 mx-auto mb-4 text-gray-300"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"
          ></path>
        </svg>
        <p>{{ currentFolderId ? '此文件夹为空' : '未找到内容' }}</p>
      </div>
    </div>

    <!-- 底部：分页和操作 -->
    <div class="mt-4 pt-4 border-t border-base-200 space-y-3">
      <!-- 分页 -->
      <div v-if="showFiles && totalFilesPages > 1" class="flex justify-center">
        <div class="join">
          <button
            class="join-item btn btn-sm"
            :disabled="currentFilePage === 1"
            @click="changeFilePage(currentFilePage - 1)"
          >
            «
          </button>
          <button class="join-item btn btn-sm">
            Page {{ currentFilePage }} / {{ totalFilesPages || 1 }}
          </button>
          <button
            class="join-item btn btn-sm"
            :disabled="currentFilePage >= totalFilesPages"
            @click="changeFilePage(currentFilePage + 1)"
          >
            »
          </button>
        </div>
      </div>
    </div>

    <!-- 操作按钮 -->
    <div class="flex justify-between items-center">
      <div class="text-sm text-base-content/70">
        已选择:
        <span v-if="showFiles" class="ml-1">{{ selectedFiles.length }} 个文件</span>
        <span v-if="showFiles && showFolders">, </span>
        <span v-if="showFolders">{{ selectedFolders.length }} 个文件夹</span>
      </div>
      <div class="flex gap-2">
        <button class="btn btn-ghost btn-sm" @click="$emit('cancel')">取消</button>
        <button
          class="btn btn-primary btn-sm"
          :disabled="totalSelected === 0"
          @click="handleConfirm"
        >
          确认 ({{ totalSelected }})
        </button>
      </div>
    </div>
  </div>
</template>
