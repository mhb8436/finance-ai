'use client'

import { useState } from 'react'
import {
  BarChart3,
  Newspaper,
  DollarSign,
  Star,
  ChevronDown,
  ChevronUp,
} from 'lucide-react'
import SentimentAnalysis from '@/components/SentimentAnalysis'
import ValuationAnalysis from '@/components/ValuationAnalysis'
import StockRecommendation from '@/components/StockRecommendation'

type AnalysisTab = 'recommendation' | 'valuation' | 'sentiment'

interface TabConfig {
  id: AnalysisTab
  label: string
  description: string
  icon: React.ReactNode
}

const TABS: TabConfig[] = [
  {
    id: 'recommendation',
    label: '종목 추천',
    description: '기술적, 기본적, 감성, 밸류에이션 분석을 종합한 투자 추천',
    icon: <Star className="w-5 h-5" />,
  },
  {
    id: 'valuation',
    label: '밸류에이션',
    description: 'DCF, PER, PBR 등 다양한 방법론을 활용한 적정가 분석',
    icon: <DollarSign className="w-5 h-5" />,
  },
  {
    id: 'sentiment',
    label: '감성 분석',
    description: '뉴스 및 유튜브 컨텐츠 기반 시장 심리 분석',
    icon: <Newspaper className="w-5 h-5" />,
  },
]

export default function AnalysisPage() {
  const [activeTab, setActiveTab] = useState<AnalysisTab>('recommendation')
  const [expandedMobile, setExpandedMobile] = useState(false)

  const activeConfig = TABS.find((t) => t.id === activeTab)!

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <BarChart3 className="w-8 h-8 text-primary-600" />
            <h1 className="text-2xl md:text-3xl font-bold text-gray-900 dark:text-white">
              고급 분석
            </h1>
          </div>
          <p className="text-gray-600 dark:text-gray-400">
            AI 기반 종목 분석 도구를 활용하여 투자 의사결정을 지원합니다
          </p>
        </div>

        {/* Desktop Tabs */}
        <div className="hidden md:flex gap-4 mb-6">
          {TABS.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex-1 p-4 rounded-lg border-2 transition-all ${
                activeTab === tab.id
                  ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20'
                  : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
              }`}
            >
              <div className="flex items-center gap-3">
                <div
                  className={`${
                    activeTab === tab.id
                      ? 'text-primary-600'
                      : 'text-gray-400'
                  }`}
                >
                  {tab.icon}
                </div>
                <div className="text-left">
                  <div
                    className={`font-semibold ${
                      activeTab === tab.id
                        ? 'text-primary-700 dark:text-primary-300'
                        : 'text-gray-700 dark:text-gray-300'
                    }`}
                  >
                    {tab.label}
                  </div>
                  <div className="text-xs text-gray-500 dark:text-gray-400">
                    {tab.description}
                  </div>
                </div>
              </div>
            </button>
          ))}
        </div>

        {/* Mobile Tabs */}
        <div className="md:hidden mb-6">
          <button
            onClick={() => setExpandedMobile(!expandedMobile)}
            className="w-full p-4 rounded-lg border-2 border-primary-500 bg-primary-50 dark:bg-primary-900/20 flex items-center justify-between"
          >
            <div className="flex items-center gap-3">
              <div className="text-primary-600">{activeConfig.icon}</div>
              <div className="text-left">
                <div className="font-semibold text-primary-700 dark:text-primary-300">
                  {activeConfig.label}
                </div>
                <div className="text-xs text-gray-500 dark:text-gray-400">
                  {activeConfig.description}
                </div>
              </div>
            </div>
            {expandedMobile ? (
              <ChevronUp className="w-5 h-5 text-gray-400" />
            ) : (
              <ChevronDown className="w-5 h-5 text-gray-400" />
            )}
          </button>

          {expandedMobile && (
            <div className="mt-2 space-y-2">
              {TABS.filter((t) => t.id !== activeTab).map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => {
                    setActiveTab(tab.id)
                    setExpandedMobile(false)
                  }}
                  className="w-full p-4 rounded-lg border border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600 flex items-center gap-3"
                >
                  <div className="text-gray-400">{tab.icon}</div>
                  <div className="text-left">
                    <div className="font-semibold text-gray-700 dark:text-gray-300">
                      {tab.label}
                    </div>
                    <div className="text-xs text-gray-500 dark:text-gray-400">
                      {tab.description}
                    </div>
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Content */}
        <div>
          {activeTab === 'recommendation' && <StockRecommendation />}
          {activeTab === 'valuation' && <ValuationAnalysis />}
          {activeTab === 'sentiment' && <SentimentAnalysis />}
        </div>

        {/* Help Section */}
        <div className="mt-8 p-6 bg-white dark:bg-gray-800 rounded-lg shadow-sm">
          <h2 className="text-lg font-semibold mb-4">분석 도구 안내</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <div className="flex items-center gap-2 mb-2">
                <Star className="w-4 h-4 text-primary-600" />
                <h3 className="font-medium">종목 추천</h3>
              </div>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                기술적 분석, 기본적 분석, 감성 분석, 밸류에이션을 종합하여
                투자 스타일에 맞는 종목 추천을 제공합니다.
              </p>
            </div>
            <div>
              <div className="flex items-center gap-2 mb-2">
                <DollarSign className="w-4 h-4 text-primary-600" />
                <h3 className="font-medium">밸류에이션</h3>
              </div>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                DCF, PER, PBR, 52주 가격범위 등 다양한 방법론을 활용하여
                주식의 적정 가치를 산출합니다.
              </p>
            </div>
            <div>
              <div className="flex items-center gap-2 mb-2">
                <Newspaper className="w-4 h-4 text-primary-600" />
                <h3 className="font-medium">감성 분석</h3>
              </div>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                뉴스 기사와 유튜브 영상의 내용을 분석하여
                시장의 심리와 주요 이슈를 파악합니다.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
