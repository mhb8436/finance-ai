'use client'

import { useEffect, useRef, useState } from 'react'
import {
  createChart,
  IChartApi,
  ISeriesApi,
  CandlestickData,
  LineData,
  Time,
  ColorType,
  CrosshairMode,
} from 'lightweight-charts'

interface PriceData {
  date: string
  open: number
  high: number
  low: number
  close: number
  volume: number
}

type ChartType = 'candlestick' | 'line' | 'area'
type TimeRange = '1W' | '1M' | '3M' | '6M' | '1Y' | 'ALL'

interface StockChartProps {
  data: PriceData[]
  symbol: string
  currency?: string
  height?: number
  showVolume?: boolean
  defaultChartType?: ChartType
  onTimeRangeChange?: (range: TimeRange) => void
}

export default function StockChart({
  data,
  symbol,
  currency = '$',
  height = 400,
  showVolume = true,
  defaultChartType = 'candlestick',
  onTimeRangeChange,
}: StockChartProps) {
  const chartContainerRef = useRef<HTMLDivElement>(null)
  const chartRef = useRef<IChartApi | null>(null)
  const priceSeriesRef = useRef<ISeriesApi<'Candlestick' | 'Line' | 'Area'> | null>(null)
  const volumeSeriesRef = useRef<ISeriesApi<'Histogram'> | null>(null)

  const [chartType, setChartType] = useState<ChartType>(defaultChartType)
  const [timeRange, setTimeRange] = useState<TimeRange>('3M')
  const [crosshairData, setCrosshairData] = useState<{
    time: string
    open: number
    high: number
    low: number
    close: number
    volume: number
  } | null>(null)

  // Filter data based on time range
  const getFilteredData = (range: TimeRange) => {
    if (!data.length) return []

    const now = new Date()
    let startDate: Date

    switch (range) {
      case '1W':
        startDate = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000)
        break
      case '1M':
        startDate = new Date(now.getFullYear(), now.getMonth() - 1, now.getDate())
        break
      case '3M':
        startDate = new Date(now.getFullYear(), now.getMonth() - 3, now.getDate())
        break
      case '6M':
        startDate = new Date(now.getFullYear(), now.getMonth() - 6, now.getDate())
        break
      case '1Y':
        startDate = new Date(now.getFullYear() - 1, now.getMonth(), now.getDate())
        break
      case 'ALL':
      default:
        return data
    }

    return data.filter(d => new Date(d.date) >= startDate)
  }

  // Initialize chart
  useEffect(() => {
    if (!chartContainerRef.current) return

    const chart = createChart(chartContainerRef.current, {
      width: chartContainerRef.current.clientWidth,
      height: height,
      layout: {
        background: { type: ColorType.Solid, color: 'transparent' },
        textColor: '#6b7280',
      },
      grid: {
        vertLines: { color: 'rgba(107, 114, 128, 0.1)' },
        horzLines: { color: 'rgba(107, 114, 128, 0.1)' },
      },
      crosshair: {
        mode: CrosshairMode.Normal,
        vertLine: {
          width: 1,
          color: 'rgba(107, 114, 128, 0.5)',
          style: 0,
        },
        horzLine: {
          width: 1,
          color: 'rgba(107, 114, 128, 0.5)',
          style: 0,
        },
      },
      rightPriceScale: {
        borderColor: 'rgba(107, 114, 128, 0.2)',
      },
      timeScale: {
        borderColor: 'rgba(107, 114, 128, 0.2)',
        timeVisible: true,
        secondsVisible: false,
      },
    })

    chartRef.current = chart

    // Handle resize
    const handleResize = () => {
      if (chartContainerRef.current) {
        chart.applyOptions({ width: chartContainerRef.current.clientWidth })
      }
    }

    window.addEventListener('resize', handleResize)

    // Crosshair move handler
    chart.subscribeCrosshairMove((param) => {
      if (param.time && param.seriesData.size > 0) {
        const priceData = param.seriesData.get(priceSeriesRef.current!)
        if (priceData) {
          const d = data.find(item => item.date === param.time)
          if (d) {
            setCrosshairData({
              time: d.date,
              open: d.open,
              high: d.high,
              low: d.low,
              close: d.close,
              volume: d.volume,
            })
          }
        }
      } else {
        setCrosshairData(null)
      }
    })

    return () => {
      window.removeEventListener('resize', handleResize)
      chart.remove()
    }
  }, [height])

  // Update series based on chart type and data
  useEffect(() => {
    if (!chartRef.current) return

    const chart = chartRef.current
    const filteredData = getFilteredData(timeRange)

    // Remove existing series safely
    try {
      if (priceSeriesRef.current) {
        chart.removeSeries(priceSeriesRef.current)
        priceSeriesRef.current = null
      }
    } catch {
      priceSeriesRef.current = null
    }

    try {
      if (volumeSeriesRef.current) {
        chart.removeSeries(volumeSeriesRef.current)
        volumeSeriesRef.current = null
      }
    } catch {
      volumeSeriesRef.current = null
    }

    if (filteredData.length === 0) return

    // Create price series based on type
    if (chartType === 'candlestick') {
      const candlestickSeries = chart.addCandlestickSeries({
        upColor: '#22c55e',
        downColor: '#ef4444',
        borderUpColor: '#22c55e',
        borderDownColor: '#ef4444',
        wickUpColor: '#22c55e',
        wickDownColor: '#ef4444',
      })

      const candleData: CandlestickData[] = filteredData.map(d => ({
        time: d.date as Time,
        open: d.open,
        high: d.high,
        low: d.low,
        close: d.close,
      }))

      candlestickSeries.setData(candleData)
      priceSeriesRef.current = candlestickSeries
    } else if (chartType === 'line') {
      const lineSeries = chart.addLineSeries({
        color: '#3b82f6',
        lineWidth: 2,
      })

      const lineData: LineData[] = filteredData.map(d => ({
        time: d.date as Time,
        value: d.close,
      }))

      lineSeries.setData(lineData)
      priceSeriesRef.current = lineSeries
    } else {
      const areaSeries = chart.addAreaSeries({
        lineColor: '#3b82f6',
        topColor: 'rgba(59, 130, 246, 0.4)',
        bottomColor: 'rgba(59, 130, 246, 0.0)',
        lineWidth: 2,
      })

      const areaData: LineData[] = filteredData.map(d => ({
        time: d.date as Time,
        value: d.close,
      }))

      areaSeries.setData(areaData)
      priceSeriesRef.current = areaSeries
    }

    // Add volume series
    if (showVolume) {
      const volumeSeries = chart.addHistogramSeries({
        color: 'rgba(107, 114, 128, 0.3)',
        priceFormat: {
          type: 'volume',
        },
        priceScaleId: '',
      })

      volumeSeries.priceScale().applyOptions({
        scaleMargins: {
          top: 0.8,
          bottom: 0,
        },
      })

      const volumeData = filteredData.map(d => ({
        time: d.date as Time,
        value: d.volume,
        color: d.close >= d.open
          ? 'rgba(34, 197, 94, 0.3)'
          : 'rgba(239, 68, 68, 0.3)',
      }))

      volumeSeries.setData(volumeData)
      volumeSeriesRef.current = volumeSeries
    }

    // Fit content
    chart.timeScale().fitContent()
  }, [data, chartType, timeRange, showVolume])

  const handleTimeRangeChange = (range: TimeRange) => {
    setTimeRange(range)
    onTimeRangeChange?.(range)
  }

  const latestData = data.length > 0 ? data[data.length - 1] : null
  const displayData = crosshairData || (latestData ? {
    time: latestData.date,
    open: latestData.open,
    high: latestData.high,
    low: latestData.low,
    close: latestData.close,
    volume: latestData.volume,
  } : null)

  const formatVolume = (vol: number) => {
    if (vol >= 1e9) return `${(vol / 1e9).toFixed(2)}B`
    if (vol >= 1e6) return `${(vol / 1e6).toFixed(2)}M`
    if (vol >= 1e3) return `${(vol / 1e3).toFixed(2)}K`
    return vol.toString()
  }

  return (
    <div className="space-y-3">
      {/* Chart Controls */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        {/* Chart Type Selector */}
        <div className="flex gap-1 bg-gray-100 dark:bg-gray-700 rounded-lg p-1">
          {(['candlestick', 'line', 'area'] as ChartType[]).map(type => (
            <button
              key={type}
              onClick={() => setChartType(type)}
              className={`px-3 py-1.5 text-sm rounded-md transition-colors ${
                chartType === type
                  ? 'bg-white dark:bg-gray-600 shadow text-primary-600 dark:text-primary-400'
                  : 'text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200'
              }`}
            >
              {type === 'candlestick' ? '캔들' : type === 'line' ? '라인' : '영역'}
            </button>
          ))}
        </div>

        {/* Time Range Selector */}
        <div className="flex gap-1 bg-gray-100 dark:bg-gray-700 rounded-lg p-1">
          {(['1W', '1M', '3M', '6M', '1Y', 'ALL'] as TimeRange[]).map(range => (
            <button
              key={range}
              onClick={() => handleTimeRangeChange(range)}
              className={`px-3 py-1.5 text-sm rounded-md transition-colors ${
                timeRange === range
                  ? 'bg-white dark:bg-gray-600 shadow text-primary-600 dark:text-primary-400'
                  : 'text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200'
              }`}
            >
              {range}
            </button>
          ))}
        </div>
      </div>

      {/* Price Info Bar */}
      {displayData && (
        <div className="flex flex-wrap items-center gap-4 text-sm">
          <span className="text-gray-500">{displayData.time}</span>
          <span>
            <span className="text-gray-500">시가</span>{' '}
            <span className="font-medium">{currency}{displayData.open.toLocaleString()}</span>
          </span>
          <span>
            <span className="text-gray-500">고가</span>{' '}
            <span className="font-medium text-green-600">{currency}{displayData.high.toLocaleString()}</span>
          </span>
          <span>
            <span className="text-gray-500">저가</span>{' '}
            <span className="font-medium text-red-600">{currency}{displayData.low.toLocaleString()}</span>
          </span>
          <span>
            <span className="text-gray-500">종가</span>{' '}
            <span className="font-medium">{currency}{displayData.close.toLocaleString()}</span>
          </span>
          <span>
            <span className="text-gray-500">거래량</span>{' '}
            <span className="font-medium">{formatVolume(displayData.volume)}</span>
          </span>
        </div>
      )}

      {/* Chart Container */}
      <div
        ref={chartContainerRef}
        className="w-full rounded-lg overflow-hidden"
        style={{ height: `${height}px` }}
      />

      {/* No Data Message */}
      {data.length === 0 && (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-100 dark:bg-gray-800 rounded-lg">
          <p className="text-gray-500">데이터가 없습니다</p>
        </div>
      )}
    </div>
  )
}
