<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import noteService from '../../api/noteService.js'
import NoteEditor from '../../components/NoteEditor.vue'
import FilePreview from '../../components/FilePreview.vue'
import { formatDate, formatSize } from '@/utils/format'
import { getFileIcon, getFileTypeColor } from '@/utils/file'

const router = useRouter()

const notes = ref([])
const loading = ref(false)
const selectedNote = ref(null)
const isEditing = ref(false)
const isViewing = ref(false)

const previewFile = ref(null)
const showFilePreview = ref(false)

const currentPage = ref(1)
const pageSize = ref(10)
const totalNotes = ref(0)
const totalPages = ref(0)

const loadNotes = async () => {
  loading.value = true
  try {
    const response = await noteService.getNotes({
      page: currentPage.value,
      page_size: pageSize.value,
    })

    if ((response.data || []).length === 0 && currentPage.value > 1) {
      currentPage.value = 1
      return loadNotes()
    }

    notes.value = response.data
    totalNotes.value = response.total
    totalPages.value = response.total_pages
  } catch (error) {
    console.error('Failed to load notes', error)
  } finally {
    loading.value = false
  }
}

const handlePageChange = (page) => {
  currentPage.value = page
  loadNotes()
}

const handleCreate = () => {
  selectedNote.value = null
  isViewing.value = false
  isEditing.value = true
}

const handleView = (note) => {
  selectedNote.value = { ...note } // Clone to avoid direct mutation
  isViewing.value = true
  isEditing.value = false
}

const handleDetail = (note) => {
  // 跳转到独立的笔记详情页面
  router.push({ name: 'note-detail', params: { id: note.id } })
}

const handleEdit = (note) => {
  if (note) {
    selectedNote.value = { ...note }
  }
  isViewing.value = false
  isEditing.value = true
}

const handleSave = async (noteData) => {
  try {
    let savedNoteId
    if (selectedNote.value && selectedNote.value.id) {
      await noteService.updateNote(selectedNote.value.id, noteData)
      savedNoteId = selectedNote.value.id
    } else {
      const response = await noteService.createNote(noteData)
      savedNoteId = response.id
    }

    // 重新加载笔记列表
    await loadNotes()

    // 找到刚保存的笔记并显示预览
    const savedNote = notes.value.find((note) => note.id === savedNoteId)
    if (savedNote) {
      selectedNote.value = { ...savedNote }
      isEditing.value = false
      isViewing.value = true
    }
  } catch (error) {
    console.error('Failed to save note', error)
  }
}

const handleDelete = async (id) => {
  if (!confirm('Are you sure you want to delete this note?')) return
  try {
    await noteService.deleteNote(id)
    await loadNotes()
    if (selectedNote.value && selectedNote.value.id === id) {
      isViewing.value = false
      selectedNote.value = null
    }
  } catch (error) {
    console.error('Failed to delete note', error)
  }
}

const handleCancel = () => {
  isEditing.value = false
  if (!selectedNote.value?.id) {
    isViewing.value = false
    selectedNote.value = null
  } else {
    isViewing.value = true
  }
}

const handleFileClick = (file) => {
  previewFile.value = file
  showFilePreview.value = true
}

const handleClosePreview = () => {
  showFilePreview.value = false
  previewFile.value = null
}

const renderedContent = computed(() => {
  if (!selectedNote.value?.content) return '暂无内容'
  const rawHtml = marked.parse(selectedNote.value.content)
  return DOMPurify.sanitize(rawHtml)
})

onMounted(async () => {
  await loadNotes()
})
</script>

<template>
  <div class="bg-gray-50 dark:bg-gray-900 h-[calc(100vh-64px)]">
    <div class="container mx-auto px-4 py-6 h-full flex flex-col md:flex-row">
      <!-- Notes List Sidebar -->
      <div
        class="w-full md:w-1/3 flex-col h-full"
        :class="[isEditing || isViewing ? 'hidden md:flex' : 'flex']"
      >
        <div class="flex justify-between items-center mb-4 px-2">
          <div>
            <h1 class="text-3xl font-bold">📝 笔记管理</h1>
            <p class="text-gray-600 dark:text-gray-400 mt-1">管理您的笔记</p>
          </div>
          <button class="btn btn-primary btn-sm" @click="handleCreate">新建笔记</button>
        </div>

        <div v-if="loading && notes.length === 0" class="flex justify-center p-4">
          <span class="loading loading-spinner"></span>
        </div>

        <div v-else class="flex-1 overflow-y-auto space-y-2 p-2">
          <div
            v-for="note in notes"
            :key="note.id"
            class="card bg-base-100 shadow-md hover:bg-base-200 cursor-pointer transition-colors"
            :class="{ 'ring-2 ring-primary': selectedNote?.id === note.id }"
            @click="handleView(note)"
          >
            <div class="card-body p-4">
              <h3 class="font-bold truncate">{{ note.title || 'Untitled Note' }}</h3>
              <p class="text-xs text-base-content/60 line-clamp-2">{{ note.content }}</p>
              <div class="flex justify-between items-center mt-2">
                <span class="flex-1 text-xs text-base-content/40">{{
                  formatDate(note.updated_at)
                }}</span>
                <div class="flex gap-1">
                  <span class="badge" v-if="note.folders && note.folders.length > 0"
                    >📁 {{ note.folders.length }}</span
                  >
                  <span class="badge" v-if="note.files && note.files.length > 0"
                    >📎 {{ note.files.length }}</span
                  >
                </div>
              </div>
            </div>
          </div>

          <div v-if="notes.length === 0 && !loading" class="text-center text-base-content/50 py-8">
            No notes found.
          </div>
        </div>

        <div class="p-2 border-t border-base-200" v-if="totalPages > 1">
          <div class="join flex justify-center">
            <button
              class="join-item btn btn-sm"
              :disabled="currentPage === 1"
              @click="handlePageChange(currentPage - 1)"
            >
              «
            </button>
            <button class="join-item btn btn-sm">Page {{ currentPage }}</button>
            <button
              class="join-item btn btn-sm"
              :disabled="currentPage === totalPages"
              @click="handlePageChange(currentPage + 1)"
            >
              »
            </button>
          </div>
        </div>
      </div>

      <!-- main Content / Editor / Preview -->
      <div
        class="flex-1 h-full md:ml-4 pb-2"
        :class="{ 'hidden md:block': !isEditing && !isViewing }"
      >
        <!-- Editor -->
        <NoteEditor
          v-if="isEditing"
          :note="selectedNote"
          @save="handleSave"
          @cancel="handleCancel"
        />

        <!-- Preview -->
        <div
          v-else-if="isViewing && selectedNote"
          class="h-full flex flex-col bg-base-100 rounded-box shadow-md"
        >
          <!-- Preview Header -->
          <div class="p-4 border-b border-base-200">
            <div class="flex justify-between items-center">
              <button class="btn btn-ghost btn-sm md:hidden" @click="isViewing = false">
                ← 返回
              </button>
              <div class="flex-1"></div>
              <div class="flex gap-2">
                <button class="btn btn-outline btn-sm" @click="handleDetail(selectedNote)">
                  🔗 打开
                </button>
                <button
                  class="btn btn-error btn-sm btn-outline"
                  @click="handleDelete(selectedNote.id)"
                >
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                    />
                  </svg>
                  删除
                </button>
                <button class="btn btn-primary btn-sm" @click="handleEdit(selectedNote)">
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
                    />
                  </svg>
                  编辑
                </button>
              </div>
            </div>

            <!-- Preview Content -->
            <!-- <div class="flex-1 overflow-y-auto p-6"> -->
            <h1 class="text-3xl font-bold py-4">{{ selectedNote.title || 'Untitled Note' }}</h1>
            <!-- <div class="text-sm text-base-content/60 md:flex gap-4">
              <div>
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
                  />
                </svg>
                创建于 {{ formatDate(selectedNote.created_at) }}
              </div>
              <div>
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                  />
                </svg>
                更新于 {{ formatDate(selectedNote.updated_at) }}
              </div>
            </div> -->
            <div class="flex flex-wrap gap-4 text-sm text-gray-600 dark:text-gray-400">
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
            <!-- 关联文件夹列表 -->
            <div
              v-if="selectedNote.folders && selectedNote.folders.length > 0"
              class="border-b border-gray-200 dark:border-gray-700 mb-3 mt-3 pb-4"
            >
              <h3 class="text-sm font-medium mb-3 flex items-center gap-2">
                <span>📁</span>
                <span>关联的文件夹 ({{ selectedNote.folders.length }})</span>
              </h3>
              <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                <div
                  v-for="folder in selectedNote.folders"
                  :key="folder.id"
                  class="flex items-center gap-3 p-3 bg-base-200 hover:bg-base-300 rounded-lg cursor-pointer transition-colors"
                >
                  <div class="text-2xl flex-shrink-0">📁</div>
                  <div class="flex-1 min-w-0">
                    <p class="font-medium truncate text-sm">{{ folder.name }}</p>
                    <p class="text-xs text-base-content/60">
                      {{ formatDate(folder.updated_at) }}
                    </p>
                  </div>
                </div>
              </div>
            </div>

            <!-- 关联文件列表 -->
            <div
              v-if="selectedNote.files && selectedNote.files.length > 0"
              class="border-b border-gray-200 dark:border-gray-700 mb-3 mt-3 pb-4"
            >
              <h3 class="text-sm font-medium mb-3 flex items-center gap-2">
                <span>📎</span>
                <span>关联的文件 ({{ selectedNote.files.length }})</span>
              </h3>
              <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                <div
                  v-for="file in selectedNote.files"
                  :key="file.id"
                  class="flex items-center gap-3 p-3 bg-base-200 hover:bg-base-300 rounded-lg cursor-pointer transition-colors"
                  @click="handleFileClick(file)"
                >
                  <div
                    :class="`w-10 h-10 rounded-lg flex items-center justify-center text-lg flex-shrink-0 ${getFileTypeColor(file.mime_type)}`"
                  >
                    {{ getFileIcon(file.mime_type) }}
                  </div>
                  <div class="flex-1 min-w-0">
                    <p class="font-medium truncate text-sm">{{ file.filename }}</p>
                    <p class="text-xs text-base-content/60">{{ formatSize(file.size) }}</p>
                  </div>
                  <svg
                    class="w-5 h-5 text-base-content/40 flex-shrink-0"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M9 5l7 7-7 7"
                    />
                  </svg>
                </div>
              </div>
            </div>
            <!-- 笔记内容 -->
            <div class="prose dark:prose-invert max-w-none mt-4">
              <div v-html="renderedContent"></div>
            </div>
          </div>
        </div>

        <!-- Empty State -->
        <div
          v-else
          class="h-full flex flex-col items-center justify-center text-base-content/30 bg-base-200 rounded-box"
        >
          <span class="text-6xl mb-4">📝</span>
          <p class="text-xl">Select a note to view or edit</p>
        </div>
      </div>
    </div>

    <!-- 文件预览弹窗 -->
    <FilePreview
      v-if="showFilePreview && previewFile"
      :file="previewFile"
      @close="handleClosePreview"
    />
  </div>
</template>
