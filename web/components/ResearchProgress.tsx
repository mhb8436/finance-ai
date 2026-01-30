'use client'

import { useEffect, useState, useCallback } from 'react'
import {
  CheckCircle,
  Circle,
  Loader2,
  XCircle,
  ChevronDown,
  ChevronUp,
} from 'lucide-react'
import type { ResearchStatus, ResearchProgress as ProgressType } from '@/types'

interface StageInfo {
  id: string
  label: string
  description: string
}

const STAGES: StageInfo[] = [
  { id: 'rephrase', label: '분석 계획', description: '분석 주제를 명확하게 정리합니다' },
  { id: 'decompose', label: '분석 항목 분해', description: '세부 분석 항목으로 분할합니다' },
  { id: 'research', label: '데이터 수집', description: '주가, 재무, 뉴스 데이터를 수집합니다' },
  { id: 'notes', label: '분석 수행', description: '기술적/기본적 분석을 수행합니다' },
  { id: 'report', label: '리포트 생성', description: '종합 투자 리포트를 작성합니다' },
]

// Event type to user-friendly label mapping
const EVENT_LABELS: Record<string, string> = {
  stage_start: '시작',
  stage_complete: '완료',
  stage_error: '오류',
  tool_call: '도구 호출',
  tool_result: '결과 수신',
  llm_call: 'AI 분석 중',
  llm_response: 'AI 응답',
  progress: '진행 중',
  thinking: '분석 중',
  researching: '리서치 중',
}

// Get user-friendly event label
const getEventLabel = (event: string | undefined): string => {
  if (!event) return ''
  // Check for exact match
  if (EVENT_LABELS[event]) return EVENT_LABELS[event]
  // Check for partial match (e.g., "rephrase_stage_start" -> "시작")
  for (const [key, label] of Object.entries(EVENT_LABELS)) {
    if (event.toLowerCase().includes(key)) return label
  }
  // Return original if no match, but clean up underscores
  return event.replace(/_/g, ' ')
}

interface ResearchProgressProps {
  status: ResearchStatus
  currentStage: string | null
  progress: ProgressType | null
  error: string | null
  className?: string
}

export default function ResearchProgress({
  status,
  currentStage,
  progress,
  error,
  className = '',
}: ResearchProgressProps) {
  const [expandedStage, setExpandedStage] = useState<string | null>(null)

  const getStageStatus = useCallback(
    (stageId: string): 'pending' | 'running' | 'completed' | 'failed' => {
      if (status === 'failed') {
        const currentIdx = STAGES.findIndex((s) =>
          currentStage?.toLowerCase().includes(s.id)
        )
        const stageIdx = STAGES.findIndex((s) => s.id === stageId)
        if (stageIdx < currentIdx) return 'completed'
        if (stageIdx === currentIdx) return 'failed'
        return 'pending'
      }

      if (status === 'completed') return 'completed'
      if (status === 'pending') return 'pending'

      // Running status
      const currentIdx = STAGES.findIndex((s) =>
        currentStage?.toLowerCase().includes(s.id)
      )
      const stageIdx = STAGES.findIndex((s) => s.id === stageId)

      if (stageIdx < currentIdx) return 'completed'
      if (stageIdx === currentIdx) return 'running'
      return 'pending'
    },
    [status, currentStage]
  )

  const getStageIcon = (stageStatus: 'pending' | 'running' | 'completed' | 'failed') => {
    switch (stageStatus) {
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-500" />
      case 'running':
        return <Loader2 className="w-5 h-5 text-primary-600 animate-spin" />
      case 'failed':
        return <XCircle className="w-5 h-5 text-red-500" />
      default:
        return <Circle className="w-5 h-5 text-gray-300" />
    }
  }

  const completedCount = STAGES.filter(
    (stage) => getStageStatus(stage.id) === 'completed'
  ).length
  const progressPercent = (completedCount / STAGES.length) * 100

  return (
    <div className={`bg-white dark:bg-gray-800 rounded-lg shadow p-6 ${className}`}>
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold">분석 진행 상황</h3>
        <StatusBadge status={status} />
      </div>

      {/* Progress bar */}
      <div className="mb-6">
        <div className="flex justify-between text-sm text-gray-500 mb-1">
          <span>진행률</span>
          <span>{Math.round(progressPercent)}%</span>
        </div>
        <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
          <div
            className={`h-2 rounded-full transition-all duration-500 ${
              status === 'failed'
                ? 'bg-red-500'
                : status === 'completed'
                ? 'bg-green-500'
                : 'bg-primary-600'
            }`}
            style={{ width: `${progressPercent}%` }}
          />
        </div>
      </div>

      {/* Stages */}
      <div className="space-y-3">
        {STAGES.map((stage, index) => {
          const stageStatus = getStageStatus(stage.id)
          const isExpanded = expandedStage === stage.id

          return (
            <div key={stage.id} className="border border-gray-200 dark:border-gray-700 rounded-lg">
              <button
                className="w-full flex items-center gap-3 p-3 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"
                onClick={() => setExpandedStage(isExpanded ? null : stage.id)}
              >
                {getStageIcon(stageStatus)}
                <div className="flex-1 text-left">
                  <div className="font-medium">{stage.label}</div>
                  <div className="text-sm text-gray-500">{stage.description}</div>
                </div>
                {stageStatus === 'running' && progress?.stage === stage.id && progress.event && (
                  <span className="text-xs text-primary-600 mr-2 whitespace-nowrap">
                    {getEventLabel(progress.event)}
                  </span>
                )}
                {isExpanded ? (
                  <ChevronUp className="w-4 h-4 text-gray-400" />
                ) : (
                  <ChevronDown className="w-4 h-4 text-gray-400" />
                )}
              </button>

              {isExpanded && stageStatus !== 'pending' && (
                <div className="px-3 pb-3 pt-1 border-t border-gray-200 dark:border-gray-700">
                  {stageStatus === 'running' && progress && (
                    <div className="text-sm">
                      <div className="flex items-center gap-2 text-primary-600">
                        <Loader2 className="w-3 h-3 animate-spin" />
                        <span className="whitespace-nowrap">
                          {getEventLabel(progress.event) || '처리 중'}
                        </span>
                      </div>
                      {progress.details && Object.keys(progress.details).length > 0 && (
                        <pre className="mt-2 p-2 bg-gray-100 dark:bg-gray-900 rounded text-xs overflow-x-auto max-h-32">
                          {JSON.stringify(progress.details, null, 2)}
                        </pre>
                      )}
                    </div>
                  )}
                  {stageStatus === 'completed' && (
                    <div className="text-sm text-green-600">
                      <CheckCircle className="w-4 h-4 inline mr-1" />
                      완료됨
                    </div>
                  )}
                  {stageStatus === 'failed' && error && (
                    <div className="text-sm text-red-600">
                      <XCircle className="w-4 h-4 inline mr-1" />
                      오류: {error}
                    </div>
                  )}
                </div>
              )}
            </div>
          )
        })}
      </div>

      {/* Error message */}
      {error && status === 'failed' && (
        <div className="mt-4 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
          <div className="flex items-start gap-2">
            <XCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
            <div>
              <div className="font-medium text-red-800 dark:text-red-200">오류 발생</div>
              <div className="text-sm text-red-600 dark:text-red-300">{error}</div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function StatusBadge({ status }: { status: ResearchStatus }) {
  const config = {
    pending: { label: '대기중', className: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200' },
    running: { label: '진행중', className: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200' },
    completed: { label: '완료', className: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' },
    failed: { label: '실패', className: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200' },
    cancelled: { label: '취소됨', className: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200' },
  }

  const { label, className } = config[status]

  return (
    <span className={`px-2 py-1 rounded-full text-xs font-medium ${className}`}>
      {label}
    </span>
  )
}
