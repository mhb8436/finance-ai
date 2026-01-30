'use client'

import React, { useState } from 'react'
import {
  FileText,
  Copy,
  Check,
  Download,
  ChevronDown,
  ChevronUp,
  BarChart3,
  Clock,
  Target,
} from 'lucide-react'
import type { ResearchResult } from '@/types'

interface ReportViewerProps {
  result: ResearchResult
  className?: string
}

export default function ReportViewer({ result, className = '' }: ReportViewerProps) {
  const [copied, setCopied] = useState(false)
  const [showStats, setShowStats] = useState(false)

  const report = result.report
  const statistics = result.statistics

  const handleCopy = async () => {
    if (report?.report_content) {
      await navigator.clipboard.writeText(report.report_content)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  const handleDownload = () => {
    if (report?.report_content) {
      const blob = new Blob([report.report_content], { type: 'text/markdown' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url

      // Generate filename with date and topic/stock name
      const date = new Date().toISOString().split('T')[0]
      let topicName = report.main_topic || 'research_report'

      // Extract stock code if present (e.g., "네이버 (035420.KS)" or "삼성전자")
      const codeMatch = topicName.match(/\((\d{6})[^)]*\)/)
      if (codeMatch) {
        // Use stock code if found
        topicName = codeMatch[1]
      } else {
        // Clean up topic name for filename (remove special characters, limit length)
        topicName = topicName
          .replace(/[^\w\s가-힣]/g, '')
          .replace(/\s+/g, '_')
          .slice(0, 30)
      }

      a.download = `${date}_${topicName}_리서치리포트.md`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    }
  }

  if (!report) {
    return (
      <div className={`bg-white dark:bg-gray-800 rounded-lg shadow p-6 ${className}`}>
        <div className="text-center text-gray-500 py-8">
          <FileText className="w-12 h-12 mx-auto mb-3 text-gray-300" />
          <p>리포트가 아직 생성되지 않았습니다</p>
        </div>
      </div>
    )
  }

  return (
    <div className={`bg-white dark:bg-gray-800 rounded-lg shadow ${className}`}>
      {/* Header */}
      <div className="border-b border-gray-200 dark:border-gray-700 p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <FileText className="w-5 h-5 text-primary-600" />
            <h3 className="text-lg font-semibold">연구 리포트</h3>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handleCopy}
              className="btn btn-secondary text-sm flex items-center gap-1"
              title="클립보드에 복사"
            >
              {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
              {copied ? '복사됨' : '복사'}
            </button>
            <button
              onClick={handleDownload}
              className="btn btn-secondary text-sm flex items-center gap-1"
              title="마크다운 파일 다운로드"
            >
              <Download className="w-4 h-4" />
              다운로드
            </button>
          </div>
        </div>

        {/* Meta info */}
        <div className="mt-3 flex flex-wrap gap-4 text-sm text-gray-500">
          {report.main_topic && (
            <div className="flex items-center gap-1">
              <Target className="w-4 h-4" />
              <span>{report.main_topic}</span>
            </div>
          )}
          {report.generated_at && (
            <div className="flex items-center gap-1">
              <Clock className="w-4 h-4" />
              <span>{new Date(report.generated_at).toLocaleString('ko-KR')}</span>
            </div>
          )}
        </div>
      </div>

      {/* Executive Summary */}
      {report.executive_summary && (
        <div className="border-b border-gray-200 dark:border-gray-700 p-4 bg-primary-50 dark:bg-primary-900/20">
          <h4 className="font-semibold text-primary-800 dark:text-primary-200 mb-2">
            핵심 요약
          </h4>
          <p className="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap">
            {report.executive_summary}
          </p>
        </div>
      )}

      {/* Statistics */}
      {statistics && (
        <div className="border-b border-gray-200 dark:border-gray-700">
          <button
            onClick={() => setShowStats(!showStats)}
            className="w-full flex items-center justify-between p-4 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"
          >
            <div className="flex items-center gap-2">
              <BarChart3 className="w-4 h-4 text-gray-500" />
              <span className="font-medium">연구 통계</span>
            </div>
            {showStats ? (
              <ChevronUp className="w-4 h-4 text-gray-400" />
            ) : (
              <ChevronDown className="w-4 h-4 text-gray-400" />
            )}
          </button>
          {showStats && (
            <div className="px-4 pb-4 grid grid-cols-2 md:grid-cols-4 gap-4">
              <StatCard
                label="전체 토픽"
                value={statistics.total_topics}
              />
              <StatCard
                label="완료된 토픽"
                value={statistics.completed_topics}
                color="green"
              />
              <StatCard
                label="실패한 토픽"
                value={statistics.failed_topics}
                color={statistics.failed_topics > 0 ? 'red' : 'gray'}
              />
              <StatCard
                label="도구 호출"
                value={statistics.total_tool_calls}
              />
            </div>
          )}
        </div>
      )}

      {/* Report Content */}
      <div className="p-4">
        <div className="prose prose-sm dark:prose-invert max-w-none">
          <MarkdownRenderer content={report.report_content} />
        </div>
      </div>
    </div>
  )
}

function StatCard({
  label,
  value,
  color = 'gray',
}: {
  label: string
  value: number
  color?: 'gray' | 'green' | 'red'
}) {
  const colorClasses = {
    gray: 'bg-gray-100 dark:bg-gray-700',
    green: 'bg-green-100 dark:bg-green-900/30',
    red: 'bg-red-100 dark:bg-red-900/30',
  }

  return (
    <div className={`p-3 rounded-lg ${colorClasses[color]}`}>
      <div className="text-2xl font-bold">{value}</div>
      <div className="text-xs text-gray-500">{label}</div>
    </div>
  )
}

function MarkdownRenderer({ content }: { content: string }) {
  // Simple markdown rendering (for production, consider using react-markdown)
  const lines = content.split('\n')
  const elements: React.ReactElement[] = []
  let inCodeBlock = false
  let codeContent: string[] = []
  let codeLanguage = ''

  lines.forEach((line, index) => {
    // Code block handling
    if (line.startsWith('```')) {
      if (inCodeBlock) {
        elements.push(
          <pre key={index} className="bg-gray-100 dark:bg-gray-900 p-3 rounded-lg overflow-x-auto text-sm">
            <code>{codeContent.join('\n')}</code>
          </pre>
        )
        codeContent = []
        inCodeBlock = false
      } else {
        inCodeBlock = true
        codeLanguage = line.slice(3)
      }
      return
    }

    if (inCodeBlock) {
      codeContent.push(line)
      return
    }

    // Headers
    if (line.startsWith('# ')) {
      elements.push(
        <h1 key={index} className="text-2xl font-bold mt-6 mb-3">
          {line.slice(2)}
        </h1>
      )
      return
    }
    if (line.startsWith('## ')) {
      elements.push(
        <h2 key={index} className="text-xl font-bold mt-5 mb-2">
          {line.slice(3)}
        </h2>
      )
      return
    }
    if (line.startsWith('### ')) {
      elements.push(
        <h3 key={index} className="text-lg font-semibold mt-4 mb-2">
          {line.slice(4)}
        </h3>
      )
      return
    }

    // List items
    if (line.startsWith('- ') || line.startsWith('* ')) {
      elements.push(
        <li key={index} className="ml-4">
          {renderInlineMarkdown(line.slice(2))}
        </li>
      )
      return
    }

    // Numbered list
    const numberedMatch = line.match(/^(\d+)\.\s(.+)/)
    if (numberedMatch) {
      elements.push(
        <li key={index} className="ml-4 list-decimal">
          {renderInlineMarkdown(numberedMatch[2])}
        </li>
      )
      return
    }

    // Empty line
    if (line.trim() === '') {
      elements.push(<br key={index} />)
      return
    }

    // Regular paragraph
    elements.push(
      <p key={index} className="mb-2">
        {renderInlineMarkdown(line)}
      </p>
    )
  })

  return <>{elements}</>
}

function renderInlineMarkdown(text: string): React.ReactNode {
  // Bold
  text = text.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
  // Italic
  text = text.replace(/\*(.+?)\*/g, '<em>$1</em>')
  // Code
  text = text.replace(/`(.+?)`/g, '<code class="bg-gray-100 dark:bg-gray-900 px-1 rounded">$1</code>')

  return <span dangerouslySetInnerHTML={{ __html: text }} />
}
