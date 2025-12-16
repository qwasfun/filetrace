<script setup>
import { ref } from 'vue'

const props = defineProps({
  folderId: {
    type: String,
    default: null,
  },
})

const emit = defineEmits(['upload-success'])
const isDragging = ref(false)
const fileInput = ref(null)
const uploading = ref(false)

const handleDragOver = (e) => {
  e.preventDefault()
  isDragging.value = true
}

const handleDragLeave = (e) => {
  e.preventDefault()
  isDragging.value = false
}

const handleDrop = (e) => {
  e.preventDefault()
  isDragging.value = false
  if (e.dataTransfer.files.length) {
    uploadFiles(e.dataTransfer.files)
  }
}

const handleFileSelect = (e) => {
  if (e.target.files.length) {
    uploadFiles(e.target.files)
  }
}

const triggerFileInput = () => {
  fileInput.value.click()
}

import fileService from '../api/fileService'

const uploadFiles = async (files) => {
  uploading.value = true
  const formData = new FormData()
  for (let i = 0; i < files.length; i++) {
    formData.append('files', files[i])
  }

  try {
    const params = {}
    if (props.folderId) {
      params.folder_id = props.folderId
    }
    await fileService.uploadFiles(formData, params)
    emit('upload-success')
  } catch (error) {
    console.error('Upload failed', error)
    alert('Upload failed')
  } finally {
    uploading.value = false
    // Reset input
    if (fileInput.value) fileInput.value.value = ''
  }
}
</script>

<template>
  <div
    class="border-2 border-dashed rounded-lg p-8 text-center transition-colors cursor-pointer"
    :class="{
      'border-primary bg-primary/10': isDragging,
      'border-base-300 hover:border-primary': !isDragging,
    }"
    @dragover="handleDragOver"
    @dragleave="handleDragLeave"
    @drop="handleDrop"
    @click="triggerFileInput"
  >
    <input type="file" multiple class="hidden" ref="fileInput" @change="handleFileSelect" />

    <div v-if="uploading" class="flex flex-col items-center">
      <span class="loading loading-spinner loading-lg text-primary"></span>
      <p class="mt-2 text-primary">Uploading...</p>
    </div>
    <div v-else>
      <div class="text-4xl mb-2">📂</div>
      <p class="text-lg font-medium">Drag & Drop files here</p>
      <p class="text-sm text-base-content/60">or click to browse</p>
    </div>
  </div>
</template>
