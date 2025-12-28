import { app, BrowserWindow, ipcMain, dialog } from 'electron'
import fs from 'node:fs'
import path from 'node:path'
import process from 'node:process'
import { fileURLToPath } from 'node:url'
import 'dotenv/config'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

function createWindow() {
  const preloadPath = path.join(__dirname, 'preload.js')
  console.log('Preload path:', preloadPath)

  const win = new BrowserWindow({
    width: 800,
    height: 600,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: preloadPath,
    },
  })

  // 打开开发者工具以便调试
  if (process.env.NODE_ENV === 'development') {
    win.webContents.openDevTools()
  }

  if (process.env.NODE_ENV === 'development') {
    win.loadURL('http://localhost:5173')
  } else {
    win.loadFile('dist/index.html')
  }

  win.on('minimize', (e) => {
    e.preventDefault()
    win.hide()
  })

  // win.loadFile('index.html');
}

// 处理文件选择请求
ipcMain.handle('select-file', async () => {
  const { canceled, filePaths } = await dialog.showOpenDialog({
    properties: ['openFile'],
  })

  if (!canceled && filePaths.length > 0) {
    return filePaths[0]
  }
  return null
})

// 处理多文件选择请求
ipcMain.handle('select-files', async () => {
  const { canceled, filePaths } = await dialog.showOpenDialog({
    properties: ['openFile', 'multiSelections'],
  })

  if (!canceled && filePaths.length > 0) {
    return filePaths
  }
  return []
})

// 处理文件夹选择请求
ipcMain.handle('select-folder', async () => {
  const { canceled, filePaths } = await dialog.showOpenDialog({
    properties: ['openDirectory'],
  })

  if (!canceled && filePaths.length > 0) {
    return filePaths[0]
  }
  return null
})

// 递归获取文件夹内所有文件
ipcMain.handle('get-folder-files', async (event, folderPath) => {
  try {
    const filesInfo = []

    function traverseDirectory(dirPath, relativePath = '') {
      const items = fs.readdirSync(dirPath)

      for (const item of items) {
        const fullPath = path.join(dirPath, item)
        const stats = fs.statSync(fullPath)
        const itemRelativePath = relativePath ? path.join(relativePath, item) : item

        if (stats.isFile()) {
          filesInfo.push({
            path: fullPath,
            relativePath: itemRelativePath,
            name: item,
            extension: path.extname(item),
            timestamps: {
              created: stats.birthtime,
              modified: stats.mtime,
              accessed: stats.atime,
              changed: stats.ctime,
            },
            size: stats.size,
          })
        } else if (stats.isDirectory()) {
          traverseDirectory(fullPath, itemRelativePath)
        }
      }
    }

    traverseDirectory(folderPath)
    return filesInfo
  } catch (error) {
    throw new Error(`无法读取文件夹: ${error.message}`)
  }
})

// 获取文件详细信息
ipcMain.handle('get-file-info', async (event, filePath) => {
  try {
    const stats = fs.statSync(filePath)

    return {
      path: filePath,
      name: path.basename(filePath),
      extension: path.extname(filePath),

      // 时间信息
      timestamps: {
        created: stats.birthtime,
        modified: stats.mtime,
        accessed: stats.atime,
        changed: stats.ctime,
      },

      // 格式化时间字符串
      formatted: {
        created: formatDate(stats.birthtime),
        modified: formatDate(stats.mtime),
        accessed: formatDate(stats.atime),
        changed: formatDate(stats.ctime),
      },

      // 其他信息
      size: stats.size,
      sizeFormatted: formatFileSize(stats.size),
      isFile: stats.isFile(),
      isDirectory: stats.isDirectory(),
      permissions: stats.mode.toString(8), // 权限（八进制）
    }
  } catch (error) {
    throw new Error(`无法读取文件信息: ${error.message}`)
  }
})

// 批量获取文件信息
ipcMain.handle('get-files-info', async (event, filePaths) => {
  try {
    const filesInfo = filePaths.map((filePath) => {
      const stats = fs.statSync(filePath)
      return {
        path: filePath,
        name: path.basename(filePath),
        extension: path.extname(filePath),
        timestamps: {
          created: stats.birthtime,
          modified: stats.mtime,
          accessed: stats.atime,
          changed: stats.ctime,
        },
        size: stats.size,
      }
    })

    console.log('filesInfo',filesInfo)
    return filesInfo
  } catch (error) {
    throw new Error(`无法读取文件信息: ${error.message}`)
  }
})

// 读取文件内容
ipcMain.handle('read-file', async (event, filePath) => {
  try {
    const buffer = fs.readFileSync(filePath)
    return buffer
  } catch (error) {
    throw new Error(`无法读取文件: ${error.message}`)
  }
})

function formatDate(date) {
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })
}

function formatFileSize(bytes) {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

app.whenReady().then(createWindow)
