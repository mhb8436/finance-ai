'use client'

import { useState, useEffect, useCallback } from 'react'
import {
  Youtube,
  Play,
  Loader2,
  Search,
  Clock,
  ExternalLink,
  Database,
  CheckCircle,
  AlertCircle,
  FileText,
  ChevronDown,
  ChevronUp,
} from 'lucide-react'
import { youtubeApi, knowledgeBaseApi } from '@/lib/api'
import type {
  YouTubeVideo,
  YouTubeTranscriptResponse,
  YouTubePresetChannel,
} from '@/types'

export default function YouTubePage() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Preset channels
  const [presetChannels, setPresetChannels] = useState<YouTubePresetChannel[]>([])
  const [selectedPreset, setSelectedPreset] = useState<string>('')

  // Channel/Video input
  const [inputType, setInputType] = useState<'video' | 'channel'>('video')
  const [videoUrl, setVideoUrl] = useState('')
  const [channelInput, setChannelInput] = useState('')

  // Results
  const [transcript, setTranscript] = useState<YouTubeTranscriptResponse | null>(null)
  const [videos, setVideos] = useState<YouTubeVideo[]>([])
  const [selectedVideo, setSelectedVideo] = useState<YouTubeVideo | null>(null)
  const [expandedTranscript, setExpandedTranscript] = useState(false)

  // RAG storage
  const [storeToRag, setStoreToRag] = useState(false)
  const [kbName, setKbName] = useState('youtube')
  const [storingToRag, setStoringToRag] = useState(false)
  const [ragResult, setRagResult] = useState<{ success: boolean; message: string } | null>(null)

  // Load presets on mount
  useEffect(() => {
    const loadPresets = async () => {
      const response = await youtubeApi.getPresetChannels()
      if (response.data) {
        setPresetChannels(response.data.channels)
      }
    }
    loadPresets()
  }, [])

  // Handle preset selection
  useEffect(() => {
    if (selectedPreset) {
      setChannelInput(selectedPreset)
    }
  }, [selectedPreset])

  const handleGetTranscript = async () => {
    if (!videoUrl.trim()) return

    setLoading(true)
    setError(null)
    setTranscript(null)
    setExpandedTranscript(false)

    const response = await youtubeApi.getTranscript({
      video_url: videoUrl,
      store_to_rag: storeToRag,
      kb_name: storeToRag ? kbName : undefined,
    })

    if (response.data) {
      if (response.data.success) {
        setTranscript(response.data)
      } else {
        setError(response.data.error || '자막을 가져올 수 없습니다.')
      }
    } else if (response.error) {
      setError(response.error)
    }
    setLoading(false)
  }

  const handleGetChannelVideos = async () => {
    if (!channelInput.trim()) return

    setLoading(true)
    setError(null)
    setVideos([])
    setSelectedVideo(null)
    setTranscript(null)

    const response = await youtubeApi.getChannelVideos({
      channel: channelInput,
      max_results: 10,
    })

    if (response.data) {
      if (response.data.success) {
        setVideos(response.data.videos)
      } else {
        setError(response.data.error || '채널 영상을 가져올 수 없습니다.')
      }
    } else if (response.error) {
      setError(response.error)
    }
    setLoading(false)
  }

  const handleVideoSelect = async (video: YouTubeVideo) => {
    setSelectedVideo(video)
    setTranscript(null)
    setExpandedTranscript(false)
    setLoading(true)
    setError(null)

    const response = await youtubeApi.getTranscript({
      video_url: video.url,
      store_to_rag: false,
    })

    if (response.data) {
      if (response.data.success) {
        setTranscript(response.data)
      } else {
        setError(response.data.error || '자막을 가져올 수 없습니다.')
      }
    } else if (response.error) {
      setError(response.error)
    }
    setLoading(false)
  }

  const handleStoreChannelToRag = async () => {
    if (!channelInput.trim()) return

    setStoringToRag(true)
    setRagResult(null)
    setError(null)

    const response = await youtubeApi.getChannelTranscripts({
      channel: channelInput,
      max_videos: 5,
      kb_name: kbName,
    })

    if (response.data) {
      setRagResult({
        success: true,
        message: `${response.data.stored_transcripts}개의 영상 자막이 "${kbName}" 지식 베이스에 저장되었습니다.`,
      })
    } else if (response.error) {
      setRagResult({
        success: false,
        message: response.error,
      })
    }
    setStoringToRag(false)
  }

  const handleStoreTranscriptToRag = async () => {
    if (!transcript?.video_id || !transcript.title) return

    setStoringToRag(true)
    setRagResult(null)

    const response = await youtubeApi.getTranscript({
      video_url: `https://www.youtube.com/watch?v=${transcript.video_id}`,
      store_to_rag: true,
      kb_name: kbName,
    })

    if (response.data?.success) {
      setRagResult({
        success: true,
        message: `"${transcript.title}" 자막이 "${kbName}" 지식 베이스에 저장되었습니다.`,
      })
    } else {
      setRagResult({
        success: false,
        message: response.data?.error || response.error || '저장 실패',
      })
    }
    setStoringToRag(false)
  }

  const formatDuration = (minutes: number) => {
    const hrs = Math.floor(minutes / 60)
    const mins = Math.floor(minutes % 60)
    if (hrs > 0) {
      return `${hrs}시간 ${mins}분`
    }
    return `${mins}분`
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <Youtube className="w-8 h-8 text-red-600" />
            <h1 className="text-2xl md:text-3xl font-bold text-gray-900 dark:text-white">
              YouTube 분석
            </h1>
          </div>
          <p className="text-gray-600 dark:text-gray-400">
            유튜브 영상의 자막을 추출하고 지식 베이스에 저장합니다
          </p>
        </div>

        {/* Error Banner */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg flex items-center gap-3">
            <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0" />
            <p className="text-red-600 dark:text-red-400">{error}</p>
          </div>
        )}

        {/* RAG Result Banner */}
        {ragResult && (
          <div className={`mb-6 p-4 rounded-lg flex items-center gap-3 ${
            ragResult.success
              ? 'bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800'
              : 'bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800'
          }`}>
            {ragResult.success ? (
              <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0" />
            ) : (
              <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0" />
            )}
            <p className={ragResult.success ? 'text-green-700 dark:text-green-300' : 'text-red-600 dark:text-red-400'}>
              {ragResult.message}
            </p>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Input Section */}
          <div className="lg:col-span-1 space-y-6">
            {/* Input Type Toggle */}
            <div className="card">
              <div className="flex gap-2 mb-4">
                <button
                  onClick={() => setInputType('video')}
                  className={`flex-1 py-2 px-4 rounded-lg font-medium transition-colors ${
                    inputType === 'video'
                      ? 'bg-primary-600 text-white'
                      : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
                  }`}
                >
                  영상 URL
                </button>
                <button
                  onClick={() => setInputType('channel')}
                  className={`flex-1 py-2 px-4 rounded-lg font-medium transition-colors ${
                    inputType === 'channel'
                      ? 'bg-primary-600 text-white'
                      : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
                  }`}
                >
                  채널
                </button>
              </div>

              {inputType === 'video' ? (
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium mb-2">YouTube 영상 URL</label>
                    <input
                      type="text"
                      value={videoUrl}
                      onChange={(e) => setVideoUrl(e.target.value)}
                      placeholder="https://www.youtube.com/watch?v=..."
                      className="input w-full"
                    />
                  </div>

                  <div className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      id="storeToRag"
                      checked={storeToRag}
                      onChange={(e) => setStoreToRag(e.target.checked)}
                      className="w-4 h-4 rounded border-gray-300"
                    />
                    <label htmlFor="storeToRag" className="text-sm">
                      지식 베이스에 저장
                    </label>
                  </div>

                  {storeToRag && (
                    <div>
                      <label className="block text-sm font-medium mb-2">지식 베이스 이름</label>
                      <input
                        type="text"
                        value={kbName}
                        onChange={(e) => setKbName(e.target.value)}
                        placeholder="youtube"
                        className="input w-full"
                      />
                    </div>
                  )}

                  <button
                    onClick={handleGetTranscript}
                    disabled={loading || !videoUrl.trim()}
                    className="btn btn-primary w-full"
                  >
                    {loading ? (
                      <Loader2 className="w-5 h-5 animate-spin" />
                    ) : (
                      <>
                        <Play className="w-5 h-5 mr-2" />
                        자막 가져오기
                      </>
                    )}
                  </button>
                </div>
              ) : (
                <div className="space-y-4">
                  {/* Preset Channels */}
                  <div>
                    <label className="block text-sm font-medium mb-2">추천 채널</label>
                    <select
                      value={selectedPreset}
                      onChange={(e) => setSelectedPreset(e.target.value)}
                      className="input w-full"
                    >
                      <option value="">직접 입력</option>
                      {presetChannels.map((channel) => (
                        <option key={channel.name} value={channel.name}>
                          {channel.name} - {channel.description}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-2">채널 입력</label>
                    <input
                      type="text"
                      value={channelInput}
                      onChange={(e) => setChannelInput(e.target.value)}
                      placeholder="채널명, @handle, 또는 채널 ID"
                      className="input w-full"
                    />
                  </div>

                  <button
                    onClick={handleGetChannelVideos}
                    disabled={loading || !channelInput.trim()}
                    className="btn btn-primary w-full"
                  >
                    {loading ? (
                      <Loader2 className="w-5 h-5 animate-spin" />
                    ) : (
                      <>
                        <Search className="w-5 h-5 mr-2" />
                        영상 목록 가져오기
                      </>
                    )}
                  </button>

                  {videos.length > 0 && (
                    <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
                      <label className="block text-sm font-medium mb-2">
                        RAG 저장 (최근 5개 영상)
                      </label>
                      <input
                        type="text"
                        value={kbName}
                        onChange={(e) => setKbName(e.target.value)}
                        placeholder="지식 베이스 이름"
                        className="input w-full mb-2"
                      />
                      <button
                        onClick={handleStoreChannelToRag}
                        disabled={storingToRag}
                        className="btn btn-secondary w-full"
                      >
                        {storingToRag ? (
                          <Loader2 className="w-5 h-5 animate-spin" />
                        ) : (
                          <>
                            <Database className="w-5 h-5 mr-2" />
                            채널 자막 RAG 저장
                          </>
                        )}
                      </button>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>

          {/* Results Section */}
          <div className="lg:col-span-2 space-y-6">
            {/* Video List */}
            {videos.length > 0 && (
              <div className="card">
                <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                  <Youtube className="w-5 h-5 text-red-600" />
                  채널 영상 ({videos.length}개)
                </h3>
                <div className="space-y-3 max-h-96 overflow-y-auto">
                  {videos.map((video) => (
                    <div
                      key={video.video_id}
                      onClick={() => handleVideoSelect(video)}
                      className={`flex gap-3 p-3 rounded-lg cursor-pointer transition-colors ${
                        selectedVideo?.video_id === video.video_id
                          ? 'bg-primary-50 dark:bg-primary-900/20 border border-primary-200 dark:border-primary-800'
                          : 'bg-gray-50 dark:bg-gray-800 hover:bg-gray-100 dark:hover:bg-gray-700'
                      }`}
                    >
                      {video.thumbnail_url && (
                        <img
                          src={video.thumbnail_url}
                          alt={video.title}
                          className="w-32 h-20 object-cover rounded flex-shrink-0"
                        />
                      )}
                      <div className="flex-1 min-w-0">
                        <h4 className="font-medium line-clamp-2">{video.title}</h4>
                        <div className="flex items-center gap-2 mt-1 text-sm text-gray-500">
                          <span>{video.channel_name}</span>
                          {video.published && (
                            <>
                              <span>•</span>
                              <span>{video.published}</span>
                            </>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Transcript Result */}
            {transcript && (
              <div className="card">
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <h3 className="text-lg font-semibold flex items-center gap-2">
                      <FileText className="w-5 h-5 text-primary-600" />
                      자막
                    </h3>
                    <p className="text-sm text-gray-500 mt-1">
                      {transcript.title}
                    </p>
                  </div>
                  <a
                    href={`https://www.youtube.com/watch?v=${transcript.video_id}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-gray-400 hover:text-gray-600"
                  >
                    <ExternalLink className="w-5 h-5" />
                  </a>
                </div>

                {/* Metadata */}
                <div className="flex flex-wrap gap-3 mb-4">
                  <span className="px-3 py-1 bg-gray-100 dark:bg-gray-700 rounded-full text-sm">
                    {transcript.channel_name}
                  </span>
                  {transcript.duration_minutes && (
                    <span className="px-3 py-1 bg-gray-100 dark:bg-gray-700 rounded-full text-sm flex items-center gap-1">
                      <Clock className="w-4 h-4" />
                      {formatDuration(transcript.duration_minutes)}
                    </span>
                  )}
                  <span className="px-3 py-1 bg-gray-100 dark:bg-gray-700 rounded-full text-sm">
                    {transcript.language}
                  </span>
                  {transcript.stored_to_rag && (
                    <span className="px-3 py-1 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 rounded-full text-sm flex items-center gap-1">
                      <CheckCircle className="w-4 h-4" />
                      RAG 저장됨
                    </span>
                  )}
                </div>

                {/* Transcript Text */}
                <div className="relative">
                  <div className={`
                    bg-gray-50 dark:bg-gray-800 rounded-lg p-4 overflow-y-auto
                    ${expandedTranscript ? 'max-h-[600px]' : 'max-h-64'}
                  `}>
                    <p className="whitespace-pre-wrap text-sm leading-relaxed">
                      {expandedTranscript ? transcript.text : transcript.text_preview}
                    </p>
                  </div>
                  {transcript.text && transcript.text.length > 2000 && (
                    <button
                      onClick={() => setExpandedTranscript(!expandedTranscript)}
                      className="mt-2 text-sm text-primary-600 hover:text-primary-700 flex items-center gap-1"
                    >
                      {expandedTranscript ? (
                        <>
                          <ChevronUp className="w-4 h-4" />
                          접기
                        </>
                      ) : (
                        <>
                          <ChevronDown className="w-4 h-4" />
                          전체 보기
                        </>
                      )}
                    </button>
                  )}
                </div>

                {/* Store to RAG Button */}
                {!transcript.stored_to_rag && (
                  <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
                    <div className="flex items-center gap-3">
                      <input
                        type="text"
                        value={kbName}
                        onChange={(e) => setKbName(e.target.value)}
                        placeholder="지식 베이스 이름"
                        className="input flex-1"
                      />
                      <button
                        onClick={handleStoreTranscriptToRag}
                        disabled={storingToRag}
                        className="btn btn-secondary"
                      >
                        {storingToRag ? (
                          <Loader2 className="w-5 h-5 animate-spin" />
                        ) : (
                          <>
                            <Database className="w-5 h-5 mr-2" />
                            RAG 저장
                          </>
                        )}
                      </button>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Empty State */}
            {!loading && !transcript && videos.length === 0 && (
              <div className="card">
                <div className="text-center py-12 text-gray-500">
                  <Youtube className="w-16 h-16 mx-auto mb-4 opacity-50" />
                  <p className="text-lg mb-2">유튜브 영상 자막 분석</p>
                  <p className="text-sm">
                    {inputType === 'video'
                      ? '영상 URL을 입력하고 자막을 추출하세요'
                      : '채널을 선택하거나 입력하여 최신 영상을 확인하세요'}
                  </p>
                  <div className="mt-6 space-y-2 text-sm text-gray-400">
                    <p>지원하는 입력 형식:</p>
                    <ul className="list-disc list-inside">
                      <li>YouTube 영상 URL</li>
                      <li>채널 핸들 (@channel)</li>
                      <li>채널 ID</li>
                      <li>사전 등록된 채널명</li>
                    </ul>
                  </div>
                </div>
              </div>
            )}

            {/* Loading State */}
            {loading && (
              <div className="card">
                <div className="text-center py-12">
                  <Loader2 className="w-12 h-12 mx-auto mb-4 animate-spin text-primary-600" />
                  <p className="text-gray-600 dark:text-gray-400">
                    {inputType === 'video' ? '자막을 가져오는 중...' : '영상 목록을 가져오는 중...'}
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
