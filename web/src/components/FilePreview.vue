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

        <!-- PDF预览（pdf.js 分页懒加载） -->
        <div
          v-else-if="isPdf(file.mime_type)"
          class="h-full flex flex-col bg-gray-50 dark:bg-gray-900"
        >
          <div
            class="flex items-center justify-between px-4 py-2 border-b border-gray-200 dark:border-gray-700 text-sm text-gray-600 dark:text-gray-300"
          >
            <div>
              <span v-if="pdfLoading">加载 PDF...</span>
              <span v-else-if="pdfError">{{ pdfError }}</span>
              <span v-else>{{ pdfPages.length }} 页 · 下拉懒加载</span>
            </div>
            <div class="flex items-center gap-3 text-xs text-gray-500">
              <span>渲染完成后可放大/截图</span>
              <form class="flex items-center gap-2" @submit.prevent="jumpToPage">
                <input
                  v-model.number="pageInput"
                  type="number"
                  :min="1"
                  :max="pdfPages.length || 1"
                  class="input input-xs input-bordered w-20"
                  placeholder="页码"
                  :disabled="pdfLoading || !!pdfError"
                />
                <button
                  type="submit"
                  class="btn btn-xs"
                  :disabled="pdfLoading || !!pdfError || !pdfPages.length"
                >
                  跳转
                </button>
              </form>
            </div>
          </div>

          <div ref="pdfScrollEl" class="flex-1 overflow-auto px-4 py-4 space-y-4">
            <div
              v-for="page in pdfPages"
              :key="page.pageNumber"
              :data-page-number="page.pageNumber"
              class="relative bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700 p-2 flex justify-center"
              :ref="(el) => setPageRef(el, page.pageNumber)"
            >
              <canvas :ref="(el) => setCanvasRef(el, page.pageNumber)" class="max-w-full"></canvas>

              <div
                v-if="!page.rendered && !page.error"
                class="absolute inset-0 flex items-center justify-center gap-2 bg-white/70 dark:bg-gray-900/70 text-gray-500"
              >
                <span class="loading loading-spinner loading-sm"></span>
                <span>加载第 {{ page.pageNumber }} 页</span>
              </div>

              <div
                v-else-if="page.error"
                class="absolute inset-0 flex items-center justify-center text-red-500"
              >
                {{ page.error }}
              </div>
            </div>

            <div
              v-if="!pdfLoading && !pdfError && pdfPages.length === 0"
              class="text-center text-gray-500"
            >
              未找到可渲染的页面
            </div>
          </div>
        </div>

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
import { nextTick, onBeforeUnmount, ref, shallowRef, watch } from 'vue'
import * as pdfjsLib from 'pdfjs-dist'
import pdfjsWorker from 'pdfjs-dist/build/pdf.worker.min.mjs?url'
import { formatDate, formatSize } from '@/utils/format'
import { getFileIcon, getFileTypeColor } from '@/utils/file'

pdfjsLib.GlobalWorkerOptions.workerSrc = pdfjsWorker

const props = defineProps({
  file: {
    type: Object,
    default: null,
  },
})

defineEmits(['close', 'add-note'])

const textContent = ref('')
const pdfLoading = ref(false)
const pdfError = ref('')
const pdfPages = ref([])
const pdfScrollEl = ref(null)
const pdfDoc = shallowRef(null)
const observer = ref(null)
const pageRefs = new Map()
const canvasRefs = new Map()
const renderTasks = new Map()
const pageInput = ref(1)

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

const setPageRef = (el, pageNumber) => {
  if (el) {
    pageRefs.set(pageNumber, el)
  } else {
    pageRefs.delete(pageNumber)
  }
}

const setCanvasRef = (el, pageNumber) => {
  if (el) {
    canvasRefs.set(pageNumber, el)
  } else {
    canvasRefs.delete(pageNumber)
  }
}

const cleanupPdf = async () => {
  observer.value?.disconnect()
  observer.value = null

  renderTasks.forEach((task) => task?.cancel?.())
  renderTasks.clear()

  pageRefs.clear()
  canvasRefs.clear()
  pdfPages.value = []
  pageInput.value = 1

  if (pdfDoc.value) {
    try {
      await pdfDoc.value.destroy()
    } catch {
      /* ignore */
    }
    pdfDoc.value = null
  }

  pdfLoading.value = false
  pdfError.value = ''
}

const renderPage = async (pageNumber) => {
  const pageMeta = pdfPages.value.find((p) => p.pageNumber === pageNumber)
  if (!pdfDoc.value || !pageMeta || pageMeta.rendered || pageMeta.error) return
  if (renderTasks.has(pageNumber)) return

  const canvas = canvasRefs.get(pageNumber)
  const container = pageRefs.get(pageNumber)
  if (!canvas || !container) return

  try {
    const page = await pdfDoc.value.getPage(pageNumber)
    const unscaledViewport = page.getViewport({ scale: 1 })
    const containerWidth = Math.max(
      320,
      Math.min(1280, (pdfScrollEl.value?.clientWidth || unscaledViewport.width) - 16),
    )
    const scale = containerWidth / unscaledViewport.width
    const viewport = page.getViewport({ scale })

    const context = canvas.getContext('2d')
    canvas.height = viewport.height
    canvas.width = viewport.width

    const renderTask = page.render({ canvasContext: context, viewport })
    renderTasks.set(pageNumber, renderTask)
    await renderTask.promise
    pageMeta.rendered = true
  } catch (err) {
    console.error('PDF page render error', err)
    pageMeta.error = '页面渲染失败'
  } finally {
    renderTasks.delete(pageNumber)
  }
}

const setupObserver = () => {
  if (observer.value) observer.value.disconnect()
  if (!pdfScrollEl.value) return

  observer.value = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          const pageNumber = Number(entry.target.dataset.pageNumber)
          renderPage(pageNumber)
        }
      })
    },
    {
      root: pdfScrollEl.value,
      rootMargin: '400px 0px',
      threshold: 0.1,
    },
  )

  pageRefs.forEach((el) => observer.value.observe(el))
}

const jumpToPage = async () => {
  if (!pdfPages.value.length || !pdfScrollEl.value) return

  const totalPages = pdfPages.value.length
  const targetPage = Math.min(Math.max(Math.round(pageInput.value || 1), 1), totalPages)
  pageInput.value = targetPage

  await nextTick()
  await renderPage(targetPage)

  const targetEl = pageRefs.get(targetPage)
  if (targetEl) {
    targetEl.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }
}

const initPdf = async () => {
  if (!props.file) return

  pdfLoading.value = true
  pdfError.value = ''

  try {
    // 启用 HTTP Range，避免一次性拉全量
    const task = pdfjsLib.getDocument({
      url: props.file.preview_url,
      rangeChunkSize: 10 * 1024 * 1024, // 10 MB
      // 仅按 Range 分块，禁用流式全量拉取，避免浏览器触发二次完整下载
      disableStream: true,
      disableAutoFetch: true,
    })
    pdfDoc.value = await task.promise
    pdfPages.value = Array.from({ length: pdfDoc.value.numPages }, (_, idx) => ({
      pageNumber: idx + 1,
      rendered: false,
      error: '',
    }))
    pageInput.value = 1

    await nextTick()
    setupObserver()
    // 先渲染首页，提升首屏体验
    renderPage(1)
  } catch (err) {
    console.error('PDF load error', err)
    pdfError.value = 'PDF 加载失败'
  } finally {
    pdfLoading.value = false
  }
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
  async (newFile) => {
    textContent.value = ''
    await cleanupPdf()

    if (newFile) {
      if (isText(newFile.mime_type)) {
        loadTextContent()
      }
      if (isPdf(newFile.mime_type)) {
        initPdf()
      }
    }
  },
  { immediate: true },
)

onBeforeUnmount(() => {
  cleanupPdf()
})
</script>
