<script setup>
import { ref, onMounted } from 'vue'
import noteService from '../../api/noteService.js'
import NoteEditor from '../../components/NoteEditor.vue'
import { formatDate } from '@/utils/format'

const notes = ref([])
const loading = ref(false)
const selectedNote = ref(null)
const isEditing = ref(false)

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
  isEditing.value = true
}

const handleEdit = (note) => {
  selectedNote.value = { ...note } // Clone to avoid direct mutation
  isEditing.value = true
}

const handleSave = async (noteData) => {
  try {
    if (selectedNote.value && selectedNote.value.id) {
      await noteService.updateNote(selectedNote.value.id, noteData)
    } else {
      await noteService.createNote(noteData)
    }
    isEditing.value = false
    selectedNote.value = null
    await loadNotes()
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
      isEditing.value = false
      selectedNote.value = null
    }
  } catch (error) {
    console.error('Failed to delete note', error)
  }
}

onMounted(async () => {
  await loadNotes()
})
</script>

<template>
  <div class="bg-gray-50 dark:bg-gray-900 h-[calc(100vh-64px)]">
    <div class="container mx-auto px-4 py-6 h-full flex">
      <!-- Notes List Sidebar -->
      <div class="w-1/3 flex flex-col h-full">
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
            class="card bg-base-100 shadow-sm hover:bg-base-200 cursor-pointer transition-colors"
            :class="{ 'ring-2 ring-primary': selectedNote?.id === note.id }"
            @click="handleEdit(note)"
          >
            <div class="card-body p-4">
              <h3 class="font-bold truncate">{{ note.title || 'Untitled Note' }}</h3>
              <p class="text-xs text-base-content/60 line-clamp-2">{{ note.content }}</p>
              <div class="flex justify-between items-center mt-2">
                <span class="text-xs text-base-content/40">{{ formatDate(note.updated_at) }}</span>
                <button class="btn btn-ghost btn-xs text-error" @click.stop="handleDelete(note.id)">
                  删除
                </button>
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

      <!-- main Content / Editor -->
      <div class="flex-1 h-full ml-4">
        <NoteEditor
          v-if="isEditing"
          :note="selectedNote"
          @save="handleSave"
          @cancel="isEditing = false"
        />
        <div
          v-else
          class="h-full flex flex-col items-center justify-center text-base-content/30 bg-base-200 rounded-box"
        >
          <span class="text-6xl mb-4">📝</span>
          <p class="text-xl">Select a note to view or edit</p>
        </div>
      </div>
    </div>
  </div>
</template>
