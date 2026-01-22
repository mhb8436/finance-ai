/**
 * TypeScript type definitions for FinanceAI
 */

export interface StockInfo {
  symbol: string
  name: string
  market: 'US' | 'KR'
  sector: string | null
  industry: string | null
  market_cap: number | null
  pe_ratio: number | null
  pb_ratio: number | null
  dividend_yield: number | null
}

export interface PriceData {
  date: string
  open: number
  high: number
  low: number
  close: number
  volume: number
}

export interface TechnicalIndicators {
  sma_20?: number[]
  sma_50?: number[]
  ema_12?: number[]
  ema_26?: number[]
  rsi_14?: number[]
  macd_line?: number[]
  macd_signal?: number[]
  macd_histogram?: number[]
  bollinger_upper?: number[]
  bollinger_middle?: number[]
  bollinger_lower?: number[]
}

export interface AnalysisResult {
  symbol: string
  market: string
  analysis_type: 'technical' | 'fundamental'
  result: Record<string, unknown>
  summary: string | null
}

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}

export interface ChatResponse {
  response: string
  sources: Array<{
    type: string
    symbol?: string
    query?: string
  }>
}

export interface ResearchReport {
  research_id: string
  topic: string
  status: string
  report_path: string | null
}

// =============================================================================
// Pipeline Research Types
// =============================================================================

export type ResearchStatus = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'

export interface PipelineResearchRequest {
  topic: string
  symbols?: string[]
  market?: 'US' | 'KR' | 'Both'
  context?: string
  skip_rephrase?: boolean
  output_format?: 'markdown' | 'json' | 'html'
  max_topics?: number
}

export interface PipelineResearchResponse {
  research_id: string
  topic: string
  status: ResearchStatus
  message: string
  created_at: string
}

export interface ResearchProgress {
  event: string
  stage: string
  details: Record<string, unknown>
}

export interface ResearchStatusResponse {
  research_id: string
  status: ResearchStatus
  topic: string
  created_at: string
  started_at: string | null
  completed_at: string | null
  current_stage: string | null
  progress: ResearchProgress | null
  error: string | null
  result: ResearchResult | null
}

export interface ResearchResult {
  report?: {
    report_content: string
    executive_summary: string
    main_topic: string
    research_objective: string
    generated_at: string
  }
  statistics?: {
    total_topics: number
    completed_topics: number
    failed_topics: number
    total_tool_calls: number
  }
}

export interface ResearchListItem {
  research_id: string
  topic: string
  status: ResearchStatus
  created_at: string
  completed_at: string | null
}

export interface ResearchTool {
  name: string
  description: string
}

// WebSocket event types
export interface WSConnectedEvent {
  type: 'connected'
  research_id: string
}

export interface WSCurrentStateEvent {
  type: 'current_state'
  data: ResearchStatusResponse
}

export interface WSUpdateEvent {
  type: 'update'
  data: ResearchStatusResponse
}

export interface WSHeartbeatEvent {
  type: 'heartbeat'
}

export interface WSFinalEvent {
  type: 'final'
  status: ResearchStatus
  result: ResearchResult | null
  error: string | null
}

export interface WSErrorEvent {
  type: 'error'
  message: string
}

export type WSEvent = WSConnectedEvent | WSCurrentStateEvent | WSUpdateEvent | WSHeartbeatEvent | WSFinalEvent | WSErrorEvent

// =============================================================================
// Phase 5: Advanced Analysis Types
// =============================================================================

// Sentiment Analysis
export interface SentimentRequest {
  symbol?: string
  market?: 'US' | 'KR'
  video_url?: string
  youtube_channel?: string
  source?: 'news' | 'youtube' | 'combined'
  news_limit?: number
}

export interface SentimentResponse {
  success: boolean
  symbol?: string
  source: string
  sentiment_score?: number
  sentiment_label?: string
  confidence?: number
  key_themes: string[]
  summary?: string
  data: Record<string, unknown>
}

// Valuation Analysis
export interface ValuationRequest {
  symbol?: string
  symbols?: string[]
  market?: 'US' | 'KR'
  quick?: boolean
}

export interface ValuationMethod {
  method: string
  value: number
  weight: number
}

export interface ValuationResponse {
  success: boolean
  symbol?: string
  market: string
  current_price?: number
  fair_value_base?: number
  fair_value_low?: number
  fair_value_high?: number
  upside_potential?: number
  valuation_status?: string
  recommendation?: string
  methods_used: ValuationMethod[]
  summary?: string
}

// Recommendation
export type InvestmentStyle = 'growth' | 'value' | 'momentum' | 'balanced'
export type TimeHorizon = 'short' | 'medium' | 'long'

export interface RecommendationRequest {
  symbol?: string
  symbols?: string[]
  market?: 'US' | 'KR'
  investment_style?: InvestmentStyle
  time_horizon?: TimeHorizon
  youtube_channel?: string
  quick?: boolean
}

export interface RecommendationResponse {
  success: boolean
  symbol?: string
  market: string
  recommendation?: string
  overall_score?: number
  confidence?: number
  current_price?: number
  target_price?: number
  upside_potential?: number
  catalysts: string[]
  risks: string[]
  summary?: string
  analyses: Record<string, unknown>
}

// =============================================================================
// Knowledge Base Types
// =============================================================================

export interface KnowledgeBase {
  name: string
  provider: string
  retrieval_mode: string
  total_chunks: number
  document_count: number
  created_at: string
  updated_at: string
  embedding_model: string
  chunk_strategy: string
}

export interface KBDocument {
  filename: string
  size: number
  modified: number
}

export interface KBSearchRequest {
  query: string
  top_k?: number
  generate_answer?: boolean
}

export interface KBSearchSource {
  content: string
  source: string
  type: string
  relevance: number
}

export interface KBSearchResponse {
  query: string
  answer: string
  sources: KBSearchSource[]
  num_results: number
}

export interface KBUploadResponse {
  filename: string
  kb_name: string
  file?: string
  chunks_added: number
}

// =============================================================================
// YouTube Types
// =============================================================================

export interface YouTubeTranscriptRequest {
  video_url: string
  languages?: string[]
  store_to_rag?: boolean
  kb_name?: string
}

export interface YouTubeTranscriptResponse {
  success: boolean
  video_id?: string
  title?: string
  channel_name?: string
  language?: string
  duration_minutes?: number
  text?: string
  text_preview?: string
  stored_to_rag?: boolean
  kb_name?: string
  error?: string
}

export interface YouTubeVideo {
  video_id: string
  title: string
  channel_name: string
  published?: string
  description?: string
  thumbnail_url?: string
  url: string
}

export interface YouTubeChannelVideosRequest {
  channel: string
  max_results?: number
}

export interface YouTubeChannelVideosResponse {
  success: boolean
  channel: string
  video_count: number
  videos: YouTubeVideo[]
  error?: string
}

export interface YouTubeChannelTranscriptsRequest {
  channel: string
  max_videos?: number
  languages?: string[]
  kb_name?: string
}

export interface YouTubePresetChannel {
  name: string
  channel_id: string
  description: string
}
