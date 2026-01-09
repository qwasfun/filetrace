<template>
  <div class="container mx-auto px-4 py-8">
    <div class="flex justify-between items-center mb-8">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-gray-100">存储后端管理</h1>
        <p class="text-gray-500 dark:text-gray-400 mt-1">
          管理文件存储位置，支持本地存储和 S3 兼容对象存储
        </p>
      </div>
      <div class="flex gap-2">
        <div class="dropdown dropdown-end">
          <label tabindex="0" class="btn btn-outline btn-sm">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              class="h-5 w-5 mr-1"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z"
              />
            </svg>
            更多操作
          </label>
          <ul
            tabindex="0"
            class="dropdown-content z-[1] menu p-2 shadow bg-base-100 rounded-box w-52 mt-2"
          >
            <li>
              <a @click="handleExport">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  class="h-5 w-5"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
                  />
                </svg>
                导出配置
              </a>
            </li>
            <li>
              <a @click="openImportModal">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  class="h-5 w-5"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L9 8m4-4v12"
                  />
                </svg>
                导入配置
              </a>
            </li>
          </ul>
        </div>
        <button class="btn btn-sm btn-primary" @click="openCreateModal">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            class="h-5 w-5 mr-2"
            viewBox="0 0 20 20"
            fill="currentColor"
          >
            <path
              fill-rule="evenodd"
              d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z"
              clip-rule="evenodd"
            />
          </svg>
          添加存储后端
        </button>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="flex justify-center py-12">
      <span class="loading loading-spinner loading-lg text-primary"></span>
    </div>

    <!-- Empty State -->
    <div
      v-else-if="backends.length === 0"
      class="text-center py-12 bg-gray-50 dark:bg-gray-800 rounded-xl"
    >
      <svg
        xmlns="http://www.w3.org/2000/svg"
        class="h-16 w-16 mx-auto text-gray-400 mb-4"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4"
        />
      </svg>
      <h3 class="text-lg font-medium text-gray-900 dark:text-gray-100">暂无存储后端</h3>
      <p class="text-gray-500 dark:text-gray-400 mt-2">请添加一个存储后端以开始存储文件</p>
    </div>

    <!-- Backend List -->
    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      <div
        v-for="backend in backends"
        :key="backend.id"
        class="card bg-base-100 shadow-xl border border-gray-200 dark:border-gray-700 hover:shadow-2xl transition-shadow"
        :class="{ 'ring-2 ring-primary': backend.is_default }"
      >
        <div class="card-body">
          <div class="flex justify-between items-start">
            <div class="flex items-center gap-2">
              <div
                class="badge badge-lg"
                :class="backend.backend_type === 'local' ? 'badge-neutral' : 'badge-accent'"
              >
                {{ backend.backend_type === 'local' ? '本地存储' : 'S3 存储' }}
              </div>
              <div v-if="backend.is_default" class="badge badge-primary badge-lg gap-1">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  class="h-3 w-3"
                  viewBox="0 0 20 20"
                  fill="currentColor"
                >
                  <path
                    fill-rule="evenodd"
                    d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                    clip-rule="evenodd"
                  />
                </svg>
                默认
              </div>
            </div>
            <div class="dropdown dropdown-end">
              <label tabindex="0" class="btn btn-ghost btn-sm btn-circle">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  class="h-5 w-5"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z"
                  />
                </svg>
              </label>
              <ul
                tabindex="0"
                class="dropdown-content z-[1] menu p-2 shadow bg-base-100 rounded-box w-52"
              >
                <li><a @click="openEditModal(backend)">编辑配置</a></li>
                <li v-if="!backend.is_default">
                  <a @click="handleSetDefault(backend)">设为默认</a>
                </li>
                <li v-if="!backend.is_default">
                  <a @click="handleDelete(backend)" class="text-error">删除后端</a>
                </li>
              </ul>
            </div>
          </div>

          <h2 class="card-title mt-2">{{ backend.name }}</h2>
          <p class="text-sm text-gray-500 dark:text-gray-400 line-clamp-2 min-h-[2.5rem]">
            {{ backend.description || '暂无描述' }}
          </p>

          <div class="divider my-2"></div>

          <div class="text-xs text-gray-500 space-y-1">
            <div v-if="backend.backend_type === 'local'">
              <span class="font-semibold">路径:</span> {{ backend.config.base_dir }}
            </div>
            <div v-else>
              <div><span class="font-semibold">Bucket:</span> {{ backend.config.bucket_name }}</div>
              <div><span class="font-semibold">Region:</span> {{ backend.config.region_name }}</div>
              <div v-if="backend.config.endpoint_url">
                <span class="font-semibold">Endpoint:</span> {{ backend.config.endpoint_url }}
              </div>
              <div class="mt-2">
                <span class="font-semibold">客户端直传:</span>
                <span
                  class="badge badge-sm ml-1"
                  :class="backend.allow_client_direct_upload ? 'badge-success' : 'badge-ghost'"
                >
                  {{ backend.allow_client_direct_upload ? '已启用' : '未启用' }}
                </span>
              </div>
            </div>
          </div>

          <div class="card-actions justify-end mt-4">
            <button
              class="btn btn-sm btn-outline"
              @click="handleTest(backend)"
              :disabled="testingId === backend.id"
            >
              <span
                v-if="testingId === backend.id"
                class="loading loading-spinner loading-xs"
              ></span>
              <span v-else>测试连接</span>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Create/Edit Modal -->
    <dialog id="backend_modal" class="modal">
      <div class="modal-box w-11/12 max-w-3xl">
        <h3 class="font-bold text-lg mb-4">{{ isEditing ? '编辑存储后端' : '添加存储后端' }}</h3>

        <form @submit.prevent="handleSubmit" class="space-y-4">
          <!-- Basic Info -->
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div class="form-control">
              <label class="label"><span class="label-text">名称</span></label>
              <input
                type="text"
                v-model="form.name"
                placeholder="例如: 主S3存储"
                class="input input-bordered w-full"
                required
              />
            </div>

            <div class="form-control">
              <label class="label"><span class="label-text">类型</span></label>
              <select
                v-model="form.backend_type"
                class="select select-bordered w-full"
                :disabled="isEditing"
              >
                <option value="local">本地存储 (Local)</option>
                <option value="s3">对象存储 (S3 Compatible)</option>
              </select>
            </div>
          </div>

          <div class="form-control">
            <label class="label"><span class="label-text">描述</span></label>
            <textarea
              v-model="form.description"
              class="textarea textarea-bordered h-20 w-full"
              placeholder="可选描述信息..."
            ></textarea>
          </div>

          <div class="divider">配置参数</div>

          <!-- Local Config -->
          <div v-if="form.backend_type === 'local'" class="bg-base-200 p-4 rounded-lg">
            <div class="form-control">
              <label class="label"><span class="label-text">基础目录 (Base Dir)</span></label>
              <input
                type="text"
                v-model="form.config.base_dir"
                placeholder="data/files"
                class="input input-bordered w-full"
                required
              />
              <label class="label"
                ><span class="label-text-alt text-gray-500">相对于应用根目录或绝对路径</span></label
              >
            </div>
          </div>

          <!-- S3 Config -->
          <div v-if="form.backend_type === 's3'" class="bg-base-200 p-4 rounded-lg space-y-4">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div class="form-control">
                <label class="label"><span class="label-text">Bucket Name</span></label>
                <input
                  type="text"
                  v-model="form.config.bucket_name"
                  class="input input-bordered w-full"
                  required
                />
              </div>
              <div class="form-control">
                <label class="label"><span class="label-text">Region Name</span></label>
                <input
                  type="text"
                  v-model="form.config.region_name"
                  placeholder="us-east-1"
                  class="input input-bordered w-full"
                />
              </div>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div class="form-control">
                <label class="label"><span class="label-text">Access Key</span></label>
                <input
                  type="text"
                  v-model="form.config.access_key"
                  class="input input-bordered w-full"
                  required
                />
              </div>
              <div class="form-control">
                <label class="label"><span class="label-text">Secret Key</span></label>
                <input
                  type="password"
                  v-model="form.config.secret_key"
                  class="input input-bordered w-full"
                  required
                />
              </div>
            </div>

            <div class="form-control">
              <label class="label"><span class="label-text">Endpoint URL (可选)</span></label>
              <input
                type="text"
                v-model="form.config.endpoint_url"
                placeholder="https://s3.amazonaws.com"
                class="input input-bordered w-full"
              />
              <label class="label"
                ><span class="label-text-alt text-gray-500"
                  >用于 MinIO, 阿里云 OSS 等非 AWS S3 服务</span
                ></label
              >
            </div>

            <div class="form-control">
              <label class="label"><span class="label-text">Public URL (可选)</span></label>
              <input
                type="text"
                v-model="form.config.public_url"
                placeholder="https://cdn.example.com"
                class="input input-bordered w-full"
              />
              <label class="label"
                ><span class="label-text-alt text-gray-500">用于公开访问的自定义域名</span></label
              >
            </div>

            <div class="form-control mt-4">
              <label class="label cursor-pointer justify-start gap-4">
                <input
                  type="checkbox"
                  v-model="form.allow_client_direct_upload"
                  class="checkbox checkbox-primary"
                />
                <div>
                  <span class="label-text font-medium">启用客户端直传</span>
                  <p class="text-xs text-gray-500 mt-1">
                    允许前端直接上传到S3，提升上传速度并减轻服务器负担
                  </p>
                </div>
              </label>
            </div>
          </div>

          <div class="form-control mt-4" v-if="!isEditing">
            <label class="label cursor-pointer justify-start gap-4">
              <input type="checkbox" v-model="form.is_default" class="checkbox checkbox-primary" />
              <span class="label-text font-medium">设为默认存储后端</span>
            </label>
          </div>

          <div class="modal-action">
            <button type="button" class="btn" @click="closeModal">取消</button>
            <button type="submit" class="btn btn-primary" :disabled="submitting">
              <span v-if="submitting" class="loading loading-spinner loading-xs"></span>
              {{ isEditing ? '保存修改' : '立即创建' }}
            </button>
          </div>
        </form>
      </div>
      <form method="dialog" class="modal-backdrop">
        <button @click="closeModal">close</button>
      </form>
    </dialog>

    <!-- Import Modal -->
    <dialog id="import_modal" class="modal">
      <div class="modal-box">
        <h3 class="font-bold text-lg mb-4">导入存储配置</h3>

        <div class="form-control">
          <label class="label">
            <span class="label-text">选择 JSON 配置文件</span>
          </label>
          <input
            type="file"
            ref="importFileInput"
            @change="handleFileSelect"
            accept=".json,application/json"
            class="file-input file-input-bordered w-full"
          />
          <label class="label">
            <span class="label-text-alt text-gray-500"> 支持导出的 JSON 配置文件 </span>
          </label>
        </div>

        <div class="form-control mt-4">
          <label class="label cursor-pointer">
            <span class="label-text">替换现有同名配置</span>
            <input
              type="checkbox"
              v-model="importOptions.replaceExisting"
              class="checkbox checkbox-primary"
            />
          </label>
          <label class="label">
            <span class="label-text-alt text-gray-500">
              勾选后，同名配置将被覆盖；不勾选则跳过同名配置
            </span>
          </label>
        </div>

        <!-- Import Result -->
        <div v-if="importResult" class="mt-4">
          <div
            class="alert"
            :class="importResult.status === 'success' ? 'alert-success' : 'alert-error'"
          >
            <svg
              v-if="importResult.status === 'success'"
              xmlns="http://www.w3.org/2000/svg"
              class="stroke-current shrink-0 h-6 w-6"
              fill="none"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <svg
              v-else
              xmlns="http://www.w3.org/2000/svg"
              class="stroke-current shrink-0 h-6 w-6"
              fill="none"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <div>
              <div class="font-bold">{{ importResult.message }}</div>
              <div v-if="importResult.stats" class="text-sm mt-1">
                总计: {{ importResult.stats.total }} | 新增: {{ importResult.stats.imported }} |
                更新: {{ importResult.stats.updated }} | 跳过: {{ importResult.stats.skipped }}
              </div>
              <div
                v-if="importResult.stats && importResult.stats.errors.length > 0"
                class="text-sm mt-2"
              >
                <details>
                  <summary class="cursor-pointer">查看错误详情</summary>
                  <ul class="list-disc list-inside mt-2">
                    <li v-for="(error, idx) in importResult.stats.errors" :key="idx">
                      {{ error }}
                    </li>
                  </ul>
                </details>
              </div>
            </div>
          </div>
        </div>

        <div class="modal-action">
          <button type="button" class="btn" @click="closeImportModal" :disabled="importing">
            取消
          </button>
          <button
            type="button"
            class="btn btn-primary"
            @click="handleImport"
            :disabled="!selectedFile || importing"
          >
            <span v-if="importing" class="loading loading-spinner loading-sm"></span>
            <span v-else>开始导入</span>
          </button>
        </div>
      </div>
      <form method="dialog" class="modal-backdrop">
        <button>close</button>
      </form>
    </dialog>

    <!-- Toast Notification (DaisyUI doesn't have built-in JS toast, using simple fixed div) -->
    <div v-if="toast.show" class="toast toast-end z-50">
      <div class="alert" :class="toast.type === 'success' ? 'alert-success' : 'alert-error'">
        <span>{{ toast.message }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch } from 'vue'
import storageBackendService from '@/api/storageBackendService'

const backends = ref([])
const loading = ref(true)
const submitting = ref(false)
const testingId = ref(null)
const isEditing = ref(false)
const currentId = ref(null)

const toast = reactive({
  show: false,
  message: '',
  type: 'success',
})

const importing = ref(false)
const selectedFile = ref(null)
const importFileInput = ref(null)
const importResult = ref(null)
const importOptions = reactive({
  replaceExisting: false,
})

const form = reactive({
  name: '',
  backend_type: 'local',
  description: '',
  is_default: false,
  allow_client_direct_upload: false,
  config: {
    base_dir: 'data/files',
    bucket_name: '',
    access_key: '',
    secret_key: '',
    endpoint_url: '',
    region_name: 'us-east-1',
    public_url: '',
  },
})

// Watch backend type to reset config defaults
watch(
  () => form.backend_type,
  (newType) => {
    if (!isEditing.value) {
      if (newType === 'local') {
        form.config = { base_dir: 'data/files' }
      } else {
        form.config = {
          bucket_name: '',
          access_key: '',
          secret_key: '',
          endpoint_url: '',
          region_name: 'us-east-1',
          public_url: '',
        }
      }
    }
  },
)

const showToast = (message, type = 'success') => {
  toast.message = message
  toast.type = type
  toast.show = true
  setTimeout(() => {
    toast.show = false
  }, 3000)
}

const fetchBackends = async () => {
  loading.value = true
  try {
    backends.value = await storageBackendService.getBackends()
  } catch (error) {
    showToast('加载存储后端失败', 'error')
    console.error(error)
  } finally {
    loading.value = false
  }
}

const openCreateModal = () => {
  isEditing.value = false
  currentId.value = null
  form.name = ''
  form.backend_type = 'local'
  form.description = ''
  form.is_default = false
  form.allow_client_direct_upload = false
  form.config = { base_dir: 'data/files' }
  document.getElementById('backend_modal').showModal()
}

const openEditModal = (backend) => {
  isEditing.value = true
  currentId.value = backend.id
  form.name = backend.name
  form.backend_type = backend.backend_type
  form.description = backend.description
  form.is_default = backend.is_default
  form.allow_client_direct_upload = backend.allow_client_direct_upload || false
  // Deep copy config to avoid reactivity issues
  form.config = JSON.parse(JSON.stringify(backend.config))

  // Ensure S3 fields exist if switching from local or old data
  if (form.backend_type === 's3') {
    form.config = {
      bucket_name: '',
      access_key: '',
      secret_key: '',
      endpoint_url: '',
      region_name: 'us-east-1',
      public_url: '',
      ...form.config,
    }
  }

  document.getElementById('backend_modal').showModal()
}

const closeModal = () => {
  document.getElementById('backend_modal').close()
}

const handleSubmit = async () => {
  submitting.value = true
  try {
    // Clean up config based on type
    const submitData = {
      name: form.name,
      backend_type: form.backend_type,
      description: form.description,
      allow_client_direct_upload:
        form.backend_type === 's3' ? form.allow_client_direct_upload : false,
      config: { ...form.config },
    }

    if (form.backend_type === 'local') {
      // Remove S3 fields for local
      submitData.config = { base_dir: form.config.base_dir }
    }

    if (isEditing.value) {
      // Update
      submitData.is_active = true // Keep active on update
      await storageBackendService.updateBackend(currentId.value, submitData)
      showToast('更新成功')
    } else {
      // Create
      submitData.is_default = form.is_default
      await storageBackendService.createBackend(submitData)
      showToast('创建成功')
    }

    closeModal()
    fetchBackends()
  } catch (error) {
    showToast(error.response?.data?.detail || '操作失败', 'error')
  } finally {
    submitting.value = false
  }
}

const handleDelete = async (backend) => {
  if (!confirm(`确定要删除 "${backend.name}" 吗？此操作不可恢复。`)) return

  try {
    await storageBackendService.deleteBackend(backend.id)
    showToast('删除成功')
    fetchBackends()
  } catch (error) {
    showToast(error.response?.data?.detail || '删除失败', 'error')
  }
}

const handleSetDefault = async (backend) => {
  try {
    await storageBackendService.setDefaultBackend(backend.id)
    showToast('已设置为默认后端')
    fetchBackends()
  } catch (error) {
    showToast(error.response?.data?.detail || '设置失败', 'error')
  }
}

const handleTest = async (backend) => {
  testingId.value = backend.id
  try {
    const res = await storageBackendService.testBackend(backend.id)
    showToast(res.message || '连接测试成功')
  } catch (error) {
    showToast(error.response?.data?.detail || '连接测试失败', 'error')
  } finally {
    testingId.value = null
  }
}

const handleExport = async () => {
  try {
    const response = await storageBackendService.exportConfig()
    // Create download link
    const blob = new Blob([JSON.stringify(response, null, 2)], {
      type: 'application/json',
    })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `storage_config_${new Date().toISOString().replace(/[:.]/g, '-')}.json`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    window.URL.revokeObjectURL(url)
    showToast('配置导出成功')
  } catch (error) {
    showToast(error.response?.data?.detail || '导出失败', 'error')
  }
}

const openImportModal = () => {
  selectedFile.value = null
  importResult.value = null
  importOptions.replaceExisting = false
  if (importFileInput.value) {
    importFileInput.value.value = ''
  }
  document.getElementById('import_modal').showModal()
}

const closeImportModal = () => {
  document.getElementById('import_modal').close()
}

const handleFileSelect = (event) => {
  const file = event.target.files[0]
  if (file) {
    selectedFile.value = file
    importResult.value = null
  }
}

const handleImport = async () => {
  if (!selectedFile.value) return

  importing.value = true
  importResult.value = null

  try {
    const formData = new FormData()
    formData.append('file', selectedFile.value)

    const result = await storageBackendService.importConfig(formData, importOptions.replaceExisting)

    importResult.value = result
    showToast(result.message || '导入成功')

    // Refresh list if successful
    if (result.status === 'success') {
      fetchBackends()
    }
  } catch (error) {
    importResult.value = {
      status: 'error',
      message: error.response?.data?.detail || '导入失败',
    }
    showToast(error.response?.data?.detail || '导入失败', 'error')
  } finally {
    importing.value = false
  }
}

onMounted(() => {
  fetchBackends()
})
</script>
