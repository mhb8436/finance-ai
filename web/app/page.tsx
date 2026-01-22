'use client'

import { useState } from 'react'
import { Search, TrendingUp, BarChart3, FileText, MessageSquare, Star, Database } from 'lucide-react'
import Link from 'next/link'

export default function Home() {
  const [searchQuery, setSearchQuery] = useState('')

  const features = [
    {
      icon: Star,
      title: '고급 분석',
      description: '감성, 밸류에이션, 종합 추천 분석',
      href: '/analysis',
    },
    {
      icon: Database,
      title: 'Knowledge Base',
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

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    if (searchQuery.trim()) {
      window.location.href = `/stock/${searchQuery.toUpperCase()}`
    }
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
          <div className="card">
            <p className="text-sm text-gray-500">S&P 500</p>
            <p className="text-2xl font-bold">-</p>
            <p className="text-sm price-unchanged">-</p>
          </div>
          <div className="card">
            <p className="text-sm text-gray-500">NASDAQ</p>
            <p className="text-2xl font-bold">-</p>
            <p className="text-sm price-unchanged">-</p>
          </div>
          <div className="card">
            <p className="text-sm text-gray-500">KOSPI</p>
            <p className="text-2xl font-bold">-</p>
            <p className="text-sm price-unchanged">-</p>
          </div>
          <div className="card">
            <p className="text-sm text-gray-500">KOSDAQ</p>
            <p className="text-2xl font-bold">-</p>
            <p className="text-sm price-unchanged">-</p>
          </div>
        </div>
      </div>
    </div>
  )
}
