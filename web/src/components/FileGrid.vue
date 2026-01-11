<script setup>
import { ref, watch } from 'vue'
import { formatDate, formatSize } from '@/utils/format'
import { getFileIcon, getFileTypeColor } from '@/utils/file'

const props = defineProps({
  files: {
    type: Array,
    required: true,
    default: () => [],
  },
  folders: {
    type: Array,
    default: () => [],
  },
  selectionMode: {
    type: Boolean,
    default: false,
  },
  selectedFiles: {
    type: Array,
    default: () => [],
  },
  selectedFolders: {
    type: Array,
    default: () => [],
  },
})

const emit = defineEmits([
  'delete-file',
  'preview-file',
  'manage-notes',
  'open-folder',
  'delete-folder',
  'edit-folder',
  'rename-file',
  'selection-change',
  'view-details',
])

const localSelectedFiles = ref([...props.selectedFiles])
const localSelectedFolders = ref([...props.selectedFolders])

watch(
  () => props.selectedFiles,
  (newVal) => {
    localSelectedFiles.value = [...newVal]
  },
)

watch(
  () => props.selectedFolders,
  (newVal) => {
    localSelectedFolders.value = [...newVal]
  },
)

const toggleFileSelection = (fileId) => {
  if (localSelectedFiles.value.includes(fileId)) {
    localSelectedFiles.value = localSelectedFiles.value.filter((id) => id !== fileId)
  } else {
    localSelectedFiles.value.push(fileId)
  }
  emitSelection()
}

const toggleFolderSelection = (folderId) => {
  if (localSelectedFolders.value.includes(folderId)) {
    localSelectedFolders.value = localSelectedFolders.value.filter((id) => id !== folderId)
  } else {
    localSelectedFolders.value.push(folderId)
  }
  emitSelection()
}

const emitSelection = () => {
  emit('selection-change', {
    files: localSelectedFiles.value,
    folders: localSelectedFolders.value,
  })
}

const hoveredFile = ref(null)
const hoveredFolder = ref(null)

const isImage = (mimeType) => mimeType.startsWith('image/')
</script>

<template>
  <div>
    <!-- Folders Section -->
    <div v-if="folders.length > 0" class="mb-8">
      <h3 class="text-lg font-medium text-gray-700 dark:text-gray-200 mb-4 flex items-center">
        <span class="mr-2">📁</span> Folders ({{ folders.length }})
      </h3>

      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        <div
          v-for="folder in folders"
          :key="folder.id"
          class="relative group bg-white dark:bg-gray-800 rounded-2xl shadow-lg hover:shadow-xl transition-all duration-300 overflow-hidden border border-gray-100 dark:border-gray-700"
          @click="$emit('open-folder', folder)"
          @mouseenter="hoveredFolder = folder.id"
          @mouseleave="hoveredFolder = null"
        >
          <div class="absolute top-2 left-2 z-10" v-if="selectionMode">
            <input
              type="checkbox"
              :checked="localSelectedFolders.includes(folder.id)"
              @click.stop="toggleFolderSelection(folder.id)"
              class="checkbox checkbox-sm checkbox-primary"
            />
          </div>
          <div
            class="relative h-48 bg-linear-to-br from-gray-50 to-gray-100 dark:from-gray-700 dark:to-gray-800 flex items-center justify-center overflow-hidden cursor-pointer group-hover:scale-105 transition-transform duration-300"
            @click.stop="$emit('open-folder', folder)"
          >
            <!-- 文件夹图标 -->
            <div class="flex flex-col items-center justify-center p-4">
              <div
                class="w-16 h-16 rounded-full flex items-center justify-center text-yellow-400 text-5xl"
              >
                📁
              </div>
            </div>
          </div>

          <!-- 文件信息 -->
          <div class="p-4 space-y-3">
            <div class="flex items-center justify-between">
              <h3
                class="font-medium text-gray-900 dark:text-gray-100 text-sm leading-tight line-clamp-2 flex-1 mr-2"
                :title="folder.name"
              >
                {{ folder.name }}
              </h3>
              <button
                @click.stop="$emit('manage-notes', folder, 'folder')"
                class="btn btn-xs btn-outline text-gray-400 hover:text-blue-500"
                :class="{ 'text-blue-500': folder.notes_count > 0 }"
                :title="`管理笔记 (${folder.notes_count || 0})`"
              >
                📝
                <span v-if="folder.notes_count > 0" class="text-xs">{{ folder.notes_count }}</span>
              </button>
            </div>
            <!-- 操作按钮 -->
            <div
              class="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400 gap-2 pt-2 border-t border-gray-100 dark:border-gray-700"
            >
              <div class="flex-1">
                <button
                  class="btn btn-xs btn-ghost text-gray-500 hover:text-blue-600"
                  @click.stop="$emit('edit-folder', folder)"
                  title="重命名"
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
                <button
                  class="btn btn-xs btn-ghost text-red-500 hover:text-red-600"
                  @click.stop="$emit('delete-folder', folder)"
                >
                  <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                    ></path>
                  </svg>
                </button>
              </div>
              <span>{{ formatDate(folder.created_at) }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Files Section -->
    <div v-if="files.length > 0">
      <h3 class="text-lg font-medium text-gray-700 dark:text-gray-200 mb-4 flex items-center">
        <span class="mr-2">📄</span> Files ({{ files.length }})
      </h3>
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        <div
          v-for="file in files"
          :key="file.id"
          class="relative group bg-white dark:bg-gray-800 rounded-2xl shadow-lg hover:shadow-xl transition-all duration-300 overflow-hidden border border-gray-100 dark:border-gray-700"
          @mouseenter="hoveredFile = file.id"
          @mouseleave="hoveredFile = null"
        >
          <div class="absolute top-2 left-2 z-10" v-if="selectionMode">
            <input
              type="checkbox"
              :checked="localSelectedFiles.includes(file.id)"
              @click.stop="toggleFileSelection(file.id)"
              class="checkbox checkbox-sm checkbox-primary"
            />
          </div>
          <!-- 文件预览区域 -->
          <div
            class="relative h-48 bg-linear-to-br from-gray-50 to-gray-100 dark:from-gray-700 dark:to-gray-800 flex items-center justify-center overflow-hidden cursor-pointer group-hover:scale-105 transition-transform duration-300"
            @click="$emit('preview-file', file)"
          >
            <!-- 图片预览 -->
            <img
              v-if="isImage(file.mime_type)"
              :src="`${file.preview_url}`"
              :alt="file.filename"
              class="w-full h-full object-cover"
            />
            <!-- 文件类型图标 -->
            <div v-else class="flex flex-col items-center justify-center p-4">
              <div
                :class="`w-24 h-24 rounded-full flex items-center justify-center text-5xl ${getFileTypeColor(file.mime_type)}`"
              >
                {{ getFileIcon(file.mime_type) }}
              </div>
              <span class="mt-2 text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wide">{{
                file.mime_type.split('/')[1]
              }}</span>
            </div>

            <!-- 悬浮操作按钮 -->
            <div
              v-if="hoveredFile === file.id"
              class="absolute inset-0 bg-black/20 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity duration-200"
            >
              <div class="flex gap-2">
                <button
                  @click.stop="$emit('preview-file', file)"
                  class="btn btn-sm btn-circle bg-white/90 hover:bg-white text-gray-700 border-0 shadow-lg"
                  title="预览文件"
                >
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                    ></path>
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
                    ></path>
                  </svg>
                </button>
              </div>
            </div>
          </div>

          <!-- 文件信息 -->
          <div class="p-4 space-y-3">
            <div class="flex items-center justify-between">
              <h3
                class="font-medium text-gray-900 dark:text-gray-100 text-sm leading-tight line-clamp-2 flex-1 mr-2"
                :title="file.filename"
              >
                {{ file.filename }}
              </h3>
              <button
                @click="$emit('manage-notes', file, 'file')"
                class="btn btn-xs btn-outline text-gray-400 hover:text-blue-500"
                :class="{ 'text-blue-500': file.notes_count > 0 }"
                :title="`管理笔记 (${file.notes_count || 0})`"
              >
                📝
                <span v-if="file.notes_count > 0" class="text-xs">{{ file.notes_count }}</span>
              </button>
            </div>

            <div class="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
              <span>{{ formatSize(file.size) }}</span>
              <span>{{ formatDate(file.created_at) }}</span>
            </div>

            <!-- 操作按钮 -->
            <div class="flex gap-2 pt-2 border-t border-gray-100 dark:border-gray-700">
              <router-link
                :to="{ name: 'file-detail', params: { id: file.id } }"
                class="btn btn-xs btn-ghost text-gray-500 hover:text-blue-600"
                title="查看详情页"
              >
                <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
              </router-link>
              <button
                class="btn btn-xs btn-ghost text-gray-500 hover:text-purple-600"
                @click="$emit('view-details', file)"
                title="快速查看"
              >
                <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                  />
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
                  />
                </svg>
              </button>
              <button
                class="btn btn-xs btn-ghost text-gray-500 hover:text-blue-600"
                @click="$emit('rename-file', file)"
                title="重命名"
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
              <button
                class="btn btn-xs btn-ghost text-red-500 hover:text-red-600"
                @click="$emit('delete-file', file.id)"
              >
                <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                  ></path>
                </svg>
              </button>
              <a
                :href="`${file.download_url}`"
                target="_blank"
                download
                class="btn btn-xs btn-ghost flex-1 text-gray-600 hover:text-blue-600"
              >
                <svg class="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                  ></path>
                </svg>
                下载
              </a>
            </div>
          </div>
        </div>
      </div>
    </div>
    <div v-if="files.length === 0 && folders.length === 0" class="text-center py-12 text-gray-500">
      No files or folders found
    </div>
  </div>
</template>
