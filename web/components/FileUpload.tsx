'use client'

import { useState, useCallback } from 'react'
import {
  Upload,
  File,
  X,
  CheckCircle,
  AlertCircle,
  Loader2,
  FileText,
  FileIcon,
} from 'lucide-react'

interface UploadFile {
  id: string
  file: File
  status: 'pending' | 'uploading' | 'success' | 'error'
  progress: number
  error?: string
}

interface FileUploadProps {
  onUpload: (files: File[]) => Promise<void>
  accept?: string
  maxFiles?: number
  maxSize?: number // in MB
  disabled?: boolean
}

export default function FileUpload({
  onUpload,
  accept = '.pdf,.txt,.md',
  maxFiles = 10,
  maxSize = 50,
  disabled = false,
}: FileUploadProps) {
  const [dragActive, setDragActive] = useState(false)
  const [files, setFiles] = useState<UploadFile[]>([])
  const [uploading, setUploading] = useState(false)

  const getFileIcon = (filename: string) => {
    const ext = filename.split('.').pop()?.toLowerCase()
    switch (ext) {
      case 'pdf':
        return <FileText className="w-5 h-5 text-red-500" />
      case 'md':
        return <FileText className="w-5 h-5 text-blue-500" />
      case 'txt':
        return <FileIcon className="w-5 h-5 text-gray-500" />
      default:
        return <File className="w-5 h-5 text-gray-400" />
    }
  }

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  const validateFile = (file: File): string | null => {
    // Check file type
    const ext = '.' + file.name.split('.').pop()?.toLowerCase()
    const acceptedTypes = accept.split(',').map(t => t.trim().toLowerCase())
    if (!acceptedTypes.includes(ext)) {
      return `지원하지 않는 파일 형식입니다. (${accept})`
    }

    // Check file size
    if (file.size > maxSize * 1024 * 1024) {
      return `파일 크기가 ${maxSize}MB를 초과합니다.`
    }

    return null
  }

  const addFiles = useCallback((newFiles: FileList | File[]) => {
    const fileArray = Array.from(newFiles)
    const validFiles: UploadFile[] = []

    for (const file of fileArray) {
      if (files.length + validFiles.length >= maxFiles) {
        break
      }

      // Check for duplicates
      const isDuplicate = files.some(f => f.file.name === file.name && f.file.size === file.size)
      if (isDuplicate) continue

      const error = validateFile(file)
      validFiles.push({
        id: Math.random().toString(36).substr(2, 9),
        file,
        status: error ? 'error' : 'pending',
        progress: 0,
        error: error || undefined,
      })
    }

    setFiles(prev => [...prev, ...validFiles])
  }, [files, maxFiles, maxSize, accept])

  const removeFile = (id: string) => {
    setFiles(prev => prev.filter(f => f.id !== id))
  }

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      addFiles(e.dataTransfer.files)
    }
  }

  const handleUpload = async () => {
    const pendingFiles = files.filter(f => f.status === 'pending')
    if (pendingFiles.length === 0) return

    setUploading(true)

    // Update all pending files to uploading
    setFiles(prev =>
      prev.map(f =>
        f.status === 'pending' ? { ...f, status: 'uploading' as const, progress: 0 } : f
      )
    )

    try {
      // Simulate progress updates
      const progressInterval = setInterval(() => {
        setFiles(prev =>
          prev.map(f =>
            f.status === 'uploading'
              ? { ...f, progress: Math.min(f.progress + 10, 90) }
              : f
          )
        )
      }, 200)

      await onUpload(pendingFiles.map(f => f.file))

      clearInterval(progressInterval)

      // Mark all uploading files as success
      setFiles(prev =>
        prev.map(f =>
          f.status === 'uploading' ? { ...f, status: 'success' as const, progress: 100 } : f
        )
      )
    } catch (error) {
      // Mark all uploading files as error
      setFiles(prev =>
        prev.map(f =>
          f.status === 'uploading'
            ? { ...f, status: 'error' as const, error: '업로드 실패' }
            : f
        )
      )
    } finally {
      setUploading(false)
    }
  }

  const clearCompleted = () => {
    setFiles(prev => prev.filter(f => f.status !== 'success'))
  }

  const pendingCount = files.filter(f => f.status === 'pending').length
  const successCount = files.filter(f => f.status === 'success').length

  return (
    <div className="space-y-4">
      {/* Drop Zone */}
      <div
        className={`
          relative border-2 border-dashed rounded-xl p-8 transition-all duration-200
          ${dragActive
            ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20 scale-[1.02]'
            : 'border-gray-300 dark:border-gray-600 hover:border-gray-400'
          }
          ${disabled ? 'opacity-50 pointer-events-none' : ''}
        `}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
      >
        <input
          type="file"
          multiple
          accept={accept}
          onChange={(e) => e.target.files && addFiles(e.target.files)}
          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
          disabled={disabled || uploading}
        />

        <div className="text-center">
          <div className={`
            w-16 h-16 mx-auto mb-4 rounded-full flex items-center justify-center
            ${dragActive ? 'bg-primary-100 dark:bg-primary-800' : 'bg-gray-100 dark:bg-gray-700'}
          `}>
            <Upload className={`w-8 h-8 ${dragActive ? 'text-primary-600' : 'text-gray-400'}`} />
          </div>
          <p className="text-lg font-medium text-gray-700 dark:text-gray-300 mb-1">
            파일을 드래그하거나 클릭하여 업로드
          </p>
          <p className="text-sm text-gray-500">
            {accept.split(',').join(', ')} 파일 지원 • 최대 {maxSize}MB
          </p>
        </div>
      </div>

      {/* File List */}
      {files.length > 0 && (
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
              파일 목록 ({files.length})
            </span>
            {successCount > 0 && (
              <button
                onClick={clearCompleted}
                className="text-sm text-gray-500 hover:text-gray-700"
              >
                완료된 항목 지우기
              </button>
            )}
          </div>

          <div className="space-y-2 max-h-64 overflow-y-auto">
            {files.map((uploadFile) => (
              <div
                key={uploadFile.id}
                className={`
                  flex items-center gap-3 p-3 rounded-lg
                  ${uploadFile.status === 'error'
                    ? 'bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800'
                    : uploadFile.status === 'success'
                      ? 'bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800'
                      : 'bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700'
                  }
                `}
              >
                {getFileIcon(uploadFile.file.name)}

                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-medium truncate">{uploadFile.file.name}</span>
                    <span className="text-xs text-gray-500 flex-shrink-0">
                      {formatSize(uploadFile.file.size)}
                    </span>
                  </div>

                  {uploadFile.status === 'uploading' && (
                    <div className="mt-1">
                      <div className="h-1.5 bg-gray-200 dark:bg-gray-600 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-primary-600 transition-all duration-300"
                          style={{ width: `${uploadFile.progress}%` }}
                        />
                      </div>
                    </div>
                  )}

                  {uploadFile.status === 'error' && uploadFile.error && (
                    <p className="text-xs text-red-600 dark:text-red-400 mt-1">
                      {uploadFile.error}
                    </p>
                  )}
                </div>

                <div className="flex items-center gap-2 flex-shrink-0">
                  {uploadFile.status === 'uploading' && (
                    <Loader2 className="w-5 h-5 text-primary-600 animate-spin" />
                  )}
                  {uploadFile.status === 'success' && (
                    <CheckCircle className="w-5 h-5 text-green-600" />
                  )}
                  {uploadFile.status === 'error' && (
                    <AlertCircle className="w-5 h-5 text-red-600" />
                  )}
                  {(uploadFile.status === 'pending' || uploadFile.status === 'error') && (
                    <button
                      onClick={() => removeFile(uploadFile.id)}
                      className="p-1 text-gray-400 hover:text-gray-600"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Upload Button */}
      {pendingCount > 0 && (
        <button
          onClick={handleUpload}
          disabled={uploading || disabled}
          className="w-full btn btn-primary py-3"
        >
          {uploading ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin mr-2" />
              업로드 중...
            </>
          ) : (
            <>
              <Upload className="w-5 h-5 mr-2" />
              {pendingCount}개 파일 업로드
            </>
          )}
        </button>
      )}
    </div>
  )
}
