'use client'

import { useState, useEffect, useCallback } from 'react'
import { useParams } from 'next/navigation'
import { ArrowLeft, TrendingUp, TrendingDown, RefreshCw } from 'lucide-react'
import Link from 'next/link'
import dynamic from 'next/dynamic'

// Dynamic import to avoid SSR issues with lightweight-charts
const StockChart = dynamic(() => import('@/components/StockChart'), {
  ssr: false,
  loading: () => (
    <div className="h-[400px] bg-gray-100 dark:bg-gray-700 rounded-lg flex items-center justify-center">
      <div className="animate-pulse text-gray-500">차트 로딩 중...</div>
    </div>
  ),
})

interface StockInfo {
  symbol: string
  name: string
  market: string
  sector: string | null
  industry: string | null
  market_cap: number | null
  pe_ratio: number | null
  pb_ratio: number | null
  dividend_yield: number | null
}

interface PriceData {
  date: string
  open: number
  high: number
  low: number
  close: number
  volume: number
}

export default function StockPage() {
  const params = useParams()
  const symbol = params.symbol as string

  const [stockInfo, setStockInfo] = useState<StockInfo | null>(null)
  const [priceData, setPriceData] = useState<PriceData[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [market, setMarket] = useState('US')
  const [period, setPeriod] = useState('1y')
  const [refreshing, setRefreshing] = useState(false)

  const fetchData = useCallback(async (sym: string, mkt: string, prd: string = '1y') => {
    setLoading(true)
    setError(null)

    try {
      const [infoRes, priceRes] = await Promise.all([
        fetch(`/api/v1/stock/info/${sym}?market=${mkt}`),
        fetch(`/api/v1/stock/price/${sym}?market=${mkt}&period=${prd}`),
      ])

      if (!infoRes.ok || !priceRes.ok) {
        throw new Error('Failed to fetch data')
      }

      const infoData = await infoRes.json()
      const priceDataRes = await priceRes.json()

      setStockInfo(infoData)
      setPriceData(priceDataRes.data || [])
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    // Detect market from symbol
    const detectedMarket = /^\d{6}$/.test(symbol) ? 'KR' : 'US'
    setMarket(detectedMarket)

    fetchData(symbol, detectedMarket, period)
  }, [symbol, fetchData, period])

  const handleRefresh = async () => {
    setRefreshing(true)
    await fetchData(symbol, market, period)
    setRefreshing(false)
  }

  const formatNumber = (num: number | null) => {
    if (num === null) return '-'
    if (num >= 1e12) return `${(num / 1e12).toFixed(2)}T`
    if (num >= 1e9) return `${(num / 1e9).toFixed(2)}B`
    if (num >= 1e6) return `${(num / 1e6).toFixed(2)}M`
    return num.toLocaleString()
  }

  const latestPrice = priceData.length > 0 ? priceData[priceData.length - 1] : null
  const previousPrice = priceData.length > 1 ? priceData[priceData.length - 2] : null
  const priceChange = latestPrice && previousPrice
    ? ((latestPrice.close - previousPrice.close) / previousPrice.close) * 100
    : 0

  return (
    <div className="min-h-screen p-8">
      {/* Back button */}
      <Link href="/" className="inline-flex items-center text-gray-600 hover:text-gray-800 mb-6">
        <ArrowLeft className="w-4 h-4 mr-2" />
        홈으로
      </Link>

      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="spinner" />
        </div>
      ) : error ? (
        <div className="text-center text-red-500 py-12">
          <p>데이터를 불러오는데 실패했습니다</p>
          <p className="text-sm">{error}</p>
        </div>
      ) : (
        <>
          {/* Stock Header */}
          <div className="card mb-6">
            <div className="flex items-start justify-between">
              <div>
                <h1 className="text-3xl font-bold">{stockInfo?.name || symbol}</h1>
                <p className="text-gray-500">{symbol} · {market === 'KR' ? 'KRX' : 'NYSE/NASDAQ'}</p>
              </div>
              <div className="text-right">
                <p className="text-3xl font-bold">
                  {market === 'KR' ? '₩' : '$'}
                  {latestPrice?.close.toLocaleString() || '-'}
                </p>
                <p className={`text-lg ${priceChange >= 0 ? 'price-up' : 'price-down'}`}>
                  {priceChange >= 0 ? <TrendingUp className="inline w-4 h-4 mr-1" /> : <TrendingDown className="inline w-4 h-4 mr-1" />}
                  {priceChange >= 0 ? '+' : ''}{priceChange.toFixed(2)}%
                </p>
              </div>
            </div>
          </div>

          {/* Key Metrics */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <div className="card">
              <p className="text-sm text-gray-500">시가총액</p>
              <p className="text-xl font-semibold">{formatNumber(stockInfo?.market_cap || null)}</p>
            </div>
            <div className="card">
              <p className="text-sm text-gray-500">P/E Ratio</p>
              <p className="text-xl font-semibold">{stockInfo?.pe_ratio?.toFixed(2) || '-'}</p>
            </div>
            <div className="card">
              <p className="text-sm text-gray-500">P/B Ratio</p>
              <p className="text-xl font-semibold">{stockInfo?.pb_ratio?.toFixed(2) || '-'}</p>
            </div>
            <div className="card">
              <p className="text-sm text-gray-500">배당수익률</p>
              <p className="text-xl font-semibold">
                {stockInfo?.dividend_yield ? `${(stockInfo.dividend_yield * 100).toFixed(2)}%` : '-'}
              </p>
            </div>
          </div>

          {/* Price Chart */}
          <div className="card mb-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="card-header !mb-0">가격 차트</h2>
              <button
                onClick={handleRefresh}
                disabled={refreshing}
                className="p-2 text-gray-500 hover:text-gray-700 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                title="새로고침"
              >
                <RefreshCw className={`w-5 h-5 ${refreshing ? 'animate-spin' : ''}`} />
              </button>
            </div>
            <StockChart
              data={priceData}
              symbol={symbol}
              currency={market === 'KR' ? '₩' : '$'}
              height={400}
              showVolume={true}
            />
          </div>

          {/* Company Info */}
          {stockInfo && (
            <div className="card">
              <div className="card-header">기업 정보</div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-gray-500">섹터</p>
                  <p>{stockInfo.sector || '-'}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">산업</p>
                  <p>{stockInfo.industry || '-'}</p>
                </div>
              </div>
            </div>
          )}

          {/* Analysis Links */}
          <div className="mt-6 flex gap-4">
            <Link href={`/analysis/technical?symbol=${symbol}&market=${market}`}>
              <button className="btn btn-primary">기술적 분석</button>
            </Link>
            <Link href={`/analysis/fundamental?symbol=${symbol}&market=${market}`}>
              <button className="btn btn-secondary">기본적 분석</button>
            </Link>
            <Link href={`/research?symbol=${symbol}&market=${market}`}>
              <button className="btn btn-secondary">리서치 리포트</button>
            </Link>
          </div>
        </>
      )}
    </div>
  )
}
