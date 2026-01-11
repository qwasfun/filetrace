<template>
  <div
    v-if="file"
    class="fixed inset-0 bg-black/80 z-50 flex items-center justify-center p-4"
    @click.self="$emit('close')"
  >
    <div
      class="bg-white dark:bg-gray-900 rounded-2xl shadow-2xl max-w-5xl max-h-[90vh] w-full h-full flex flex-col overflow-hidden"
    >
      <!-- 头部 -->
      <div
        class="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700"
      >
        <div class="flex items-center gap-3">
          <div
            :class="`w-10 h-10 rounded-full flex items-center justify-center text-lg ${getFileTypeColor(file.mime_type)}`"
          >
            {{ getFileIcon(file.mime_type) }}
          </div>
          <div>
            <h2 class="font-semibold text-gray-900 dark:text-gray-100">
              {{ file.filename }}
            </h2>
            <p class="text-sm text-gray-500">
              {{ formatSize(file.size) }} • {{ formatDate(file.created_at) }}
            </p>
          </div>
        </div>
        <div class="flex items-center gap-2">
          <button
            @click="$emit('add-note', file)"
            class="btn btn-sm btn-primary"
            title="为此文件添加笔记"
          >
            <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M12 4v16m8-8H4"
              ></path>
            </svg>
            添加笔记
          </button>
          <a :href="`${file.download_url}`" target="_blank" download class="btn btn-sm btn-outline">
            <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
              ></path>
            </svg>
            下载
          </a>
          <button @click="$emit('close')" class="btn btn-sm btn-circle btn-ghost">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M6 18L18 6M6 6l12 12"
              ></path>
            </svg>
          </button>
        </div>
      </div>

      <!-- 内容区域 -->
      <div class="flex-1 overflow-auto">
        <!-- 图片预览 -->
        <div
          v-if="isImage(file.mime_type)"
          class="flex items-center justify-center p-6 bg-gray-50 dark:bg-gray-800 h-full"
        >
          <img
            :src="`${file.preview_url}`"
            :alt="file.filename"
            class="max-w-full max-h-full object-contain rounded-lg shadow-lg"
          />
        </div>

        <!-- 视频预览 -->
        <div
          v-else-if="isVideo(file.mime_type)"
          class="flex items-center justify-center p-6 bg-black h-full"
        >
          <video
            :src="`${file.preview_url}`"
            controls
            class="max-w-full max-h-full rounded-lg shadow-lg"
          >
            您的浏览器不支持视频播放
          </video>
        </div>

        <!-- PDF预览 -->
        <PDFViewer v-else-if="isPdf(file.mime_type)" :url="file.preview_url" />

        <!-- 音频预览 -->
        <div v-else-if="isAudio(file.mime_type)" class="flex items-center justify-center p-8">
          <div class="w-full max-w-md">
            <div class="text-center mb-6">
              <div
                class="w-24 h-24 bg-purple-100 text-purple-600 rounded-full flex items-center justify-center text-4xl mx-auto mb-4"
              >
                🎵
              </div>
              <h3 class="font-medium text-gray-900 dark:text-gray-100">
                {{ file.filename }}
              </h3>
            </div>
            <audio :src="`${file.preview_url}`" controls class="w-full">
              您的浏览器不支持音频播放
            </audio>
          </div>
        </div>

        <!-- 文本文件预览 -->
        <div v-else-if="isText(file.mime_type)" class="p-4 h-full">
          <div
            class="bg-gray-50 dark:bg-gray-800 rounded-lg p-4 font-mono text-sm overflow-auto h-full"
          >
            <pre v-if="textContent">{{ textContent }}</pre>
            <div v-else class="flex items-center justify-center py-8">
              <span class="loading loading-spinner loading-md"></span>
              <span class="ml-2">加载中...</span>
            </div>
          </div>
        </div>

        <!-- 其他文件类型 -->
        <div v-else class="flex flex-col items-center justify-center p-12 text-center">
          <div
            :class="`w-24 h-24 rounded-full flex items-center justify-center text-4xl mb-6 ${getFileTypeColor(file.mime_type)}`"
          >
            {{ getFileIcon(file.mime_type) }}
          </div>
          <h3 class="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">
            {{ file.filename }}
          </h3>
          <p class="text-gray-500 dark:text-gray-400 mb-6">
            此文件类型 ({{ file.mime_type }}) 暂不支持预览
          </p>
          <a :href="`${file.download_url}`" target="_blank" download class="btn btn-primary">
            <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
              ></path>
            </svg>
            下载文件
          </a>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { formatDate, formatSize } from '@/utils/format'
import { getFileIcon, getFileTypeColor } from '@/utils/file'
import PDFViewer from './PDFViewer.vue'

const props = defineProps({
  file: {
    type: Object,
    default: null,
  },
})

defineEmits(['close', 'add-note'])

const textContent = ref('')

const isImage = (mimeType) => mimeType.startsWith('image/')
const isVideo = (mimeType) => mimeType.startsWith('video/')
const isPdf = (mimeType) => mimeType === 'application/pdf'
const isAudio = (mimeType) => mimeType.startsWith('audio/')
const isText = (mimeType) => {
  return (
    mimeType.startsWith('text/') ||
    ['application/json', 'application/javascript', 'application/xml'].includes(mimeType)
  )
}

// 加载文本内容
const loadTextContent = async () => {
  if (!props.file || !isText(props.file.mime_type)) return

  try {
    const response = await fetch(`${props.file.preview_url}`)
    const text = await response.text()
    textContent.value =
      text.length > 10000 ? text.substring(0, 10000) + '\n...(文件内容过长，已截断)' : text
  } catch {
    textContent.value = '无法加载文件内容'
  }
}

watch(
  () => props.file,
  (newFile) => {
    textContent.value = ''

    if (newFile && isText(newFile.mime_type)) {
      loadTextContent()
    }
  },
  { immediate: true },
)
</script>
