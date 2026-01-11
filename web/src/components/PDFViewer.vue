<script setup>
import { ref, watch, onBeforeUnmount, shallowRef, nextTick } from 'vue'
import * as pdfjsLib from 'pdfjs-dist'
import pdfjsWorker from 'pdfjs-dist/build/pdf.worker.min.mjs?url'

pdfjsLib.GlobalWorkerOptions.workerSrc = pdfjsWorker

const props = defineProps({
  url: {
    type: String,
    required: true,
  },
})

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
  if (!props.url) return

  pdfLoading.value = true
  pdfError.value = ''

  try {
    // 启用 HTTP Range，避免一次性拉全量
    const task = pdfjsLib.getDocument({
      url: props.url,
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

watch(
  () => props.url,
  async (newUrl) => {
    await cleanupPdf()
    if (newUrl) {
      initPdf()
    }
  },
  { immediate: true },
)

onBeforeUnmount(() => {
  cleanupPdf()
})
</script>

<template>
  <div class="h-full w-full flex flex-col bg-gray-50 dark:bg-gray-900">
    <!-- 工具栏 -->
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

    <!-- 页面容器 -->
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
</template>
