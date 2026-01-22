'use client'

import { useState } from 'react'
import { Loader2, DollarSign, TrendingUp, TrendingDown, Minus, Target } from 'lucide-react'
import { analysisApi } from '@/lib/api'
import type { ValuationResponse } from '@/types'

interface ValuationAnalysisProps {
  symbol?: string
  market?: 'US' | 'KR'
  className?: string
}

export default function ValuationAnalysis({
  symbol: initialSymbol = '',
  market: initialMarket = 'US',
  className = '',
}: ValuationAnalysisProps) {
  const [symbol, setSymbol] = useState(initialSymbol)
  const [market, setMarket] = useState<'US' | 'KR'>(initialMarket)
  const [quick, setQuick] = useState(true)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<ValuationResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleAnalyze = async () => {
    if (!symbol.trim()) {
      setError('종목 코드를 입력해주세요')
      return
    }

    setLoading(true)
    setError(null)
    setResult(null)

    const response = await analysisApi.valuation({
      symbol: symbol.toUpperCase(),
      market,
      quick,
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

  const formatCurrency = (value?: number, currency: string = '$') => {
    if (value === undefined || value === null) return 'N/A'
    return `${currency}${value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
  }

  const formatPercent = (value?: number) => {
    if (value === undefined || value === null) return 'N/A'
    const sign = value >= 0 ? '+' : ''
    return `${sign}${value.toFixed(1)}%`
  }

  const getValuationColor = (status?: string) => {
    if (!status) return 'text-gray-500'
    const lower = status.toLowerCase()
    if (lower.includes('undervalued') || lower.includes('저평가')) return 'text-green-600'
    if (lower.includes('overvalued') || lower.includes('고평가')) return 'text-red-600'
    return 'text-gray-500'
  }

  const getValuationBgColor = (status?: string) => {
    if (!status) return 'bg-gray-100 dark:bg-gray-700'
    const lower = status.toLowerCase()
    if (lower.includes('undervalued') || lower.includes('저평가')) return 'bg-green-100 dark:bg-green-900/30'
    if (lower.includes('overvalued') || lower.includes('고평가')) return 'bg-red-100 dark:bg-red-900/30'
    return 'bg-gray-100 dark:bg-gray-700'
  }

  const getValuationIcon = (status?: string) => {
    if (!status) return <Minus className="w-6 h-6" />
    const lower = status.toLowerCase()
    if (lower.includes('undervalued') || lower.includes('저평가')) return <TrendingUp className="w-6 h-6" />
    if (lower.includes('overvalued') || lower.includes('고평가')) return <TrendingDown className="w-6 h-6" />
    return <Minus className="w-6 h-6" />
  }

  const currency = market === 'KR' ? '₩' : '$'

  return (
    <div className={`card ${className}`}>
      <div className="flex items-center gap-2 mb-4">
        <DollarSign className="w-5 h-5 text-primary-600" />
        <h2 className="text-lg font-semibold">밸류에이션 분석</h2>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
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
            <option value="quick">빠른 분석</option>
            <option value="full">상세 분석 (DCF)</option>
          </select>
        </div>
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
          '밸류에이션 분석 실행'
        )}
      </button>

      {error && (
        <div className="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg text-red-600 dark:text-red-400 mb-4">
          {error}
        </div>
      )}

      {result && result.success && (
        <div className="space-y-4">
          <div className={`p-4 rounded-lg ${getValuationBgColor(result.valuation_status)}`}>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className={getValuationColor(result.valuation_status)}>
                  {getValuationIcon(result.valuation_status)}
                </div>
                <div>
                  <div className="text-2xl font-bold">
                    {result.valuation_status || 'N/A'}
                  </div>
                  <div className="text-sm text-gray-500">
                    {result.recommendation || ''}
                  </div>
                </div>
              </div>
              {result.upside_potential !== undefined && (
                <div className="text-right">
                  <div className="text-sm text-gray-500">상승 여력</div>
                  <div className={`text-xl font-bold ${result.upside_potential >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {formatPercent(result.upside_potential)}
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
              <div className="text-xs text-gray-500 mb-1">적정가</div>
              <div className="text-lg font-semibold text-primary-600">
                {formatCurrency(result.fair_value_base, currency)}
              </div>
            </div>
            <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
              <div className="text-xs text-gray-500 mb-1">적정가 (하단)</div>
              <div className="text-lg font-semibold">
                {formatCurrency(result.fair_value_low, currency)}
              </div>
            </div>
            <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
              <div className="text-xs text-gray-500 mb-1">적정가 (상단)</div>
              <div className="text-lg font-semibold">
                {formatCurrency(result.fair_value_high, currency)}
              </div>
            </div>
          </div>

          {result.methods_used && result.methods_used.length > 0 && (
            <div>
              <div className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 flex items-center gap-2">
                <Target className="w-4 h-4" />
                사용된 밸류에이션 방법
              </div>
              <div className="space-y-2">
                {result.methods_used.map((method, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between p-2 bg-gray-50 dark:bg-gray-800 rounded"
                  >
                    <span className="text-sm">{method.method}</span>
                    <div className="flex items-center gap-4">
                      <span className="text-sm font-medium">
                        {formatCurrency(method.value, currency)}
                      </span>
                      <span className="text-xs text-gray-500">
                        가중치: {(method.weight * 100).toFixed(0)}%
                      </span>
                    </div>
                  </div>
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
