<script setup>
import { ref, onMounted } from 'vue'
import folderService from '../api/folderService'

const props = defineProps({
  excludeIds: {
    type: Array,
    default: () => [],
  },
})

const emit = defineEmits(['select', 'cancel'])

const folders = ref([])
const loading = ref(false)
const selectedFolders = ref([])
const currentFolderId = ref(null)
const breadcrumbs = ref([{ id: null, name: '根目录' }])

const loadFolders = async () => {
  loading.value = true
  try {
    const params = {}
    if (currentFolderId.value) {
      params.parent_id = currentFolderId.value
    }
    const response = await folderService.getFolders(params)
    folders.value = response
  } catch (error) {
    console.error('Failed to load folders', error)
  } finally {
    loading.value = false
  }
}

const enterFolder = (folder) => {
  currentFolderId.value = folder.id
  breadcrumbs.value.push({ id: folder.id, name: folder.name })
  loadFolders()
}

const navigateBreadcrumb = (index) => {
  const target = breadcrumbs.value[index]
  currentFolderId.value = target.id
  breadcrumbs.value = breadcrumbs.value.slice(0, index + 1)
  loadFolders()
}

const toggleSelection = (folderId) => {
  if (selectedFolders.value.includes(folderId)) {
    selectedFolders.value = selectedFolders.value.filter((id) => id !== folderId)
  } else {
    selectedFolders.value.push(folderId)
  }
}

const handleConfirm = () => {
  emit('select', selectedFolders.value)
}

onMounted(() => {
  loadFolders()
})
</script>

<template>
  <div class="flex flex-col h-full">
    <div class="mb-4">
      <h3 class="font-bold text-lg mb-2">关联文件夹</h3>

      <!-- Breadcrumb -->
      <div class="text-sm breadcrumbs">
        <ul>
          <li
            v-for="(crumb, index) in breadcrumbs"
            :key="index"
            class="cursor-pointer hover:text-primary"
            @click="navigateBreadcrumb(index)"
          >
            {{ crumb.name }}
          </li>
        </ul>
      </div>
    </div>

    <div v-if="loading" class="flex-1 flex justify-center items-center">
      <span class="loading loading-spinner"></span>
    </div>

    <div v-else class="flex-1 overflow-y-auto space-y-2">
      <div
        v-for="folder in folders"
        :key="folder.id"
        class="card bg-base-200 border-2 cursor-pointer relative"
        :class="
          selectedFolders.includes(folder.id)
            ? 'border-primary'
            : 'border-transparent hover:border-base-300'
        "
      >
        <div
          v-if="props.excludeIds.includes(folder.id)"
          class="absolute inset-0 bg-base-300/50 cursor-not-allowed z-10 flex items-center justify-center"
        >
          <span class="badge">已关联</span>
        </div>

        <div class="card-body p-4">
          <div class="flex items-center gap-3">
            <div class="flex-none">
              <input
                type="checkbox"
                class="checkbox checkbox-primary"
                :checked="selectedFolders.includes(folder.id)"
                :disabled="props.excludeIds.includes(folder.id)"
                @click.stop="toggleSelection(folder.id)"
              />
            </div>
            <div class="flex-1 flex items-center gap-3" @click="enterFolder(folder)">
              <div class="text-2xl">📁</div>
              <div class="flex-1">
                <h4 class="font-bold">{{ folder.name }}</h4>
                <p class="text-xs text-base-content/60">
                  {{ new Date(folder.updated_at).toLocaleDateString() }}
                </p>
              </div>
              <div class="text-base-content/40">→</div>
            </div>
          </div>
        </div>
      </div>

      <div v-if="folders.length === 0" class="text-center py-10 text-base-content/50">
        此文件夹为空
      </div>
    </div>

    <!-- Actions -->
    <div class="flex justify-between items-center mt-4 pt-4 border-t border-base-200">
      <div class="text-sm text-base-content/70">已选择 {{ selectedFolders.length }} 个文件夹</div>
      <div class="flex gap-2">
        <button class="btn btn-ghost btn-sm" @click="$emit('cancel')">取消</button>
        <button
          class="btn btn-primary btn-sm"
          :disabled="selectedFolders.length === 0"
          @click="handleConfirm"
        >
          确认 ({{ selectedFolders.length }})
        </button>
      </div>
    </div>
  </div>
</template>
