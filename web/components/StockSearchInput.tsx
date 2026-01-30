'use client'

import { useState, useEffect, useRef, useCallback } from 'react'
import { Search, Loader2, X } from 'lucide-react'
import { stockApi } from '@/lib/api'

interface StockSearchResult {
  symbol: string
  name: string
  market: string
  exchange: string
}

interface StockSearchInputProps {
  value: string
  onChange: (symbol: string, name?: string) => void
  market: 'US' | 'KR'
  placeholder?: string
  label?: string
  className?: string
  onMarketChange?: (market: 'US' | 'KR') => void
  showMarketSelect?: boolean
}

export default function StockSearchInput({
  value,
  onChange,
  market,
  placeholder = '종목 코드 또는 이름 검색',
  label = '종목 검색',
  className = '',
  onMarketChange,
  showMarketSelect = true,
}: StockSearchInputProps) {
  const [query, setQuery] = useState(value)
  const [results, setResults] = useState<StockSearchResult[]>([])
  const [loading, setLoading] = useState(false)
  const [showDropdown, setShowDropdown] = useState(false)
  const [selectedName, setSelectedName] = useState<string>('')
  const wrapperRef = useRef<HTMLDivElement>(null)
  const debounceRef = useRef<NodeJS.Timeout | null>(null)

  // Sync external value changes
  useEffect(() => {
    if (value !== query) {
      setQuery(value)
    }
  }, [value])

  // Close dropdown on outside click
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target as Node)) {
        setShowDropdown(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const searchStocks = useCallback(async (searchQuery: string) => {
    if (!searchQuery.trim() || searchQuery.length < 2) {
      setResults([])
      setShowDropdown(false)
      return
    }

    // Skip search if it's already a valid code format
    const isUSSymbol = /^[A-Za-z]{1,5}$/.test(searchQuery)
    const isKRCode = /^\d{6}$/.test(searchQuery)
    if (isUSSymbol || isKRCode) {
      setResults([])
      return
    }

    setLoading(true)
    try {
      const data = await stockApi.searchStocks(searchQuery, market, 8)
      setResults(data || [])
      setShowDropdown(data && data.length > 0)
    } catch (error) {
      console.error('Search error:', error)
      setResults([])
    } finally {
      setLoading(false)
    }
  }, [market])

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value
    setQuery(newValue)
    setSelectedName('')
    onChange(newValue)

    // Debounce search
    if (debounceRef.current) {
      clearTimeout(debounceRef.current)
    }
    debounceRef.current = setTimeout(() => {
      searchStocks(newValue)
    }, 300)
  }

  const handleSelect = (stock: StockSearchResult) => {
    setQuery(stock.symbol)
    setSelectedName(stock.name)
    onChange(stock.symbol, stock.name)
    setShowDropdown(false)
    setResults([])
  }

  const handleClear = () => {
    setQuery('')
    setSelectedName('')
    onChange('')
    setResults([])
    setShowDropdown(false)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      setShowDropdown(false)
    }
  }

  return (
    <div ref={wrapperRef} className={`relative ${className}`}>
      <div className="flex gap-2">
        <div className="flex-1 relative">
          {label && (
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              {label}
            </label>
          )}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              value={query}
              onChange={handleInputChange}
              onFocus={() => results.length > 0 && setShowDropdown(true)}
              onKeyDown={handleKeyDown}
              placeholder={placeholder}
              className="input w-full pl-10 pr-10"
            />
            {loading && (
              <Loader2 className="absolute right-8 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400 animate-spin" />
            )}
            {query && (
              <button
                type="button"
                onClick={handleClear}
                className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
              >
                <X className="w-4 h-4" />
              </button>
            )}
          </div>
          {selectedName && (
            <p className="text-xs text-gray-500 mt-1">{selectedName}</p>
          )}
        </div>

        {showMarketSelect && onMarketChange && (
          <div>
            {label && (
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                시장
              </label>
            )}
            <select
              value={market}
              onChange={(e) => {
                onMarketChange(e.target.value as 'US' | 'KR')
                setResults([])
              }}
              className="input w-28"
            >
              <option value="US">미국</option>
              <option value="KR">한국</option>
            </select>
          </div>
        )}
      </div>

      {/* Dropdown Results */}
      {showDropdown && results.length > 0 && (
        <div className="absolute z-50 w-full mt-1 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg max-h-60 overflow-y-auto">
          {results.map((stock, index) => (
            <button
              key={`${stock.symbol}-${index}`}
              type="button"
              onClick={() => handleSelect(stock)}
              className="w-full px-4 py-3 text-left hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center justify-between border-b border-gray-100 dark:border-gray-700 last:border-b-0"
            >
              <div>
                <div className="font-medium text-gray-900 dark:text-white">
                  {stock.name}
                </div>
                <div className="text-sm text-gray-500">
                  {stock.symbol}
                </div>
              </div>
              <span className="text-xs text-gray-400 bg-gray-100 dark:bg-gray-700 px-2 py-1 rounded">
                {stock.exchange || stock.market}
              </span>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
