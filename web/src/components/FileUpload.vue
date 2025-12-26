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
  // 如果有 Electron API，使用 Electron 的文件选择器
  if (window.electronAPI) {
    console.log('Running in Electron environment')
    console.log('electronAPI is available')
    selectFilesViaElectron()
  } else {
    console.error('electronAPI is undefined, falling back to browser file picker')
    console.log('Not running in Electron, using browser file picker')
    // 否则使用浏览器的文件选择器
    fileInput.value.click()
  }
}

import fileService from '../api/fileService'

// 通过 Electron 选择文件
const selectFilesViaElectron = async () => {
  try {
    const filePaths = await window.electronAPI.selectFiles()
    if (filePaths && filePaths.length > 0) {
      // 获取所有文件的信息，包括创建和修改时间
      const filesInfo = await window.electronAPI.getFilesInfo(filePaths)
      await uploadFilesWithMetadata(filesInfo)
    }
  } catch (error) {
    console.error('选择文件失败', error)
    alert('选择文件失败')
  }
}

// 上传文件（带时间元数据）
const uploadFilesWithMetadata = async (filesInfo) => {
  uploading.value = true
  try {
    // 为每个文件单独上传，以便传递时间信息
    for (const fileInfo of filesInfo) {
      const formData = new FormData()

      // 从文件路径读取文件内容
      const buffer = await window.electronAPI.readFile(fileInfo.path)
      const blob = new Blob([buffer])
      const file = new File([blob], fileInfo.name)

      formData.append('files', file)

      const params = {}
      if (props.folderId) {
        params.folder_id = props.folderId
      }

      // 添加原始创建时间和修改时间
      if (fileInfo.timestamps) {
        params.original_created_at = fileInfo.timestamps.created
        params.original_updated_at = fileInfo.timestamps.modified
      }

      await fileService.uploadFiles(formData, params)
    }

    emit('upload-success')
  } catch (error) {
    console.error('上传失败', error)
    alert('上传失败')
  } finally {
    uploading.value = false
  }
}

// 上传文件（浏览器方式，无时间信息）
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
