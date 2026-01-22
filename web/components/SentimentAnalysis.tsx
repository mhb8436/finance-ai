'use client'

import { useState } from 'react'
import { Loader2, TrendingUp, TrendingDown, Minus, Newspaper, Youtube } from 'lucide-react'
import { analysisApi } from '@/lib/api'
import type { SentimentResponse } from '@/types'

interface SentimentAnalysisProps {
  symbol?: string
  market?: 'US' | 'KR'
  className?: string
}

export default function SentimentAnalysis({
  symbol: initialSymbol = '',
  market: initialMarket = 'US',
  className = '',
}: SentimentAnalysisProps) {
  const [symbol, setSymbol] = useState(initialSymbol)
  const [market, setMarket] = useState<'US' | 'KR'>(initialMarket)
  const [source, setSource] = useState<'news' | 'youtube' | 'combined'>('combined')
  const [youtubeChannel, setYoutubeChannel] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<SentimentResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleAnalyze = async () => {
    if (!symbol.trim()) {
      setError('종목 코드를 입력해주세요')
      return
    }

    setLoading(true)
    setError(null)
    setResult(null)

    const response = await analysisApi.sentiment({
      symbol: symbol.toUpperCase(),
      market,
      source,
      youtube_channel: youtubeChannel || undefined,
    })

    setLoading(false)

    if (response.error) {
      setError(response.error)
      return
    }

    if (response.data) {
      setResult(response.data)
    }
  }

  const getSentimentColor = (score?: number) => {
    if (score === undefined) return 'text-gray-500'
    if (score >= 0.7) return 'text-green-600'
    if (score >= 0.5) return 'text-green-500'
    if (score >= 0.4) return 'text-gray-500'
    if (score >= 0.3) return 'text-red-500'
    return 'text-red-600'
  }

  const getSentimentIcon = (score?: number) => {
    if (score === undefined) return <Minus className="w-6 h-6" />
    if (score >= 0.5) return <TrendingUp className="w-6 h-6" />
    if (score >= 0.4) return <Minus className="w-6 h-6" />
    return <TrendingDown className="w-6 h-6" />
  }

  const getSentimentBgColor = (score?: number) => {
    if (score === undefined) return 'bg-gray-100 dark:bg-gray-700'
    if (score >= 0.7) return 'bg-green-100 dark:bg-green-900/30'
    if (score >= 0.5) return 'bg-green-50 dark:bg-green-900/20'
    if (score >= 0.4) return 'bg-gray-100 dark:bg-gray-700'
    if (score >= 0.3) return 'bg-red-50 dark:bg-red-900/20'
    return 'bg-red-100 dark:bg-red-900/30'
  }

  return (
    <div className={`card ${className}`}>
      <div className="flex items-center gap-2 mb-4">
        <Newspaper className="w-5 h-5 text-primary-600" />
        <h2 className="text-lg font-semibold">감성 분석</h2>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            종목 코드
          </label>
          <input
            type="text"
            value={symbol}
            onChange={(e) => setSymbol(e.target.value)}
            placeholder="예: AAPL, 005930"
            className="input w-full"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            시장
          </label>
          <select
            value={market}
            onChange={(e) => setMarket(e.target.value as 'US' | 'KR')}
            className="input w-full"
          >
            <option value="US">미국 (US)</option>
            <option value="KR">한국 (KR)</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            분석 소스
          </label>
          <select
            value={source}
            onChange={(e) => setSource(e.target.value as 'news' | 'youtube' | 'combined')}
            className="input w-full"
          >
            <option value="combined">뉴스 + 유튜브</option>
            <option value="news">뉴스만</option>
            <option value="youtube">유튜브만</option>
          </select>
        </div>

        {(source === 'youtube' || source === 'combined') && (
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              유튜브 채널 (선택)
            </label>
            <input
              type="text"
              value={youtubeChannel}
              onChange={(e) => setYoutubeChannel(e.target.value)}
              placeholder="채널 ID 또는 핸들"
              className="input w-full"
            />
          </div>
        )}
      </div>

      <button
        onClick={handleAnalyze}
        disabled={loading}
        className="btn btn-primary w-full mb-4"
      >
        {loading ? (
          <>
            <Loader2 className="w-4 h-4 animate-spin mr-2" />
            분석 중...
          </>
        ) : (
          '감성 분석 실행'
        )}
      </button>

      {error && (
        <div className="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg text-red-600 dark:text-red-400 mb-4">
          {error}
        </div>
      )}

      {result && result.success && (
        <div className="space-y-4">
          <div className={`p-4 rounded-lg ${getSentimentBgColor(result.sentiment_score)}`}>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className={getSentimentColor(result.sentiment_score)}>
                  {getSentimentIcon(result.sentiment_score)}
                </div>
                <div>
                  <div className="text-2xl font-bold">
                    {result.sentiment_label || 'N/A'}
                  </div>
                  <div className="text-sm text-gray-500">
                    점수: {result.sentiment_score?.toFixed(2) || 'N/A'}
                  </div>
                </div>
              </div>
              {result.confidence !== undefined && (
                <div className="text-right">
                  <div className="text-sm text-gray-500">신뢰도</div>
                  <div className="text-lg font-semibold">
                    {(result.confidence * 100).toFixed(0)}%
                  </div>
                </div>
              )}
            </div>
          </div>

          <div className="flex items-center gap-2 text-sm text-gray-500">
            {result.source === 'news' && <Newspaper className="w-4 h-4" />}
            {result.source === 'youtube' && <Youtube className="w-4 h-4" />}
            {result.source === 'combined' && (
              <>
                <Newspaper className="w-4 h-4" />
                <span>+</span>
                <Youtube className="w-4 h-4" />
              </>
            )}
            <span>소스: {result.source}</span>
          </div>

          {result.key_themes && result.key_themes.length > 0 && (
            <div>
              <div className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                주요 테마
              </div>
              <div className="flex flex-wrap gap-2">
                {result.key_themes.map((theme, index) => (
                  <span
                    key={index}
                    className="px-2 py-1 bg-gray-100 dark:bg-gray-700 rounded-full text-sm"
                  >
                    {theme}
                  </span>
                ))}
              </div>
            </div>
          )}

          {result.summary && (
            <div>
              <div className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                분석 요약
              </div>
              <p className="text-sm text-gray-600 dark:text-gray-400 whitespace-pre-line">
                {result.summary}
              </p>
            </div>
          )}
        </div>
      )}

      {result && !result.success && (
        <div className="p-3 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg text-yellow-600 dark:text-yellow-400">
          분석 결과를 가져올 수 없습니다.
        </div>
      )}
    </div>
  )
}
