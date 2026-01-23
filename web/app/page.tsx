'use client'

import { useState, useEffect } from 'react'
import { Search, TrendingUp, BarChart3, FileText, MessageSquare, Star, Database, Loader2 } from 'lucide-react'
import Link from 'next/link'
import { stockApi } from '@/lib/api'

interface MarketIndex {
  name: string
  symbol: string
  market: string
  price: number | null
  change: number | null
  changePercent: number | null
  loading: boolean
}

export default function Home() {
  const [searchQuery, setSearchQuery] = useState('')
  const [marketIndices, setMarketIndices] = useState<MarketIndex[]>([
    { name: 'S&P 500', symbol: '^GSPC', market: 'US', price: null, change: null, changePercent: null, loading: true },
    { name: 'NASDAQ', symbol: '^IXIC', market: 'US', price: null, change: null, changePercent: null, loading: true },
    { name: 'KOSPI', symbol: '^KS11', market: 'US', price: null, change: null, changePercent: null, loading: true },
    { name: 'KOSDAQ', symbol: '^KQ11', market: 'US', price: null, change: null, changePercent: null, loading: true },
  ])

  useEffect(() => {
    const fetchMarketData = async () => {
      const updatedIndices = await Promise.all(
        marketIndices.map(async (index) => {
          const quote = await stockApi.getIndexQuote(index.symbol, index.market)
          return {
            ...index,
            price: quote?.price ?? null,
            change: quote?.change ?? null,
            changePercent: quote?.changePercent ?? null,
            loading: false,
          }
        })
      )
      setMarketIndices(updatedIndices)
    }
    fetchMarketData()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const features = [
    {
      icon: Star,
      title: '고급 분석',
      description: '감성, 밸류에이션, 종합 추천 분석',
      href: '/analysis',
    },
    {
      icon: Database,
      title: '지식 베이스',
      description: '문서 업로드 및 RAG 기반 Q&A',
      href: '/knowledge',
    },
    {
      icon: TrendingUp,
      title: '기술적 분석',
      description: '이동평균, RSI, MACD 등 기술적 지표 분석',
      href: '/analysis/technical',
    },
    {
      icon: BarChart3,
      title: '기본적 분석',
      description: '재무제표, 밸류에이션, 성장성 분석',
      href: '/analysis/fundamental',
    },
    {
      icon: FileText,
      title: '리서치 리포트',
      description: 'AI 기반 종목/산업 리서치 리포트 생성',
      href: '/research',
    },
    {
      icon: MessageSquare,
      title: 'AI 질의응답',
      description: '자연어로 주식 정보 질문하기',
      href: '/chat',
    },
  ]

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault()
    const query = searchQuery.trim()
    if (!query) return

    // Check if it's already a valid symbol format
    const isUSSymbol = /^[A-Za-z]{1,5}$/.test(query)
    const isKRCode = /^\d{6}$/.test(query)

    if (isUSSymbol || isKRCode) {
      // Direct navigation for valid symbols
      window.location.href = `/stock/${query.toUpperCase()}`
      return
    }

    // For Korean company names, search for the stock code
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8001'}/api/v1/stock/search?query=${encodeURIComponent(query)}&market=KR&limit=1`
      )
      if (response.ok) {
        const results = await response.json()
        if (results.length > 0) {
          // Navigate using the found stock code
          window.location.href = `/stock/${results[0].symbol}`
          return
        }
      }
    } catch (error) {
      console.error('Search error:', error)
    }

    // Fallback: navigate with original query
    window.location.href = `/stock/${query.toUpperCase()}`
  }

  return (
    <div className="min-h-screen p-8">
      {/* Header */}
      <div className="text-center mb-12">
        <h1 className="text-4xl font-bold mb-4">
          <span className="text-primary-600">Finance</span>AI
        </h1>
        <p className="text-xl text-gray-600 dark:text-gray-400">
          AI 기반 주식 분석 플랫폼
        </p>
      </div>

      {/* Search */}
      <form onSubmit={handleSearch} className="max-w-2xl mx-auto mb-12">
        <div className="relative">
          <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="종목 코드 또는 이름 검색 (예: AAPL, 삼성전자)"
            className="input pl-12 py-4 text-lg"
          />
          <button
            type="submit"
            className="absolute right-2 top-1/2 transform -translate-y-1/2 btn btn-primary"
          >
            검색
          </button>
        </div>
      </form>

      {/* Features */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-6xl mx-auto">
        {features.map((feature) => (
          <Link key={feature.title} href={feature.href}>
            <div className="card hover:shadow-lg transition-shadow cursor-pointer h-full">
              <feature.icon className="w-12 h-12 text-primary-600 mb-4" />
              <h3 className="text-lg font-semibold mb-2">{feature.title}</h3>
              <p className="text-gray-600 dark:text-gray-400 text-sm">
                {feature.description}
              </p>
            </div>
          </Link>
        ))}
      </div>

      {/* Quick Stats */}
      <div className="mt-12 max-w-6xl mx-auto">
        <h2 className="text-2xl font-semibold mb-6">시장 현황</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {marketIndices.map((index) => (
            <div key={index.symbol} className="card">
              <p className="text-sm text-gray-500">{index.name}</p>
              {index.loading ? (
                <div className="flex items-center gap-2 mt-2">
                  <Loader2 className="w-4 h-4 animate-spin text-gray-400" />
                  <span className="text-gray-400">로딩 중...</span>
                </div>
              ) : index.price !== null ? (
                <>
                  <p className="text-2xl font-bold">{index.price.toLocaleString(undefined, { maximumFractionDigits: 2 })}</p>
                  <p className={`text-sm ${
                    index.change !== null
                      ? index.change > 0
                        ? 'text-red-500'
                        : index.change < 0
                        ? 'text-blue-500'
                        : 'text-gray-500'
                      : 'text-gray-500'
                  }`}>
                    {index.change !== null && index.changePercent !== null
                      ? `${index.change > 0 ? '+' : ''}${index.change.toFixed(2)} (${index.changePercent > 0 ? '+' : ''}${index.changePercent.toFixed(2)}%)`
                      : '-'}
                  </p>
                </>
              ) : (
                <>
                  <p className="text-2xl font-bold text-gray-400">-</p>
                  <p className="text-sm text-gray-400">데이터 없음</p>
                </>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
