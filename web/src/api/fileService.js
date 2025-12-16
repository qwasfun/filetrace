import service from '@/utils/service'

export default {
  uploadFiles(formData, params) {
    return service.post('/v1/files/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      params,
    })
  },
  getFiles(params) {
    return service.get('/v1/files/', { params })
  },
  deleteFile(id) {
    return service.delete(`/v1/files/${id}`)
  },
  moveFile(id, data) {
    return service.put(`/v1/files/${id}/move`, data)
  },
}
