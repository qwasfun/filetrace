<script setup>
import { ref } from 'vue'
import fileService from '../api/fileService'

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
    uploadFiles(Array.from(e.dataTransfer.files).map(f => ({file: f, path: f.name})))
  }
}

const handleFileSelect = (e) => {
  if (e.target.files.length) {
    const files = Array.from(e.target.files).map(f => ({
      file: f,
      path: f.name
    }))
    uploadFiles(files)
  }
}

const triggerFileInput = (e) => {
  e.stopPropagation()
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

const handleFolderSelect = (e) => {
  if (e.target.files.length) {
    const files = Array.from(e.target.files).map(f => ({
      file: f,
      path: f.webkitRelativePath || f.name
    }))
    uploadFiles(files)
  }
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
const uploadFiles = async (filesWithPaths) => {
  uploading.value = true
  const formData = new FormData()

  // 添加文件和对应的相对路径
  for (let i = 0; i < filesWithPaths.length; i++) {
    const { file, path } = filesWithPaths[i]
    formData.append('files', file)
    formData.append('relative_paths', path)
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
    <input
      type="file"
      multiple
      class="hidden"
      ref="fileInput"
      @change="handleFileSelect"
    />
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
    </div>
    <div v-else>
      <div class="text-4xl mb-4">📂</div>
      <p class="text-lg font-medium mb-4">拖放文件或文件夹到这里</p>
      <div class="flex gap-3 justify-center">
        <button
          @click="triggerFileInput"
          class="btn btn-primary btn-sm"
        >
          📄 选择文件
        </button>
        <button
          @click="triggerFolderInput"
          class="btn btn-secondary btn-sm"
        >
          📁 选择文件夹
        </button>
      </div>
      <p class="text-xs text-base-content/60 mt-3">支持拖拽上传，自动保留文件夹结构</p>
    </div>
  </div>
</template>
