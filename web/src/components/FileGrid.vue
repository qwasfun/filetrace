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
  'add-note',
  'view-notes',
  'open-folder',
  'delete-folder',
  'edit-folder',
  'rename-file',
  'selection-change',
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
        <span class="mr-2">📁</span> Folders
      </h3>
      <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
        <div
          v-for="folder in folders"
          :key="folder.id"
          class="relative group bg-white dark:bg-gray-800 p-4 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 hover:shadow-md hover:border-blue-300 dark:hover:border-blue-500 transition-all cursor-pointer"
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
          <div class="flex flex-col items-center p-2">
            <div class="text-5xl mb-3 text-yellow-400">📁</div>
            <div
              class="text-sm font-medium text-gray-700 dark:text-gray-200 truncate w-full text-center"
            >
              {{ folder.name }}
            </div>
          </div>

          <!-- Folder Actions -->
          <div
            v-if="hoveredFolder === folder.id"
            class="absolute top-2 right-2 flex space-x-1"
            @click.stop
          >
            <button
              @click="$emit('edit-folder', folder)"
              class="p-1.5 bg-white dark:bg-gray-700 rounded-full shadow hover:bg-gray-100 dark:hover:bg-gray-600 text-gray-600 dark:text-gray-300"
              title="Rename"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                class="h-3 w-3"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
                />
              </svg>
            </button>
            <button
              @click="$emit('delete-folder', folder)"
              class="p-1.5 bg-white dark:bg-gray-700 rounded-full shadow hover:bg-red-50 dark:hover:bg-red-900/30 text-red-500"
              title="Delete"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                class="h-3 w-3"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Files Section -->
    <div v-if="files.length > 0">
      <h3
        v-if="files.length > 0"
        class="text-lg font-medium text-gray-700 dark:text-gray-200 mb-4 flex items-center"
      >
        <span class="mr-2">📄</span> Files
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
                :class="`w-16 h-16 rounded-full flex items-center justify-center text-2xl ${getFileTypeColor(file.mime_type)}`"
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
                <button
                  @click.stop="$emit('add-note', file)"
                  class="btn btn-sm btn-circle bg-blue-500 hover:bg-blue-600 text-white border-0 shadow-lg"
                  title="添加笔记"
                >
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M12 4v16m8-8H4"
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
                @click="$emit('view-notes', file)"
                class="btn btn-xs btn-outline text-gray-400 hover:text-blue-500"
                :class="{ 'text-blue-500': file.notes_count > 0 }"
                :title="`查看笔记 (${file.notes_count || 0})`"
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
