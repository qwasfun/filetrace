<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  url: {
    type: String,
    required: true,
  },
  maxLength: {
    type: Number,
    default: 10000,
  },
})

const textContent = ref('')
const loading = ref(false)
const error = ref('')

const loadTextContent = async () => {
  if (!props.url) return

  loading.value = true
  error.value = ''

  try {
    const response = await fetch(props.url)
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`)
    }
    const text = await response.text()
    textContent.value =
      text.length > props.maxLength
        ? text.substring(0, props.maxLength) + '\n\n...(文件内容过长，已截断)'
        : text
  } catch (err) {
    console.error('加载文本内容失败:', err)
    error.value = '无法加载文件内容'
    textContent.value = ''
  } finally {
    loading.value = false
  }
}

watch(
  () => props.url,
  async (newUrl) => {
    textContent.value = ''
    if (newUrl) {
      await loadTextContent()
    }
  },
  { immediate: true },
)
</script>

<template>
  <div
    class="h-full w-full bg-gray-50 dark:bg-gray-800 rounded-lg p-4 font-mono text-sm overflow-auto"
  >
    <!-- 加载中 -->
    <div v-if="loading" class="flex items-center justify-center py-8">
      <span class="loading loading-spinner loading-md"></span>
      <span class="ml-2 text-gray-600 dark:text-gray-400">加载中...</span>
    </div>

    <!-- 错误状态 -->
    <div v-else-if="error" class="flex flex-col items-center justify-center py-8 text-red-500">
      <svg class="w-12 h-12 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
        />
      </svg>
      <span>{{ error }}</span>
    </div>

    <!-- 文本内容 -->
    <pre
      v-else-if="textContent"
      class="text-gray-900 dark:text-gray-100 whitespace-pre-wrap break-words"
      >{{ textContent }}</pre
    >

    <!-- 空内容 -->
    <div v-else class="flex items-center justify-center py-8 text-gray-500">
      <span>文件内容为空</span>
    </div>
  </div>
</template>
