'use client'

import { useState, useEffect, useCallback } from 'react'
import {
  Database,
  Plus,
  Trash2,
  Upload,
  Search,
  FileText,
  Loader2,
  FolderOpen,
  ChevronRight,
  X,
  File,
  CheckCircle,
} from 'lucide-react'
import { knowledgeBaseApi } from '@/lib/api'
import type { KnowledgeBase, KBDocument, KBSearchResponse } from '@/types'
import FileUpload from '@/components/FileUpload'

export default function KnowledgePage() {
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBase[]>([])
  const [selectedKB, setSelectedKB] = useState<string | null>(null)
  const [documents, setDocuments] = useState<KBDocument[]>([])
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [searching, setSearching] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Create KB form
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [newKBName, setNewKBName] = useState('')
  const [newKBDescription, setNewKBDescription] = useState('')

  // Search
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResult, setSearchResult] = useState<KBSearchResponse | null>(null)

  // Upload - drag state moved to FileUpload component

  const loadKnowledgeBases = useCallback(async () => {
    setLoading(true)
    const response = await knowledgeBaseApi.list()
    if (response.data) {
      setKnowledgeBases(response.data)
    } else if (response.error) {
      setError(response.error)
    }
    setLoading(false)
  }, [])

  const loadDocuments = useCallback(async (kbName: string) => {
    const response = await knowledgeBaseApi.listDocuments(kbName)
    if (response.data) {
      setDocuments(response.data)
    }
  }, [])

  useEffect(() => {
    loadKnowledgeBases()
  }, [loadKnowledgeBases])

  useEffect(() => {
    if (selectedKB) {
      loadDocuments(selectedKB)
      setSearchResult(null)
      setSearchQuery('')
    }
  }, [selectedKB, loadDocuments])

  const handleCreateKB = async () => {
    if (!newKBName.trim()) return

    const response = await knowledgeBaseApi.create(newKBName.trim(), newKBDescription)
    if (response.data) {
      await loadKnowledgeBases()
      setNewKBName('')
      setNewKBDescription('')
      setShowCreateForm(false)
      setSelectedKB(newKBName.trim())
    } else if (response.error) {
      setError(response.error)
    }
  }

  const handleDeleteKB = async (kbName: string) => {
    if (!confirm(`"${kbName}" 지식 베이스를 삭제하시겠습니까?`)) return

    const response = await knowledgeBaseApi.delete(kbName)
    if (response.data) {
      await loadKnowledgeBases()
      if (selectedKB === kbName) {
        setSelectedKB(null)
        setDocuments([])
      }
    } else if (response.error) {
      setError(response.error)
    }
  }

  const handleFileUpload = async (files: FileList | File[]) => {
    if (!selectedKB || files.length === 0) return

    setUploading(true)
    setError(null)

    const fileArray = Array.from(files)

    if (fileArray.length === 1) {
      const response = await knowledgeBaseApi.uploadDocument(selectedKB, fileArray[0])
      if (response.error) {
        setError(response.error)
      }
    } else {
      const response = await knowledgeBaseApi.uploadMultipleDocuments(selectedKB, fileArray)
      if (response.error) {
        setError(response.error)
      }
    }

    await loadDocuments(selectedKB)
    await loadKnowledgeBases()
    setUploading(false)
  }

  const handleDeleteDocument = async (filename: string) => {
    if (!selectedKB) return
    if (!confirm(`"${filename}" 파일을 삭제하시겠습니까?`)) return

    const response = await knowledgeBaseApi.deleteDocument(selectedKB, filename)
    if (response.data) {
      await loadDocuments(selectedKB)
      await loadKnowledgeBases()
    } else if (response.error) {
      setError(response.error)
    }
  }

  const handleSearch = async () => {
    if (!selectedKB || !searchQuery.trim()) return

    setSearching(true)
    const response = await knowledgeBaseApi.search(selectedKB, {
      query: searchQuery,
      top_k: 5,
      generate_answer: true,
    })

    if (response.data) {
      setSearchResult(response.data)
    } else if (response.error) {
      setError(response.error)
    }
    setSearching(false)
  }

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  const formatDate = (timestamp: number) => {
    return new Date(timestamp * 1000).toLocaleDateString('ko-KR', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    })
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <Database className="w-8 h-8 text-primary-600" />
            <h1 className="text-2xl md:text-3xl font-bold text-gray-900 dark:text-white">
              Knowledge Base
            </h1>
          </div>
          <p className="text-gray-600 dark:text-gray-400">
            문서를 업로드하고 AI가 답변할 수 있는 지식 베이스를 구축합니다
          </p>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg text-red-600 dark:text-red-400 flex items-center justify-between">
            <span>{error}</span>
            <button onClick={() => setError(null)}>
              <X className="w-4 h-4" />
            </button>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Knowledge Base List */}
          <div className="lg:col-span-1">
            <div className="card">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold">지식 베이스</h2>
                <button
                  onClick={() => setShowCreateForm(!showCreateForm)}
                  className="btn btn-primary btn-sm"
                >
                  <Plus className="w-4 h-4" />
                </button>
              </div>

              {showCreateForm && (
                <div className="mb-4 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                  <input
                    type="text"
                    value={newKBName}
                    onChange={(e) => setNewKBName(e.target.value)}
                    placeholder="이름"
                    className="input w-full mb-2"
                  />
                  <input
                    type="text"
                    value={newKBDescription}
                    onChange={(e) => setNewKBDescription(e.target.value)}
                    placeholder="설명 (선택)"
                    className="input w-full mb-2"
                  />
                  <div className="flex gap-2">
                    <button onClick={handleCreateKB} className="btn btn-primary btn-sm flex-1">
                      생성
                    </button>
                    <button
                      onClick={() => setShowCreateForm(false)}
                      className="btn btn-secondary btn-sm"
                    >
                      취소
                    </button>
                  </div>
                </div>
              )}

              {loading ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="w-6 h-6 animate-spin text-primary-600" />
                </div>
              ) : knowledgeBases.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <FolderOpen className="w-12 h-12 mx-auto mb-2 opacity-50" />
                  <p>지식 베이스가 없습니다</p>
                  <p className="text-sm">새로운 지식 베이스를 생성하세요</p>
                </div>
              ) : (
                <div className="space-y-2">
                  {knowledgeBases.map((kb) => (
                    <div
                      key={kb.name}
                      className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                        selectedKB === kb.name
                          ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20'
                          : 'border-gray-200 dark:border-gray-700 hover:border-gray-300'
                      }`}
                      onClick={() => setSelectedKB(kb.name)}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <Database className="w-4 h-4 text-primary-600" />
                          <span className="font-medium">{kb.name}</span>
                        </div>
                        <div className="flex items-center gap-1">
                          <button
                            onClick={(e) => {
                              e.stopPropagation()
                              handleDeleteKB(kb.name)
                            }}
                            className="p-1 text-gray-400 hover:text-red-500"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                          <ChevronRight className="w-4 h-4 text-gray-400" />
                        </div>
                      </div>
                      <div className="mt-1 text-xs text-gray-500">
                        {kb.document_count}개 문서 • {kb.total_chunks}개 청크
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Main Content */}
          <div className="lg:col-span-2 space-y-6">
            {selectedKB ? (
              <>
                {/* Upload Section */}
                <div className="card">
                  <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                    <Upload className="w-5 h-5 text-primary-600" />
                    문서 업로드
                  </h3>
                  <FileUpload
                    onUpload={async (files) => {
                      await handleFileUpload(files)
                    }}
                    accept=".pdf,.txt,.md"
                    maxFiles={10}
                    maxSize={50}
                    disabled={uploading}
                  />
                </div>

                {/* Documents List */}
                <div className="card">
                  <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                    <FileText className="w-5 h-5 text-primary-600" />
                    문서 목록
                  </h3>

                  {documents.length === 0 ? (
                    <div className="text-center py-8 text-gray-500">
                      <File className="w-12 h-12 mx-auto mb-2 opacity-50" />
                      <p>업로드된 문서가 없습니다</p>
                    </div>
                  ) : (
                    <div className="space-y-2">
                      {documents.map((doc) => (
                        <div
                          key={doc.filename}
                          className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg"
                        >
                          <div className="flex items-center gap-3">
                            <FileText className="w-5 h-5 text-gray-400" />
                            <div>
                              <div className="font-medium">{doc.filename}</div>
                              <div className="text-xs text-gray-500">
                                {formatFileSize(doc.size)} • {formatDate(doc.modified)}
                              </div>
                            </div>
                          </div>
                          <button
                            onClick={() => handleDeleteDocument(doc.filename)}
                            className="p-2 text-gray-400 hover:text-red-500"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* Search Section */}
                <div className="card">
                  <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                    <Search className="w-5 h-5 text-primary-600" />
                    지식 검색
                  </h3>

                  <div className="flex gap-2 mb-4">
                    <input
                      type="text"
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                      placeholder="질문을 입력하세요..."
                      className="input flex-1"
                    />
                    <button
                      onClick={handleSearch}
                      disabled={searching || !searchQuery.trim()}
                      className="btn btn-primary"
                    >
                      {searching ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      ) : (
                        <Search className="w-4 h-4" />
                      )}
                    </button>
                  </div>

                  {searchResult && (
                    <div className="space-y-4">
                      <div className="p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg">
                        <div className="flex items-start gap-2">
                          <CheckCircle className="w-5 h-5 text-green-600 mt-0.5" />
                          <div>
                            <div className="font-medium text-green-800 dark:text-green-200">
                              AI 답변
                            </div>
                            <p className="text-gray-700 dark:text-gray-300 whitespace-pre-line mt-1">
                              {searchResult.answer}
                            </p>
                          </div>
                        </div>
                      </div>

                      {searchResult.sources.length > 0 && (
                        <div>
                          <div className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                            참고 소스 ({searchResult.num_results}개)
                          </div>
                          <div className="space-y-2">
                            {searchResult.sources.map((source, index) => (
                              <div
                                key={index}
                                className="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg text-sm"
                              >
                                <div className="flex items-center gap-2 text-gray-500 mb-1">
                                  <FileText className="w-4 h-4" />
                                  <span>{source.source}</span>
                                  <span className="text-xs px-2 py-0.5 bg-gray-200 dark:bg-gray-700 rounded">
                                    {(source.relevance * 100).toFixed(0)}% 관련
                                  </span>
                                </div>
                                <p className="text-gray-600 dark:text-gray-400 line-clamp-3">
                                  {source.content}
                                </p>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </>
            ) : (
              <div className="card">
                <div className="text-center py-12 text-gray-500">
                  <Database className="w-16 h-16 mx-auto mb-4 opacity-50" />
                  <p className="text-lg">지식 베이스를 선택하세요</p>
                  <p className="text-sm mt-2">
                    왼쪽에서 지식 베이스를 선택하거나 새로 생성하세요
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
