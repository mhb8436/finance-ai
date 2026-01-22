'use client'

import { useState } from 'react'
import {
  Loader2,
  Star,
  TrendingUp,
  TrendingDown,
  Minus,
  AlertTriangle,
  Zap,
  Target,
  Shield,
} from 'lucide-react'
import { analysisApi } from '@/lib/api'
import type { RecommendationResponse, InvestmentStyle, TimeHorizon } from '@/types'

interface StockRecommendationProps {
  symbol?: string
  market?: 'US' | 'KR'
  className?: string
}

const STYLE_LABELS: Record<InvestmentStyle, string> = {
  growth: '성장주',
  value: '가치주',
  momentum: '모멘텀',
  balanced: '균형',
}

const HORIZON_LABELS: Record<TimeHorizon, string> = {
  short: '단기 (3개월 미만)',
  medium: '중기 (3~12개월)',
  long: '장기 (1년 이상)',
}

export default function StockRecommendation({
  symbol: initialSymbol = '',
  market: initialMarket = 'US',
  className = '',
}: StockRecommendationProps) {
  const [symbol, setSymbol] = useState(initialSymbol)
  const [market, setMarket] = useState<'US' | 'KR'>(initialMarket)
  const [investmentStyle, setInvestmentStyle] = useState<InvestmentStyle>('balanced')
  const [timeHorizon, setTimeHorizon] = useState<TimeHorizon>('medium')
  const [quick, setQuick] = useState(true)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<RecommendationResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleAnalyze = async () => {
    if (!symbol.trim()) {
      setError('종목 코드를 입력해주세요')
      return
    }

    setLoading(true)
    setError(null)
    setResult(null)

    const response = quick
      ? await analysisApi.quickRecommend(symbol.toUpperCase(), market)
      : await analysisApi.recommend({
          symbol: symbol.toUpperCase(),
          market,
          investment_style: investmentStyle,
          time_horizon: timeHorizon,
          quick: false,
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

  const getRecommendationColor = (rec?: string) => {
    if (!rec) return 'text-gray-500'
    const lower = rec.toLowerCase()
    if (lower.includes('strong buy') || lower === '적극 매수') return 'text-green-600'
    if (lower.includes('buy') || lower === '매수') return 'text-green-500'
    if (lower.includes('hold') || lower === '보유') return 'text-gray-500'
    if (lower.includes('sell') && !lower.includes('strong')) return 'text-red-500'
    if (lower.includes('strong sell') || lower === '적극 매도') return 'text-red-600'
    return 'text-gray-500'
  }

  const getRecommendationBgColor = (rec?: string) => {
    if (!rec) return 'bg-gray-100 dark:bg-gray-700'
    const lower = rec.toLowerCase()
    if (lower.includes('strong buy') || lower === '적극 매수') return 'bg-green-100 dark:bg-green-900/30'
    if (lower.includes('buy') || lower === '매수') return 'bg-green-50 dark:bg-green-900/20'
    if (lower.includes('hold') || lower === '보유') return 'bg-gray-100 dark:bg-gray-700'
    if (lower.includes('sell') && !lower.includes('strong')) return 'bg-red-50 dark:bg-red-900/20'
    if (lower.includes('strong sell') || lower === '적극 매도') return 'bg-red-100 dark:bg-red-900/30'
    return 'bg-gray-100 dark:bg-gray-700'
  }

  const getRecommendationIcon = (rec?: string) => {
    if (!rec) return <Minus className="w-8 h-8" />
    const lower = rec.toLowerCase()
    if (lower.includes('buy')) return <TrendingUp className="w-8 h-8" />
    if (lower.includes('sell')) return <TrendingDown className="w-8 h-8" />
    return <Minus className="w-8 h-8" />
  }

  const formatCurrency = (value?: number, currency: string = '$') => {
    if (value === undefined || value === null) return 'N/A'
    return `${currency}${value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
  }

  const formatPercent = (value?: number) => {
    if (value === undefined || value === null) return 'N/A'
    const sign = value >= 0 ? '+' : ''
    return `${sign}${value.toFixed(1)}%`
  }

  const currency = market === 'KR' ? '₩' : '$'

  return (
    <div className={`card ${className}`}>
      <div className="flex items-center gap-2 mb-4">
        <Star className="w-5 h-5 text-primary-600" />
        <h2 className="text-lg font-semibold">종목 추천</h2>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-4">
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
            분석 모드
          </label>
          <select
            value={quick ? 'quick' : 'full'}
            onChange={(e) => setQuick(e.target.value === 'quick')}
            className="input w-full"
          >
            <option value="quick">빠른 분석 (밸류에이션 기반)</option>
            <option value="full">종합 분석</option>
          </select>
        </div>

        {!quick && (
          <>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                투자 스타일
              </label>
              <select
                value={investmentStyle}
                onChange={(e) => setInvestmentStyle(e.target.value as InvestmentStyle)}
                className="input w-full"
              >
                {Object.entries(STYLE_LABELS).map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                투자 기간
              </label>
              <select
                value={timeHorizon}
                onChange={(e) => setTimeHorizon(e.target.value as TimeHorizon)}
                className="input w-full"
              >
                {Object.entries(HORIZON_LABELS).map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </select>
            </div>
          </>
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
          '추천 분석 실행'
        )}
      </button>

      {error && (
        <div className="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg text-red-600 dark:text-red-400 mb-4">
          {error}
        </div>
      )}

      {result && result.success && (
        <div className="space-y-4">
          <div className={`p-6 rounded-lg ${getRecommendationBgColor(result.recommendation)}`}>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className={getRecommendationColor(result.recommendation)}>
                  {getRecommendationIcon(result.recommendation)}
                </div>
                <div>
                  <div className="text-3xl font-bold">
                    {result.recommendation || 'N/A'}
                  </div>
                  {result.overall_score !== undefined && (
                    <div className="text-sm text-gray-500 mt-1">
                      종합 점수: {result.overall_score.toFixed(0)} / 100
                    </div>
                  )}
                </div>
              </div>
              {result.confidence !== undefined && (
                <div className="text-right">
                  <div className="text-sm text-gray-500">신뢰도</div>
                  <div className="text-2xl font-bold">
                    {(result.confidence * 100).toFixed(0)}%
                  </div>
                </div>
              )}
            </div>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
              <div className="text-xs text-gray-500 mb-1">현재가</div>
              <div className="text-lg font-semibold">
                {formatCurrency(result.current_price, currency)}
              </div>
            </div>
            <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
              <div className="text-xs text-gray-500 mb-1 flex items-center gap-1">
                <Target className="w-3 h-3" />
                목표가
              </div>
              <div className="text-lg font-semibold text-primary-600">
                {formatCurrency(result.target_price, currency)}
              </div>
            </div>
            <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg col-span-2">
              <div className="text-xs text-gray-500 mb-1">상승 여력</div>
              <div className={`text-xl font-bold ${(result.upside_potential ?? 0) >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {formatPercent(result.upside_potential)}
              </div>
            </div>
          </div>

          {result.catalysts && result.catalysts.length > 0 && (
            <div>
              <div className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 flex items-center gap-2">
                <Zap className="w-4 h-4 text-green-500" />
                상승 촉매 요인
              </div>
              <ul className="space-y-1">
                {result.catalysts.map((catalyst, index) => (
                  <li
                    key={index}
                    className="flex items-start gap-2 text-sm text-gray-600 dark:text-gray-400"
                  >
                    <span className="text-green-500 mt-1">•</span>
                    {catalyst}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {result.risks && result.risks.length > 0 && (
            <div>
              <div className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-orange-500" />
                리스크 요인
              </div>
              <ul className="space-y-1">
                {result.risks.map((risk, index) => (
                  <li
                    key={index}
                    className="flex items-start gap-2 text-sm text-gray-600 dark:text-gray-400"
                  >
                    <span className="text-orange-500 mt-1">•</span>
                    {risk}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {result.summary && (
            <div>
              <div className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 flex items-center gap-2">
                <Shield className="w-4 h-4" />
                분석 요약
              </div>
              <p className="text-sm text-gray-600 dark:text-gray-400 whitespace-pre-line bg-gray-50 dark:bg-gray-800 p-4 rounded-lg">
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
