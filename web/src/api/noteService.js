import service from '@/utils/service'

export default {
  createNote(noteData) {
    return service.post('/v1/notes/', noteData)
  },
  getNotes(params) {
    return service.get('/v1/notes/', { params })
  },
  getNote(id) {
    return service.get(`/v1/notes/${id}`)
  },
  getNotesByFileId(fileId) {
    return service.get('/v1/notes/', { params: { file_id: fileId } })
  },
  getNotesByFolderId(folderId) {
    return service.get('/v1/notes/', { params: { folder_id: folderId } })
  },
  updateNote(id, noteData) {
    return service.put(`/v1/notes/${id}`, noteData)
  },
  deleteNote(id) {
    return service.delete(`/v1/notes/${id}`)
  },
  attachFiles(id, fileIds) {
    return service.post(`/v1/notes/${id}/attach`, { file_ids: fileIds })
  },
  detachFiles(id, fileIds) {
    return service.post(`/v1/notes/${id}/detach`, { file_ids: fileIds })
  },
  attachFolders(id, folderIds) {
    return service.post(`/v1/notes/${id}/attach-folders`, { folder_ids: folderIds })
  },
  detachFolders(id, folderIds) {
    return service.post(`/v1/notes/${id}/detach-folders`, { folder_ids: folderIds })
  },
}
