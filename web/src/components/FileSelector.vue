<script setup>
import { ref, onMounted, watch } from 'vue'
import fileService from '../api/fileService'
import { getFileIcon } from '@/utils/file'

const props = defineProps({
  excludeIds: {
    type: Array,
    default: () => [],
  },
})

const emit = defineEmits(['select', 'cancel'])

const files = ref([])
const loading = ref(false)
const selectedFiles = ref([])

// Pagination and Search state
const searchQuery = ref('')
const currentPage = ref(1)
const pageSize = ref(12)
const total = ref(0)
const totalPages = ref(0)

const loadFiles = async () => {
  loading.value = true
  try {
    const params = {
      page: currentPage.value,
      page_size: pageSize.value,
      q: searchQuery.value || undefined,
    }
    const response = await fileService.getFiles(params)
    files.value = response.data
    total.value = response.total
    totalPages.value = response.total_pages
  } catch (error) {
    console.error('Failed to load files', error)
  } finally {
    loading.value = false
  }
}

let searchTimeout
const handleSearch = () => {
  if (searchTimeout) clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    currentPage.value = 1
    loadFiles()
  }, 300)
}

const changePage = (page) => {
  if (page < 1 || page > totalPages.value) return
  currentPage.value = page
  loadFiles()
}

const toggleSelection = (fileId) => {
  if (selectedFiles.value.includes(fileId)) {
    selectedFiles.value = selectedFiles.value.filter((id) => id !== fileId)
  } else {
    selectedFiles.value.push(fileId)
  }
}

const handleConfirm = () => {
  emit('select', selectedFiles.value)
}

const isImage = (mimeType) => mimeType.startsWith('image/')

watch(searchQuery, handleSearch)

onMounted(() => {
  loadFiles()
})
</script>

<template>
  <div class="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
    <div class="bg-base-100 p-6 rounded-box shadow-xl w-[90%] max-w-3xl h-[80vh] flex flex-col">
      <div class="flex justify-between items-center mb-4">
        <h3 class="font-bold text-lg">关联文件</h3>
        <div class="form-control">
          <input
            type="text"
            placeholder="搜索文件..."
            class="input input-bordered input-sm w-full max-w-xs"
            v-model="searchQuery"
          />
        </div>
      </div>

      <div v-if="loading" class="flex-1 flex justify-center items-center">
        <span class="loading loading-spinner"></span>
      </div>

      <div
        v-else
        class="flex-1 overflow-y-auto grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4 p-2 content-start"
      >
        <div
          v-for="file in files"
          :key="file.id"
          class="card bg-base-200 border-2 cursor-pointer relative h-32"
          :class="
            selectedFiles.includes(file.id)
              ? 'border-primary'
              : 'border-transparent hover:border-base-300'
          "
          @click="toggleSelection(file.id)"
        >
          <div
            v-if="props.excludeIds.includes(file.id)"
            class="absolute inset-0 bg-base-300/50 cursor-not-allowed z-10 flex items-center justify-center"
          >
            <span class="badge">已关联</span>
          </div>

          <figure class="h-20 flex items-center justify-center bg-base-300 overflow-hidden">
            <img
              v-if="isImage(file.mime_type)"
              :src="`${file.preview_url}`"
              class="w-full h-full object-cover opacity-80"
            />
            <span v-else class="text-3xl">{{ getFileIcon(file.mime_type) }}</span>
          </figure>
          <div class="p-2 text-xs truncate font-medium text-center">
            {{ file.filename }}
          </div>

          <div
            v-if="selectedFiles.includes(file.id)"
            class="absolute top-2 right-2 badge badge-primary"
          >
            ✓
          </div>
        </div>

        <div v-if="files.length === 0" class="col-span-full text-center py-10 text-base-content/50">
          未找到文件
        </div>
      </div>

      <!-- Pagination -->
      <div class="flex justify-between items-center mt-4 pt-2 border-t border-base-200">
        <div class="text-sm text-base-content/70">共 {{ total }} 个文件</div>
        <div class="join">
          <button
            class="join-item btn btn-sm"
            :disabled="currentPage === 1"
            @click="changePage(currentPage - 1)"
          >
            «
          </button>
          <button class="join-item btn btn-sm">
            Page {{ currentPage }} / {{ totalPages || 1 }}
          </button>
          <button
            class="join-item btn btn-sm"
            :disabled="currentPage >= totalPages"
            @click="changePage(currentPage + 1)"
          >
            »
          </button>
        </div>
        <div class="flex gap-2">
          <button class="btn btn-ghost btn-sm" @click="$emit('cancel')">取消</button>
          <button
            class="btn btn-primary btn-sm"
            :disabled="selectedFiles.length === 0"
            @click="handleConfirm"
          >
            确认 ({{ selectedFiles.length }})
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
