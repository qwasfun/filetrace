import service from '@/utils/service'

export default {
  createFolder(data) {
    return service.post('/v1/folders/', data)
  },
  getFolders(params) {
    return service.get('/v1/folders/', { params })
  },
  getFolder(id) {
    return service.get(`/v1/folders/${id}`)
  },
  updateFolder(id, data) {
    return service.put(`/v1/folders/${id}`, data)
  },
  deleteFolder(id) {
    return service.delete(`/v1/folders/${id}`)
  },
}
