'use client'

import { useState, useEffect, useCallback } from 'react'
import { useSearchParams } from 'next/navigation'
import Link from 'next/link'
import {
  ArrowLeft,
  RefreshCw,
  Loader2,
  Building2,
  TrendingUp,
  TrendingDown,
  Minus,
  DollarSign,
  PieChart,
  FileText,
} from 'lucide-react'
import { analysisApi } from '@/lib/api'
import type { AnalysisResult } from '@/types'

export default function FundamentalAnalysisPage() {
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

    const response = await analysisApi.fundamental(sym.toUpperCase(), mkt)

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

  const formatNumber = (value: number | null | undefined, currency?: string): string => {
    if (value === null || value === undefined) return '-'

    const prefix = currency || ''

    if (Math.abs(value) >= 1_000_000_000_000) {
      return `${prefix}${(value / 1_000_000_000_000).toFixed(2)}T`
    }
    if (Math.abs(value) >= 1_000_000_000) {
      return `${prefix}${(value / 1_000_000_000).toFixed(2)}B`
    }
    if (Math.abs(value) >= 1_000_000) {
      return `${prefix}${(value / 1_000_000).toFixed(2)}M`
    }
    return `${prefix}${value.toLocaleString()}`
  }

  const formatPercent = (value: number | null | undefined): string => {
    if (value === null || value === undefined) return '-'
    return `${(value * 100).toFixed(2)}%`
  }

  const formatRatio = (value: number | null | undefined): string => {
    if (value === null || value === undefined) return '-'
    return value.toFixed(2)
  }

  const getCompanyInfo = (data: Record<string, unknown>) => {
    const info = data.info as Record<string, unknown> | undefined
    return info || {}
  }

  const getFinancials = (data: Record<string, unknown>) => {
    const financials = data.financials as Record<string, unknown> | undefined
    return financials || {}
  }

  const getRatios = (data: Record<string, unknown>) => {
    const ratios = data.ratios as Record<string, number> | undefined
    return ratios || {}
  }

  const currency = market === 'KR' ? '₩' : '$'
  const companyInfo = result?.result ? getCompanyInfo(result.result) : {}
  const financials = result?.result ? getFinancials(result.result) : {}
  const ratios = result?.result ? getRatios(result.result) : {}

  const incomeStatement = financials.income_statement as Record<string, number> | undefined
  const balanceSheet = financials.balance_sheet as Record<string, number> | undefined

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
            <Building2 className="w-8 h-8 text-primary-600" />
            <div>
              <h1 className="text-2xl md:text-3xl font-bold text-gray-900 dark:text-white">
                기본적 분석
              </h1>
              <p className="text-gray-600 dark:text-gray-400">
                재무제표, 밸류에이션, 성장성 분석
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
                    <FileText className="w-4 h-4 mr-2" />
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
            <p className="text-gray-600 dark:text-gray-400">기본적 분석 중...</p>
            <p className="text-sm text-gray-500">AI가 재무 데이터를 분석하고 있습니다</p>
          </div>
        )}

        {/* Results */}
        {result && !loading && (
          <div className="space-y-6">
            {/* Company Info Header */}
            <div className="card">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-xl font-bold">
                    {(companyInfo.name as string) || result.symbol}
                  </h2>
                  <p className="text-gray-500">
                    {result.symbol} · {result.market === 'KR' ? 'KRX' : 'NYSE/NASDAQ'}
                  </p>
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

            {/* Company Overview */}
            <div className="card">
              <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <Building2 className="w-5 h-5 text-primary-600" />
                기업 개요
              </h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                  <div className="text-xs text-gray-500 mb-1">섹터</div>
                  <div className="font-semibold">
                    {(companyInfo.sector as string) || '-'}
                  </div>
                </div>
                <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                  <div className="text-xs text-gray-500 mb-1">산업</div>
                  <div className="font-semibold">
                    {(companyInfo.industry as string) || '-'}
                  </div>
                </div>
                <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                  <div className="text-xs text-gray-500 mb-1">시가총액</div>
                  <div className="font-semibold">
                    {formatNumber(companyInfo.market_cap as number, currency)}
                  </div>
                </div>
                <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                  <div className="text-xs text-gray-500 mb-1">배당수익률</div>
                  <div className="font-semibold">
                    {formatPercent(companyInfo.dividend_yield as number)}
                  </div>
                </div>
              </div>
            </div>

            {/* Valuation Metrics */}
            <div className="card">
              <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <DollarSign className="w-5 h-5 text-primary-600" />
                밸류에이션 지표
              </h3>
              <div className="grid grid-cols-3 md:grid-cols-3 gap-4">
                <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg text-center">
                  <div className="text-xs text-gray-500 mb-1">P/E Ratio</div>
                  <div className="text-2xl font-bold text-primary-600">
                    {formatRatio(companyInfo.pe_ratio as number)}
                  </div>
                  <div className="text-xs text-gray-500 mt-1">주가수익비율</div>
                </div>
                <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg text-center">
                  <div className="text-xs text-gray-500 mb-1">P/B Ratio</div>
                  <div className="text-2xl font-bold text-primary-600">
                    {formatRatio(companyInfo.pb_ratio as number)}
                  </div>
                  <div className="text-xs text-gray-500 mt-1">주가순자산비율</div>
                </div>
                <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg text-center">
                  <div className="text-xs text-gray-500 mb-1">배당률</div>
                  <div className="text-2xl font-bold text-primary-600">
                    {formatPercent(companyInfo.dividend_yield as number)}
                  </div>
                  <div className="text-xs text-gray-500 mt-1">배당수익률</div>
                </div>
              </div>
            </div>

            {/* Financial Statements */}
            {(incomeStatement || balanceSheet) && (
              <div className="card">
                <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                  <PieChart className="w-5 h-5 text-primary-600" />
                  재무 현황
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {/* Income Statement */}
                  {incomeStatement && (
                    <div>
                      <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                        손익계산서
                      </h4>
                      <div className="space-y-2">
                        <div className="flex justify-between p-2 bg-gray-50 dark:bg-gray-800 rounded">
                          <span className="text-sm text-gray-600 dark:text-gray-400">매출</span>
                          <span className="font-medium">
                            {formatNumber(incomeStatement.revenue, currency)}
                          </span>
                        </div>
                        <div className="flex justify-between p-2 bg-gray-50 dark:bg-gray-800 rounded">
                          <span className="text-sm text-gray-600 dark:text-gray-400">순이익</span>
                          <span className="font-medium">
                            {formatNumber(incomeStatement.net_income, currency)}
                          </span>
                        </div>
                        <div className="flex justify-between p-2 bg-gray-50 dark:bg-gray-800 rounded">
                          <span className="text-sm text-gray-600 dark:text-gray-400">매출총이익률</span>
                          <span className="font-medium">
                            {formatPercent(incomeStatement.gross_margin)}
                          </span>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Balance Sheet */}
                  {balanceSheet && (
                    <div>
                      <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                        재무상태표
                      </h4>
                      <div className="space-y-2">
                        <div className="flex justify-between p-2 bg-gray-50 dark:bg-gray-800 rounded">
                          <span className="text-sm text-gray-600 dark:text-gray-400">총자산</span>
                          <span className="font-medium">
                            {formatNumber(balanceSheet.total_assets, currency)}
                          </span>
                        </div>
                        <div className="flex justify-between p-2 bg-gray-50 dark:bg-gray-800 rounded">
                          <span className="text-sm text-gray-600 dark:text-gray-400">총부채</span>
                          <span className="font-medium">
                            {formatNumber(balanceSheet.total_debt, currency)}
                          </span>
                        </div>
                        <div className="flex justify-between p-2 bg-gray-50 dark:bg-gray-800 rounded">
                          <span className="text-sm text-gray-600 dark:text-gray-400">현금</span>
                          <span className="font-medium">
                            {formatNumber(balanceSheet.cash, currency)}
                          </span>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Financial Ratios */}
            {Object.keys(ratios).length > 0 && (
              <div className="card">
                <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                  <TrendingUp className="w-5 h-5 text-primary-600" />
                  재무 비율
                </h3>
                <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                  {ratios.roe !== undefined && (
                    <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg text-center">
                      <div className="text-xs text-gray-500 mb-1">ROE</div>
                      <div className="text-lg font-bold">{formatPercent(ratios.roe)}</div>
                      <div className="text-xs text-gray-500">자기자본이익률</div>
                    </div>
                  )}
                  {ratios.roa !== undefined && (
                    <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg text-center">
                      <div className="text-xs text-gray-500 mb-1">ROA</div>
                      <div className="text-lg font-bold">{formatPercent(ratios.roa)}</div>
                      <div className="text-xs text-gray-500">총자산이익률</div>
                    </div>
                  )}
                  {ratios.current_ratio !== undefined && (
                    <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg text-center">
                      <div className="text-xs text-gray-500 mb-1">유동비율</div>
                      <div className="text-lg font-bold">{formatRatio(ratios.current_ratio)}</div>
                      <div className="text-xs text-gray-500">Current Ratio</div>
                    </div>
                  )}
                  {ratios.debt_to_equity !== undefined && (
                    <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg text-center">
                      <div className="text-xs text-gray-500 mb-1">부채비율</div>
                      <div className="text-lg font-bold">{formatRatio(ratios.debt_to_equity)}</div>
                      <div className="text-xs text-gray-500">D/E Ratio</div>
                    </div>
                  )}
                  {ratios.profit_margin !== undefined && (
                    <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg text-center">
                      <div className="text-xs text-gray-500 mb-1">이익률</div>
                      <div className="text-lg font-bold">{formatPercent(ratios.profit_margin)}</div>
                      <div className="text-xs text-gray-500">Profit Margin</div>
                    </div>
                  )}
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
              <Link href={`/analysis/technical?symbol=${result.symbol}&market=${result.market}`}>
                <button className="btn btn-secondary">기술적 분석 보기</button>
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
            <Building2 className="w-16 h-16 mx-auto text-gray-400 mb-4" />
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
              종목을 검색하세요
            </h3>
            <p className="text-gray-500">
              종목 코드를 입력하고 기본적 분석을 실행하세요
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
