export const formatDate = (dateString) => {
  if (!dateString) return ''
  const dateStr =
    dateString.endsWith('Z') || dateString.includes('+') ? dateString : dateString + 'Z'
  return new Date(dateStr).toLocaleString()
}

export const formatSize = (bytes) => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}
