export const getFileIcon = (mimeType) => {
  if (mimeType.startsWith('image/')) return '🖼️'
  if (mimeType.startsWith('video/')) return '🎥'
  if (mimeType === 'application/pdf') return '📄'
  if (mimeType.startsWith('audio/')) return '🎵'
  if (
    mimeType.startsWith('text/') ||
    ['application/json', 'application/javascript', 'application/xml'].includes(mimeType)
  )
    return '📄'
  if (mimeType.includes('document') || mimeType.includes('word')) return '📝'
  if (mimeType.includes('sheet') || mimeType.includes('excel')) return '📊'
  if (mimeType.includes('presentation') || mimeType.includes('powerpoint')) return '📋'
  if (mimeType.includes('zip') || mimeType.includes('archive')) return '🗜️'
  return '📁'
}

export const getFileTypeColor = (mimeType) => {
  if (mimeType.startsWith('image/')) return 'bg-green-100 text-green-600'
  if (mimeType.startsWith('video/')) return 'bg-blue-100 text-blue-600'
  if (mimeType === 'application/pdf') return 'bg-red-100 text-red-600'
  if (mimeType.startsWith('audio/')) return 'bg-purple-100 text-purple-600'
  return 'bg-gray-100 text-gray-600'
}
