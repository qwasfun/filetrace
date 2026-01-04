<template>
  <div
    v-if="isOpen"
    class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4"
    @click.self="$emit('close')"
  >
    <div
      class="bg-white dark:bg-gray-900 rounded-2xl shadow-2xl max-w-4xl w-full max-h-[90vh] flex flex-col overflow-hidden"
    >
      <!-- 头部 -->
      <div
        class="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700"
      >
        <div class="flex items-center gap-3">
          <div
            class="w-10 h-10 rounded-full bg-yellow-100 dark:bg-yellow-900 flex items-center justify-center text-lg"
          >
            📁
          </div>
          <div>
            <h2 class="text-xl font-semibold text-gray-900 dark:text-gray-100">文件夹笔记</h2>
            <p class="text-sm text-gray-500">{{ folder?.name }}</p>
          </div>
        </div>
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

      <!-- 内容区域 -->
      <div class="flex-1 overflow-y-auto p-6">
        <div v-if="loading" class="flex justify-center p-6">
          <span class="loading loading-spinner loading-md"></span>
        </div>

        <div v-else>
          <!-- 笔记列表 -->
          <div v-if="notes.length > 0" class="space-y-4">
            <h3 class="text-lg font-medium text-gray-900 dark:text-gray-100 mb-4">
              关联的笔记 ({{ notes.length }})
            </h3>
            <div
              v-for="note in notes"
              :key="note.id"
              class="p-4 rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800"
            >
              <div class="flex items-start justify-between">
                <div class="flex-1">
                  <h4 class="font-medium text-gray-900 dark:text-gray-100 mb-2">
                    {{ note.title || '无标题' }}
                  </h4>
                  <p class="text-sm text-gray-600 dark:text-gray-400 line-clamp-3 mb-2">
                    {{ note.content }}
                  </p>
                  <span class="text-xs text-gray-400">
                    {{ formatDate(note.updated_at) }}
                  </span>
                </div>
                <button
                  @click="detachNote(note.id)"
                  class="btn btn-xs btn-ghost text-gray-400 hover:text-red-500"
                  title="取消关联"
                >
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
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
          </div>

          <div v-else class="text-center text-gray-500 py-12">
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
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
              ></path>
            </svg>
            <p class="text-sm">此文件夹还没有关联的笔记</p>
          </div>
        </div>
      </div>

      <!-- 底部操作栏 -->
      <div
        class="p-4 border-t border-gray-200 dark:border-gray-700 flex justify-between items-center"
      >
        <div class="text-sm text-gray-500">在笔记管理中添加笔记并关联到此文件夹</div>
        <button @click="$emit('close')" class="btn btn-sm">关闭</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import folderService from '../api/folderService'
import { formatDate } from '@/utils/format'

const props = defineProps({
  isOpen: {
    type: Boolean,
    default: false,
  },
  folder: {
    type: Object,
    default: null,
  },
})

const emit = defineEmits(['close', 'note-created'])

const notes = ref([])
const loading = ref(false)

const loadNotes = async () => {
  if (!props.folder?.id) return

  loading.value = true
  try {
    const response = await folderService.getFolderNotes(props.folder.id)
    notes.value = response.notes || []
  } catch (error) {
    console.error('Failed to load folder notes', error)
  } finally {
    loading.value = false
  }
}

const detachNote = async (noteId) => {
  if (!confirm('确定要取消此笔记与文件夹的关联吗？')) return

  try {
    await folderService.detachNotes(props.folder.id, [noteId])
    await loadNotes()
    emit('note-created')
  } catch (error) {
    console.error('Failed to detach note', error)
    alert('取消关联失败')
  }
}

watch(
  () => props.isOpen,
  (isOpen) => {
    if (isOpen && props.folder) {
      loadNotes()
    }
  },
)
</script>
