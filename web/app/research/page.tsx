'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { useRouter, useSearchParams } from 'next/navigation'
import {
  Search,
  Plus,
  Clock,
  CheckCircle,
  XCircle,
  Loader2,
  FileText,
  RefreshCw,
  Trash2,
} from 'lucide-react'
import { pipelineApi } from '@/lib/api'
import type { ResearchListItem, ResearchStatus, PipelineResearchRequest } from '@/types'

export default function ResearchPage() {
  const router = useRouter()
  const searchParams = useSearchParams()

  // Read URL parameters
  const initialSymbol = searchParams.get('symbol') || ''
  const initialMarket = (searchParams.get('market') as 'US' | 'KR') || 'US'

  const [researches, setResearches] = useState<ResearchListItem[]>([])
  const [loading, setLoading] = useState(true)
  const [showNewForm, setShowNewForm] = useState(!!initialSymbol) // Auto-show form if symbol provided
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Form state - initialize with URL parameters
  const [formData, setFormData] = useState<PipelineResearchRequest>({
    topic: initialSymbol ? `${initialSymbol} 종목 분석 및 투자 전망` : '',
    symbols: [],
    market: initialMarket,
    context: '',
    max_topics: 10,
    language: 'ko',
  })
  const [symbolInput, setSymbolInput] = useState(initialSymbol)

  const fetchResearches = async () => {
    setLoading(true)
    const { data, error } = await pipelineApi.list()
    if (error) {
      setError(error)
    } else if (data) {
      setResearches(data)
    }
    setLoading(false)
  }

  useEffect(() => {
    fetchResearches()
  }, [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!formData.topic.trim()) return

    setSubmitting(true)
    setError(null)

    const { data, error } = await pipelineApi.start({
      ...formData,
      symbols: symbolInput.split(',').map((s) => s.trim()).filter(Boolean),
    })

    if (error) {
      setError(error)
      setSubmitting(false)
      return
    }

    if (data) {
      router.push(`/research/${data.research_id}`)
    }
  }

  const handleCancel = async (researchId: string) => {
    if (!confirm('분석을 취소하시겠습니까?')) return

    const { error } = await pipelineApi.cancel(researchId)
    if (error) {
      setError(error)
    } else {
      fetchResearches()
    }
  }

  const getStatusIcon = (status: ResearchStatus) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-500" />
      case 'running':
        return <Loader2 className="w-5 h-5 text-blue-500 animate-spin" />
      case 'failed':
        return <XCircle className="w-5 h-5 text-red-500" />
      case 'cancelled':
        return <XCircle className="w-5 h-5 text-yellow-500" />
      default:
        return <Clock className="w-5 h-5 text-gray-400" />
    }
  }

  const getStatusLabel = (status: ResearchStatus) => {
    const labels: Record<ResearchStatus, string> = {
      pending: '대기중',
      running: '진행중',
      completed: '완료',
      failed: '실패',
      cancelled: '취소됨',
    }
    return labels[status]
  }

  return (
    <main className="flex-1 p-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold">AI 종목 리서치</h1>
          <p className="text-gray-500 mt-1">
            AI 멀티 에이전트 기반 종합 주식 분석 리포트
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={fetchResearches}
            className="btn btn-secondary flex items-center gap-2"
            disabled={loading}
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            새로고침
          </button>
          <button
            onClick={() => setShowNewForm(!showNewForm)}
            className="btn btn-primary flex items-center gap-2"
          >
            <Plus className="w-4 h-4" />
            새 분석 시작
          </button>
        </div>
      </div>

      {/* Error message */}
      {error && (
        <div className="mb-6 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg text-red-600 dark:text-red-400">
          {error}
        </div>
      )}

      {/* New Research Form */}
      {showNewForm && (
        <div className="mb-8 bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-4">새 종목 분석</h2>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1">분석 주제 *</label>
              <input
                type="text"
                value={formData.topic}
                onChange={(e) => setFormData({ ...formData, topic: e.target.value })}
                placeholder="예: 삼성전자 2024년 실적 분석 및 투자 전망"
                className="input"
                required
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium mb-1">종목 코드 (쉼표로 구분)</label>
                <input
                  type="text"
                  value={symbolInput}
                  onChange={(e) => setSymbolInput(e.target.value)}
                  placeholder="예: AAPL, MSFT 또는 005930, 000660"
                  className="input"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">시장</label>
                <select
                  value={formData.market}
                  onChange={(e) => setFormData({ ...formData, market: e.target.value as 'US' | 'KR' | 'Both' })}
                  className="input"
                >
                  <option value="US">미국 (NYSE/NASDAQ)</option>
                  <option value="KR">한국 (KRX)</option>
                  <option value="Both">미국 + 한국</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">보고서 언어</label>
                <select
                  value={formData.language}
                  onChange={(e) => setFormData({ ...formData, language: e.target.value as 'ko' | 'en' })}
                  className="input"
                >
                  <option value="ko">한국어</option>
                  <option value="en">English</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">추가 컨텍스트 (선택)</label>
              <textarea
                value={formData.context}
                onChange={(e) => setFormData({ ...formData, context: e.target.value })}
                placeholder="분석에 포함할 특정 관점이나 제약 조건을 입력하세요"
                className="input min-h-[80px]"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">
                분석 상세도: {formData.max_topics}
              </label>
              <input
                type="range"
                min="3"
                max="20"
                value={formData.max_topics}
                onChange={(e) => setFormData({ ...formData, max_topics: parseInt(e.target.value) })}
                className="w-full"
              />
              <div className="flex justify-between text-xs text-gray-500">
                <span>3 (빠름)</span>
                <span>20 (상세)</span>
              </div>
            </div>

            <div className="flex items-center justify-end gap-2 pt-4 border-t border-gray-200 dark:border-gray-700">
              <button
                type="button"
                onClick={() => setShowNewForm(false)}
                className="btn btn-secondary"
              >
                취소
              </button>
              <button
                type="submit"
                className="btn btn-primary flex items-center gap-2"
                disabled={submitting || !formData.topic.trim()}
              >
                {submitting && <Loader2 className="w-4 h-4 animate-spin" />}
                분석 시작
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Research List */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
        <div className="border-b border-gray-200 dark:border-gray-700 p-4">
          <div className="flex items-center gap-2">
            <FileText className="w-5 h-5 text-primary-600" />
            <h2 className="font-semibold">리서치 목록</h2>
            <span className="text-sm text-gray-500">({researches.length}개)</span>
          </div>
        </div>

        {loading ? (
          <div className="p-8 text-center">
            <Loader2 className="w-8 h-8 mx-auto animate-spin text-primary-600" />
            <p className="mt-2 text-gray-500">불러오는 중...</p>
          </div>
        ) : researches.length === 0 ? (
          <div className="p-8 text-center text-gray-500">
            <Search className="w-12 h-12 mx-auto mb-3 text-gray-300" />
            <p className="mb-2">아직 리서치 리포트가 없습니다</p>
            <p className="text-sm">위의 "새 분석 시작" 버튼을 클릭하여 첫 번째 종목 분석을 시작하세요</p>
          </div>
        ) : (
          <div className="divide-y divide-gray-200 dark:divide-gray-700">
            {researches.map((research) => (
              <div
                key={research.research_id}
                className="p-4 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"
              >
                <div className="flex items-start justify-between">
                  <Link href={`/research/${research.research_id}`} className="flex-1">
                    <div className="flex items-center gap-3">
                      {getStatusIcon(research.status)}
                      <div>
                        <h3 className="font-medium hover:text-primary-600 transition-colors">
                          {research.topic}
                        </h3>
                        <div className="flex items-center gap-4 mt-1 text-sm text-gray-500">
                          <span>{getStatusLabel(research.status)}</span>
                          <span>
                            시작: {new Date(research.created_at).toLocaleString('ko-KR')}
                          </span>
                          {research.completed_at && (
                            <span>
                              완료: {new Date(research.completed_at).toLocaleString('ko-KR')}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  </Link>
                  {(research.status === 'pending' || research.status === 'running') && (
                    <button
                      onClick={() => handleCancel(research.research_id)}
                      className="p-2 text-gray-400 hover:text-red-500 transition-colors"
                      title="분석 취소"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </main>
  )
}
