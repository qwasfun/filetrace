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
const folderInput = ref(null)
const uploading = ref(false)
const uploadProgress = ref({ current: 0, total: 0 })

const handleDragOver = (e) => {
  e.preventDefault()
  isDragging.value = true
}

const handleDragLeave = (e) => {
  e.preventDefault()
  isDragging.value = false
}

const handleDrop = async (e) => {
  e.preventDefault()
  isDragging.value = false
  if (e.dataTransfer.items && e.dataTransfer.items.length) {
    const files = await getAllFiles(e.dataTransfer.items)
    if (files.length) {
      uploadFiles(files)
    }
  } else if (e.dataTransfer.files.length) {
    uploadFiles(Array.from(e.dataTransfer.files).map((f) => ({ file: f, path: f.name })))
  }
}

const handleFileSelect = (e) => {
  if (e.target.files.length) {
    const files = Array.from(e.target.files).map((f) => ({
      file: f,
      path: f.name,
    }))
    uploadFiles(files)
  }
}

const handleFolderSelect = (e) => {
  if (e.target.files.length) {
    const files = Array.from(e.target.files).map((f) => ({
      file: f,
      path: f.webkitRelativePath || f.name,
    }))
    uploadFiles(files)
  }
}

const triggerFileInput = (e) => {
  e.stopPropagation()
  fileInput.value.click()
}

const triggerFolderInput = (e) => {
  e.stopPropagation()
  folderInput.value.click()
}

// 递归处理文件和文件夹
const getAllFiles = async (dataTransferItems) => {
  const files = []
  const queue = []

  for (let i = 0; i < dataTransferItems.length; i++) {
    const item = dataTransferItems[i].webkitGetAsEntry()
    if (item) {
      queue.push({ entry: item, path: '' })
    }
  }

  while (queue.length > 0) {
    const { entry, path } = queue.shift()

    if (entry.isFile) {
      const file = await new Promise((resolve) => {
        entry.file(resolve)
      })
      const fullPath = path ? `${path}/${entry.name}` : entry.name
      files.push({ file, path: fullPath })
    } else if (entry.isDirectory) {
      const reader = entry.createReader()
      const entries = await new Promise((resolve) => {
        reader.readEntries(resolve)
      })

      for (const childEntry of entries) {
        const newPath = path ? `${path}/${entry.name}` : entry.name
        queue.push({ entry: childEntry, path: newPath })
      }
    }
  }

  return files
}

import fileService from '../api/fileService'

const uploadFiles = async (filesWithPaths) => {
  uploading.value = true

  // 分批上传，每批最多 20 个文件
  const BATCH_SIZE = 20
  const totalFiles = filesWithPaths.length
  let uploadedCount = 0

  uploadProgress.value = { current: 0, total: totalFiles }

  try {
    for (let i = 0; i < totalFiles; i += BATCH_SIZE) {
      const batch = filesWithPaths.slice(i, i + BATCH_SIZE)
      const formData = new FormData()

      // 添加文件和对应的相对路径
      for (const { file, path } of batch) {
        // 使用 webkitRelativePath 作为文件名发送
        const fileToUpload = new File([file], path, { type: file.type })
        formData.append('files', fileToUpload)
      }

      const params = {}
      if (props.folderId) {
        params.folder_id = props.folderId
      }

      await fileService.uploadFiles(formData, params)
      uploadedCount += batch.length
      uploadProgress.value.current = uploadedCount
      console.log(`已上传 ${uploadedCount}/${totalFiles} 个文件`)
    }

    emit('upload-success')
  } catch (error) {
    console.error('Upload failed', error)
    alert(`上传失败: ${error.message || '未知错误'}`)
  } finally {
    uploading.value = false
    uploadProgress.value = { current: 0, total: 0 }
    // Reset input
    if (fileInput.value) fileInput.value.value = ''
    if (folderInput.value) folderInput.value.value = ''
  }
}
</script>

<template>
  <div
    class="border-2 border-dashed rounded-lg p-8 text-center transition-colors"
    :class="{
      'border-primary bg-primary/10': isDragging,
      'border-base-300 hover:border-primary': !isDragging,
    }"
    @dragover="handleDragOver"
    @dragleave="handleDragLeave"
    @drop="handleDrop"
  >
    <input type="file" multiple class="hidden" ref="fileInput" @change="handleFileSelect" />
    <input
      type="file"
      webkitdirectory
      class="hidden"
      ref="folderInput"
      @change="handleFolderSelect"
    />

    <div v-if="uploading" class="flex flex-col items-center">
      <span class="loading loading-spinner loading-lg text-primary"></span>
      <p class="mt-2 text-primary">上传中...</p>
      <p class="text-sm text-base-content/60 mt-1">
        {{ uploadProgress.current }} / {{ uploadProgress.total }} 个文件
      </p>
      <progress
        class="progress progress-primary w-56 mt-2"
        :value="uploadProgress.current"
        :max="uploadProgress.total"
      ></progress>
    </div>
    <div v-else>
      <div class="text-4xl mb-4">📂</div>
      <p class="text-lg font-medium mb-4">拖放文件或文件夹到这里</p>
      <div class="flex gap-3 justify-center">
        <button @click="triggerFileInput" class="btn btn-primary btn-sm">📄 选择文件</button>
        <button @click="triggerFolderInput" class="btn btn-secondary btn-sm">📁 选择文件夹</button>
      </div>
      <p class="text-xs text-base-content/60 mt-3">支持拖拽上传，自动保留文件夹结构</p>
    </div>
  </div>
</template>
