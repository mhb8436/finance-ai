'use client'

import { useState, useEffect, useRef, useCallback } from 'react'
import { useParams, useRouter } from 'next/navigation'
import Link from 'next/link'
import {
  ArrowLeft,
  RefreshCw,
  Trash2,
  Loader2,
  Clock,
  Target,
  Globe,
} from 'lucide-react'
import { pipelineApi } from '@/lib/api'
import ResearchProgress from '@/components/ResearchProgress'
import ReportViewer from '@/components/ReportViewer'
import type { ResearchStatusResponse, WSEvent } from '@/types'

export default function ResearchDetailPage() {
  const params = useParams()
  const router = useRouter()
  const researchId = params.id as string

  const [research, setResearch] = useState<ResearchStatusResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [wsConnected, setWsConnected] = useState(false)

  const wsRef = useRef<WebSocket | null>(null)

  const fetchResearch = useCallback(async () => {
    setLoading(true)
    const { data, error } = await pipelineApi.get(researchId)
    if (error) {
      setError(error)
    } else if (data) {
      setResearch(data)
    }
    setLoading(false)
  }, [researchId])

  // Initial fetch
  useEffect(() => {
    fetchResearch()
  }, [fetchResearch])

  // WebSocket connection for real-time updates
  useEffect(() => {
    if (!research) return
    if (research.status === 'completed' || research.status === 'failed' || research.status === 'cancelled') {
      return
    }

    // Connect to WebSocket
    const ws = pipelineApi.createWebSocket(researchId)
    wsRef.current = ws

    ws.onopen = () => {
      setWsConnected(true)
      console.log('WebSocket connected')
    }

    ws.onmessage = (event) => {
      try {
        const data: WSEvent = JSON.parse(event.data)

        switch (data.type) {
          case 'connected':
            console.log('WebSocket: connected', data.research_id)
            break

          case 'current_state':
          case 'update':
            if ('data' in data && data.data) {
              setResearch(data.data)
            }
            break

          case 'final':
            setResearch((prev) =>
              prev
                ? {
                    ...prev,
                    status: data.status,
                    result: data.result,
                    error: data.error,
                  }
                : null
            )
            ws.close()
            break

          case 'error':
            setError(data.message)
            break

          case 'heartbeat':
            // Ignore heartbeats
            break
        }
      } catch (err) {
        console.error('WebSocket message parse error:', err)
      }
    }

    ws.onerror = (err) => {
      console.error('WebSocket error:', err)
      setWsConnected(false)
    }

    ws.onclose = () => {
      setWsConnected(false)
      console.log('WebSocket disconnected')
    }

    return () => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.close()
      }
    }
  }, [research?.status, researchId])

  const handleCancel = async () => {
    if (!confirm('분석을 취소하시겠습니까?')) return

    const { error } = await pipelineApi.cancel(researchId)
    if (error) {
      setError(error)
    } else {
      fetchResearch()
    }
  }

  if (loading && !research) {
    return (
      <main className="flex-1 p-8">
        <div className="flex items-center justify-center h-64">
          <Loader2 className="w-8 h-8 animate-spin text-primary-600" />
        </div>
      </main>
    )
  }

  if (error && !research) {
    return (
      <main className="flex-1 p-8">
        <div className="text-center">
          <div className="text-red-500 mb-4">{error}</div>
          <Link href="/research" className="btn btn-secondary">
            목록으로 돌아가기
          </Link>
        </div>
      </main>
    )
  }

  if (!research) {
    return (
      <main className="flex-1 p-8">
        <div className="text-center">
          <div className="text-gray-500 mb-4">리서치를 찾을 수 없습니다</div>
          <Link href="/research" className="btn btn-secondary">
            목록으로 돌아가기
          </Link>
        </div>
      </main>
    )
  }

  const isActive = research.status === 'pending' || research.status === 'running'

  return (
    <main className="flex-1 p-8">
      {/* Header */}
      <div className="mb-6">
        <Link
          href="/research"
          className="inline-flex items-center gap-2 text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 mb-4"
        >
          <ArrowLeft className="w-4 h-4" />
          리서치 목록으로
        </Link>

        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-bold">{research.topic}</h1>
            <div className="flex flex-wrap items-center gap-4 mt-2 text-sm text-gray-500">
              <span className="font-mono text-xs bg-gray-100 dark:bg-gray-700 px-2 py-1 rounded">
                {research.research_id}
              </span>
              {wsConnected && (
                <span className="flex items-center gap-1 text-green-500">
                  <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                  실시간 연결
                </span>
              )}
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={fetchResearch}
              className="btn btn-secondary flex items-center gap-2"
              disabled={loading}
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
              새로고침
            </button>
            {isActive && (
              <button
                onClick={handleCancel}
                className="btn btn-secondary text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 flex items-center gap-2"
              >
                <Trash2 className="w-4 h-4" />
                취소
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Error banner */}
      {error && (
        <div className="mb-6 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg text-red-600 dark:text-red-400">
          {error}
        </div>
      )}

      {/* Research Info */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <InfoCard
          icon={<Clock className="w-5 h-5" />}
          label="시작 시간"
          value={
            research.started_at
              ? new Date(research.started_at).toLocaleString('ko-KR')
              : research.created_at
              ? new Date(research.created_at).toLocaleString('ko-KR')
              : '-'
          }
        />
        <InfoCard
          icon={<Target className="w-5 h-5" />}
          label="현재 단계"
          value={research.current_stage || '대기 중'}
        />
        <InfoCard
          icon={<Globe className="w-5 h-5" />}
          label="완료 시간"
          value={
            research.completed_at
              ? new Date(research.completed_at).toLocaleString('ko-KR')
              : '-'
          }
        />
      </div>

      {/* Main content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Progress */}
        <div className="lg:col-span-1">
          <ResearchProgress
            status={research.status}
            currentStage={research.current_stage}
            progress={research.progress}
            error={research.error}
          />
        </div>

        {/* Report */}
        <div className="lg:col-span-2">
          {research.result ? (
            <ReportViewer result={research.result} />
          ) : (
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-8 text-center">
              {isActive ? (
                <>
                  <Loader2 className="w-12 h-12 mx-auto mb-4 text-primary-600 animate-spin" />
                  <p className="text-gray-500">분석 진행 중입니다...</p>
                  <p className="text-sm text-gray-400 mt-2">
                    {research.current_stage || '초기화 중'}
                  </p>
                </>
              ) : (
                <>
                  <div className="w-12 h-12 mx-auto mb-4 rounded-full bg-gray-100 dark:bg-gray-700 flex items-center justify-center">
                    <Target className="w-6 h-6 text-gray-400" />
                  </div>
                  <p className="text-gray-500">리포트가 아직 생성되지 않았습니다</p>
                </>
              )}
            </div>
          )}
        </div>
      </div>
    </main>
  )
}

function InfoCard({
  icon,
  label,
  value,
}: {
  icon: React.ReactNode
  label: string
  value: string
}) {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
      <div className="flex items-center gap-3">
        <div className="text-gray-400">{icon}</div>
        <div>
          <div className="text-xs text-gray-500 uppercase tracking-wide">{label}</div>
          <div className="font-medium">{value}</div>
        </div>
      </div>
    </div>
  )
}
