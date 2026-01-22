'use client'

import { useState, useEffect, useCallback } from 'react'
import { useSearchParams } from 'next/navigation'
import Link from 'next/link'
import {
  ArrowLeft,
  TrendingUp,
  TrendingDown,
  Minus,
  RefreshCw,
  Loader2,
  BarChart3,
  Activity,
} from 'lucide-react'
import { analysisApi } from '@/lib/api'
import type { AnalysisResult } from '@/types'

interface IndicatorSignal {
  name: string
  value: number | string | null
  signal: 'buy' | 'sell' | 'neutral'
  description: string
}

export default function TechnicalAnalysisPage() {
  const searchParams = useSearchParams()
  const initialSymbol = searchParams.get('symbol') || ''
  const initialMarket = (searchParams.get('market') as 'US' | 'KR') || 'US'

  const [symbol, setSymbol] = useState(initialSymbol)
  const [market, setMarket] = useState<'US' | 'KR'>(initialMarket)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<AnalysisResult | null>(null)
  const [error, setError] = useState<string | null>(null)

  const analyzeStock = useCallback(async (sym: string, mkt: string) => {
    if (!sym.trim()) return

    setLoading(true)
    setError(null)

    const response = await analysisApi.technical(sym.toUpperCase(), mkt)

    setLoading(false)

    if (response.error) {
      setError(response.error)
      return
    }

    if (response.data) {
      setResult(response.data as AnalysisResult)
    }
  }, [])

  useEffect(() => {
    if (initialSymbol) {
      analyzeStock(initialSymbol, initialMarket)
    }
  }, [initialSymbol, initialMarket, analyzeStock])

  const handleAnalyze = () => {
    analyzeStock(symbol, market)
  }

  const getSignalColor = (signal: string) => {
    switch (signal) {
      case 'buy':
        return 'text-green-600 bg-green-100 dark:bg-green-900/30'
      case 'sell':
        return 'text-red-600 bg-red-100 dark:bg-red-900/30'
      default:
        return 'text-gray-600 bg-gray-100 dark:bg-gray-700'
    }
  }

  const getSignalIcon = (signal: string) => {
    switch (signal) {
      case 'buy':
        return <TrendingUp className="w-4 h-4" />
      case 'sell':
        return <TrendingDown className="w-4 h-4" />
      default:
        return <Minus className="w-4 h-4" />
    }
  }

  const getSignalLabel = (signal: string) => {
    switch (signal) {
      case 'buy':
        return '매수'
      case 'sell':
        return '매도'
      default:
        return '중립'
    }
  }

  const parseIndicators = (data: Record<string, unknown>): IndicatorSignal[] => {
    const latest = data.latest as Record<string, unknown> | undefined
    if (!latest) return []

    const indicators = latest.indicators as Record<string, number> | undefined
    const price = latest.price as Record<string, number> | undefined

    if (!indicators || !price) return []

    const currentPrice = price.close || 0
    const signals: IndicatorSignal[] = []

    // SMA 20
    if (indicators.sma_20 !== undefined) {
      const sma20 = indicators.sma_20
      signals.push({
        name: 'SMA 20',
        value: sma20?.toFixed(2) || null,
        signal: currentPrice > sma20 ? 'buy' : currentPrice < sma20 ? 'sell' : 'neutral',
        description: '20일 단순이동평균',
      })
    }

    // SMA 50
    if (indicators.sma_50 !== undefined) {
      const sma50 = indicators.sma_50
      signals.push({
        name: 'SMA 50',
        value: sma50?.toFixed(2) || null,
        signal: currentPrice > sma50 ? 'buy' : currentPrice < sma50 ? 'sell' : 'neutral',
        description: '50일 단순이동평균',
      })
    }

    // EMA 12
    if (indicators.ema_12 !== undefined) {
      const ema12 = indicators.ema_12
      signals.push({
        name: 'EMA 12',
        value: ema12?.toFixed(2) || null,
        signal: currentPrice > ema12 ? 'buy' : currentPrice < ema12 ? 'sell' : 'neutral',
        description: '12일 지수이동평균',
      })
    }

    // RSI 14
    if (indicators.rsi_14 !== undefined) {
      const rsi = indicators.rsi_14
      signals.push({
        name: 'RSI 14',
        value: rsi?.toFixed(2) || null,
        signal: rsi < 30 ? 'buy' : rsi > 70 ? 'sell' : 'neutral',
        description: rsi < 30 ? '과매도 구간' : rsi > 70 ? '과매수 구간' : '중립 구간',
      })
    }

    // MACD
    if (indicators.macd_histogram !== undefined) {
      const macdHist = indicators.macd_histogram
      signals.push({
        name: 'MACD',
        value: macdHist?.toFixed(4) || null,
        signal: macdHist > 0 ? 'buy' : macdHist < 0 ? 'sell' : 'neutral',
        description: 'MACD 히스토그램',
      })
    }

    return signals
  }

  const getLatestPrice = (data: Record<string, unknown>) => {
    const latest = data.latest as Record<string, unknown> | undefined
    if (!latest) return null

    const price = latest.price as Record<string, number> | undefined
    return price || null
  }

  const currency = market === 'KR' ? '₩' : '$'
  const latestPrice = result?.result ? getLatestPrice(result.result) : null
  const indicators = result?.result ? parseIndicators(result.result) : []

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-6">
          <Link
            href={initialSymbol ? `/stock/${initialSymbol}` : '/'}
            className="inline-flex items-center text-gray-600 hover:text-gray-800 dark:text-gray-400 dark:hover:text-gray-200 mb-4"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            {initialSymbol ? '종목 페이지로' : '홈으로'}
          </Link>

          <div className="flex items-center gap-3">
            <BarChart3 className="w-8 h-8 text-primary-600" />
            <div>
              <h1 className="text-2xl md:text-3xl font-bold text-gray-900 dark:text-white">
                기술적 분석
              </h1>
              <p className="text-gray-600 dark:text-gray-400">
                이동평균, RSI, MACD 등 기술적 지표 분석
              </p>
            </div>
          </div>
        </div>

        {/* Search Form */}
        <div className="card mb-6">
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
                onKeyDown={(e) => e.key === 'Enter' && handleAnalyze()}
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

            <div className="flex items-end">
              <button
                onClick={handleAnalyze}
                disabled={loading || !symbol.trim()}
                className="btn btn-primary w-full"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin mr-2" />
                    분석 중...
                  </>
                ) : (
                  <>
                    <Activity className="w-4 h-4 mr-2" />
                    분석 실행
                  </>
                )}
              </button>
            </div>
          </div>
        </div>

        {/* Error */}
        {error && (
          <div className="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg text-red-600 dark:text-red-400 mb-6">
            <p className="font-medium">분석 오류</p>
            <p className="text-sm">{error}</p>
            <button
              onClick={handleAnalyze}
              className="mt-2 text-sm underline hover:no-underline"
            >
              다시 시도
            </button>
          </div>
        )}

        {/* Loading */}
        {loading && (
          <div className="flex flex-col items-center justify-center py-12">
            <Loader2 className="w-12 h-12 animate-spin text-primary-600 mb-4" />
            <p className="text-gray-600 dark:text-gray-400">기술적 분석 중...</p>
            <p className="text-sm text-gray-500">AI가 기술 지표를 분석하고 있습니다</p>
          </div>
        )}

        {/* Results */}
        {result && !loading && (
          <div className="space-y-6">
            {/* Stock Info Header */}
            <div className="card">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-xl font-bold">{result.symbol}</h2>
                  <p className="text-gray-500">{result.market === 'KR' ? 'KRX' : 'NYSE/NASDAQ'}</p>
                </div>
                <button
                  onClick={handleAnalyze}
                  className="p-2 text-gray-500 hover:text-gray-700 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
                  title="새로고침"
                >
                  <RefreshCw className="w-5 h-5" />
                </button>
              </div>
            </div>

            {/* Latest Price */}
            {latestPrice && (
              <div className="card">
                <h3 className="text-lg font-semibold mb-4">현재가 정보</h3>
                <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                  <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                    <div className="text-xs text-gray-500 mb-1">시가</div>
                    <div className="text-lg font-semibold">
                      {currency}{latestPrice.open?.toLocaleString() || '-'}
                    </div>
                  </div>
                  <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                    <div className="text-xs text-gray-500 mb-1">고가</div>
                    <div className="text-lg font-semibold text-red-600">
                      {currency}{latestPrice.high?.toLocaleString() || '-'}
                    </div>
                  </div>
                  <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                    <div className="text-xs text-gray-500 mb-1">저가</div>
                    <div className="text-lg font-semibold text-blue-600">
                      {currency}{latestPrice.low?.toLocaleString() || '-'}
                    </div>
                  </div>
                  <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                    <div className="text-xs text-gray-500 mb-1">종가</div>
                    <div className="text-lg font-semibold">
                      {currency}{latestPrice.close?.toLocaleString() || '-'}
                    </div>
                  </div>
                  <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                    <div className="text-xs text-gray-500 mb-1">거래량</div>
                    <div className="text-lg font-semibold">
                      {latestPrice.volume?.toLocaleString() || '-'}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Technical Indicators */}
            {indicators.length > 0 && (
              <div className="card">
                <h3 className="text-lg font-semibold mb-4">기술 지표</h3>
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
                  {indicators.map((indicator, index) => (
                    <div
                      key={index}
                      className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg"
                    >
                      <div className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                        {indicator.name}
                      </div>
                      <div className="text-xl font-bold mb-2">
                        {indicator.value || '-'}
                      </div>
                      <div
                        className={`inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-medium ${getSignalColor(indicator.signal)}`}
                      >
                        {getSignalIcon(indicator.signal)}
                        {getSignalLabel(indicator.signal)}
                      </div>
                      <div className="text-xs text-gray-500 mt-2">
                        {indicator.description}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* AI Summary */}
            {result.summary && (
              <div className="card">
                <h3 className="text-lg font-semibold mb-4">AI 분석 요약</h3>
                <div className="prose prose-sm dark:prose-invert max-w-none">
                  <p className="whitespace-pre-line text-gray-700 dark:text-gray-300">
                    {result.summary}
                  </p>
                </div>
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex gap-4">
              <Link href={`/analysis/fundamental?symbol=${result.symbol}&market=${result.market}`}>
                <button className="btn btn-secondary">기본적 분석 보기</button>
              </Link>
              <Link href={`/research?symbol=${result.symbol}&market=${result.market}`}>
                <button className="btn btn-secondary">리서치 리포트 생성</button>
              </Link>
            </div>
          </div>
        )}

        {/* Empty State */}
        {!result && !loading && !error && !initialSymbol && (
          <div className="text-center py-12">
            <BarChart3 className="w-16 h-16 mx-auto text-gray-400 mb-4" />
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
              종목을 검색하세요
            </h3>
            <p className="text-gray-500">
              종목 코드를 입력하고 기술적 분석을 실행하세요
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
