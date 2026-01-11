<script setup>
import { ref, watch, computed } from 'vue'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import fileService from '../api/fileService'
import folderService from '../api/folderService'
import noteService from '../api/noteService'
import { formatDate } from '@/utils/format'
import { getFileIcon, getFileTypeColor } from '@/utils/file'

const props = defineProps({
  isOpen: {
    type: Boolean,
    default: false,
  },
  item: {
    type: Object,
    default: null,
  },
  itemType: {
    type: String,
    default: 'file', // 'file' or 'folder'
    validator: (value) => ['file', 'folder'].includes(value),
  },
})

const emit = defineEmits(['close', 'note-created'])

const notes = ref([])
const selectedNote = ref(null)
const loading = ref(false)
const isEditing = ref(false)
const editingNote = ref({
  id: null,
  title: '',
  content: '',
})

const loadNotes = async () => {
  if (!props.item?.id) return

  loading.value = true
  try {
    let response
    if (props.itemType === 'folder') {
      response = await noteService.getNotesByFolderId(props.item.id)
      notes.value = response.data || []
    } else {
      response = await noteService.getNotesByFileId(props.item.id)
      notes.value = response.data || []
    }
  } catch (error) {
    console.error('Failed to load notes', error)
  } finally {
    loading.value = false
  }
}

const startNewNote = () => {
  isEditing.value = true
  editingNote.value = {
    id: null,
    title: '',
    content: '',
  }
  selectedNote.value = null
}

const editNote = (note) => {
  isEditing.value = true
  editingNote.value = {
    id: note.id,
    title: note.title || '',
    content: note.content || '',
  }
}

const cancelEdit = () => {
  isEditing.value = false
  editingNote.value = {
    id: null,
    title: '',
    content: '',
  }
}

const saveNote = async () => {
  if (!editingNote.value.content.trim()) {
    alert('笔记内容不能为空')
    return
  }

  try {
    if (editingNote.value.id) {
      // 更新现有笔记
      await noteService.updateNote(editingNote.value.id, {
        title: editingNote.value.title,
        content: editingNote.value.content,
      })
    } else {
      // 创建新笔记并关联
      const newNote = await noteService.createNote({
        title: editingNote.value.title,
        content: editingNote.value.content,
      })

      // 关联笔记
      if (props.itemType === 'folder') {
        await noteService.attachFolders(newNote.id, [props.item.id])
      } else if (props.itemType === 'file') {
        await noteService.attachFiles(newNote.id, [props.item.id])
      }

      emit('note-created')
    }

    isEditing.value = false
    editingNote.value = { id: null, title: '', content: '' }
    await loadNotes()
  } catch (error) {
    console.error('Failed to save note', error)
    alert('保存失败，请重试')
  }
}

const selectNote = (note) => {
  if (isEditing.value) return
  selectedNote.value = note
}

const renderedContent = computed(() => {
  if (!selectedNote.value?.content) return '暂无内容'
  const rawHtml = marked.parse(selectedNote.value.content)
  return DOMPurify.sanitize(rawHtml)
})

const detachNote = async (noteId) => {
  if (!confirm('确定要取消此笔记的关联吗？（笔记本身不会被删除）')) return

  try {
    if (props.itemType === 'folder') {
      await noteService.detachFolders(noteId, [props.item.id])
    } else {
      await noteService.detachFiles(noteId, [props.item.id])
    }

    await loadNotes()
    if (selectedNote.value?.id === noteId) {
      selectedNote.value = null
    }
    emit('note-created')
  } catch (error) {
    console.error('Failed to detach note', error)
  }
}

const deleteNote = async (noteId) => {
  if (!confirm('确定要永久删除这条笔记吗？此操作无法撤销！')) return

  try {
    await noteService.deleteNote(noteId)
    await loadNotes()
    if (selectedNote.value?.id === noteId) {
      selectedNote.value = null
    }
    emit('note-created')
  } catch (error) {
    console.error('Failed to delete note', error)
  }
}

watch(
  () => props.isOpen,
  (newVal) => {
    if (newVal) {
      loadNotes()
      isEditing.value = false
      selectedNote.value = null
      editingNote.value = { id: null, title: '', content: '' }
    } else {
      notes.value = []
      selectedNote.value = null
      isEditing.value = false
    }
  },
)

watch(
  () => props.item,
  () => {
    if (props.isOpen) {
      loadNotes()
    }
  },
)
</script>

<template>
  <div
    v-if="isOpen"
    class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4"
    @click.self="$emit('close')"
  >
    <div
      class="bg-white dark:bg-gray-900 rounded-2xl shadow-2xl max-w-4xl w-full h-[90vh] flex flex-col overflow-hidden"
    >
      <!-- 头部 -->
      <div
        class="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700"
      >
        <div class="flex items-center gap-3">
          <div
            v-if="itemType === 'folder'"
            class="w-10 h-10 rounded-full bg-yellow-100 dark:bg-yellow-900 flex items-center justify-center text-lg"
          >
            📁
          </div>
          <div
            v-else
            :class="`w-10 h-10 rounded-full flex items-center justify-center text-lg ${getFileTypeColor(item?.mime_type)}`"
          >
            {{ getFileIcon(item?.mime_type) }}
          </div>
          <div>
            <h2 class="text-xl font-semibold text-gray-900 dark:text-gray-100">
              {{ isEditing ? (editingNote?.id ? '编辑笔记' : '新建笔记') : '笔记管理' }}
            </h2>
            <p class="text-sm text-gray-500">
              {{ itemType === 'folder' ? item?.name : item?.filename }}
            </p>
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
      <div class="flex-1 overflow-hidden flex">
        <!-- 左侧：笔记列表 -->
        <div class="w-1/3 border-r border-gray-200 dark:border-gray-700 flex flex-col">
          <div class="p-4 border-b border-gray-200 dark:border-gray-700">
            <button @click="startNewNote" class="w-full btn btn-primary btn-sm">
              <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M12 4v16m8-8H4"
                ></path>
              </svg>
              新建笔记
            </button>
          </div>

          <div class="flex-1 overflow-y-auto">
            <div v-if="loading" class="flex justify-center p-6">
              <span class="loading loading-spinner loading-md"></span>
            </div>

            <div v-else-if="notes.length === 0" class="p-6 text-center text-gray-500">
              <svg
                class="w-12 h-12 mx-auto mb-3 text-gray-300"
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
              <p class="text-sm">暂无笔记</p>
              <p class="text-xs mt-2">点击上方按钮创建新笔记</p>
            </div>

            <div v-else class="space-y-2 p-4">
              <div
                v-for="note in notes"
                :key="note.id"
                :class="[
                  'p-3 rounded-lg border cursor-pointer transition-colors',
                  selectedNote?.id === note.id
                    ? 'bg-blue-50 border-blue-200 dark:bg-blue-900/20 dark:border-blue-700'
                    : 'bg-gray-50 border-gray-200 hover:bg-gray-100 dark:bg-gray-800 dark:border-gray-700 dark:hover:bg-gray-700',
                ]"
                @click="selectNote(note)"
              >
                <h4 class="font-medium text-sm text-gray-900 dark:text-gray-100 mb-1 line-clamp-1">
                  {{ note.title || '无标题' }}
                </h4>
                <p class="text-xs text-gray-500 line-clamp-2">
                  {{ note.content }}
                </p>
                <div class="flex items-center justify-between mt-2">
                  <span class="text-xs text-gray-400">
                    {{ formatDate(note.updated_at) }}
                  </span>
                  <div class="flex gap-1">
                    <button
                      @click.stop="editNote(note)"
                      class="btn btn-xs btn-ghost text-gray-400 hover:text-blue-500"
                      title="编辑"
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
                      @click.stop="detachNote(note.id)"
                      class="btn btn-xs btn-ghost text-gray-400 hover:text-orange-500"
                      title="取消关联"
                    >
                      <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path
                          stroke-linecap="round"
                          stroke-linejoin="round"
                          stroke-width="2"
                          d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21"
                        ></path>
                      </svg>
                    </button>
                    <button
                      @click.stop="deleteNote(note.id)"
                      class="btn btn-xs btn-ghost text-gray-400 hover:text-red-500"
                      title="删除"
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
        </div>

        <!-- 右侧：笔记内容/编辑器 -->
        <div class="flex-1 flex flex-col">
          <!-- 编辑模式 -->
          <div v-if="isEditing" class="flex-1 flex flex-col">
            <div class="p-4 border-b border-gray-200 dark:border-gray-700">
              <input
                v-model="editingNote.title"
                placeholder="笔记标题..."
                class="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-xl text-lg font-medium bg-transparent focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900 dark:text-gray-100 placeholder-gray-400"
              />
            </div>
            <div class="flex-1 p-4">
              <textarea
                v-model="editingNote.content"
                placeholder="输入笔记内容..."
                class="w-full h-full resize-none border border-gray-300 dark:border-gray-600 rounded-xl p-4 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900 dark:text-gray-100 bg-transparent placeholder-gray-400"
              ></textarea>
            </div>
            <div class="p-4 border-t border-gray-200 dark:border-gray-700 flex justify-end gap-2">
              <button @click="cancelEdit" class="btn btn-ghost">取消</button>
              <button @click="saveNote" class="btn btn-primary">
                {{ editingNote.id ? '保存' : '创建并关联' }}
              </button>
            </div>
          </div>

          <!-- 查看模式 -->
          <div v-else-if="selectedNote" class="flex-1 flex flex-col overflow-hidden">
            <div class="p-6 border-b border-gray-200 dark:border-gray-700">
              <h3 class="text-2xl font-semibold text-gray-900 dark:text-gray-100">
                {{ selectedNote.title || '无标题' }}
              </h3>
              <div class="flex flex-wrap gap-4 text-sm text-gray-600 dark:text-gray-400 mt-2">
                <div class="flex items-center gap-2">
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
                    />
                  </svg>
                  <span>创建于 {{ formatDate(selectedNote.created_at) }}</span>
                </div>
                <div class="flex items-center gap-2">
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                    />
                  </svg>
                  <span>更新于 {{ formatDate(selectedNote.updated_at) }}</span>
                </div>
              </div>
            </div>
            <div class="flex-1 overflow-y-auto p-6">
              <div class="prose dark:prose-invert max-w-none">
                <div v-html="renderedContent"></div>
              </div>
            </div>
          </div>

          <!-- 空状态 -->
          <div v-else class="flex-1 flex items-center justify-center text-gray-400">
            <div class="text-center">
              <svg
                class="w-20 h-20 mx-auto mb-4 text-gray-300"
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
              <p class="text-lg">选择或创建一条笔记</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
