import service from '@/utils/service'

export default {
  // 获取所有存储后端
  getBackends() {
    return service.get('/v1/storage-backends')
  },

  // 获取指定存储后端
  getBackend(id) {
    return service.get(`/v1/storage-backends/${id}`)
  },

  // 创建存储后端
  createBackend(data) {
    return service.post('/v1/storage-backends', data)
  },

  // 更新存储后端
  updateBackend(id, data) {
    return service.put(`/v1/storage-backends/${id}`, data)
  },

  // 删除存储后端
  deleteBackend(id) {
    return service.delete(`/v1/storage-backends/${id}`)
  },

  // 设置默认存储后端
  setDefaultBackend(id) {
    return service.post(`/v1/storage-backends/${id}/set-default`)
  },

  // 测试存储后端连接
  testBackend(id) {
    return service.post(`/v1/storage-backends/${id}/test`)
  },

  // 导出存储配置
  exportConfig() {
    return service.get('/v1/storage-backends/export/config')
  },

  // 导入存储配置
  importConfig(formData, replaceExisting = false) {
    return service.post(
      `/v1/storage-backends/import/config?replace_existing=${replaceExisting}`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      },
    )
  },
}
