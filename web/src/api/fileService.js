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
  // 获取预签名上传URL（用于S3直传）
  getPresignedUploadUrl(filename, contentType, params) {
    return service.post('/v1/files/presigned-upload-url', null, {
      params: {
        filename,
        content_type: contentType,
        ...params,
      },
    })
  },
  // 确认直传完成，创建文件记录
  confirmDirectUpload(data) {
    return service.post('/v1/files/confirm-direct-upload', null, {
      params: data,
    })
  },
  // 直接上传到S3（使用预签名URL）
  async uploadToS3(presignedData, file) {
    const formData = new FormData()

    // 添加预签名字段
    Object.keys(presignedData.fields).forEach((key) => {
      formData.append(key, presignedData.fields[key])
    })

    // 添加文件（必须是最后一个）
    formData.append('file', file)

    // 直接上传到S3
    const response = await fetch(presignedData.presigned_url, {
      method: 'POST',
      body: formData,
    })

    if (!response.ok) {
      throw new Error(`S3上传失败: ${response.statusText}`)
    }

    return response
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
  renameFile(id, data) {
    return service.put(`/v1/files/${id}/rename`, data)
  },
  batchMoveFiles(data) {
    return service.post('/v1/files/batch/move', data)
  },
  batchDeleteFiles(data) {
    return service.post('/v1/files/batch/delete', data)
  },
}
