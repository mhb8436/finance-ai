"""Tools Module.

Provides various tools for data fetching and analysis:
- Stock Data: Price, info, financials
- Technical Analysis: Indicators (SMA, EMA, RSI, MACD, etc.)
- Web Search: DuckDuckGo, Naver, Google News
- RAG: Knowledge base search
- YouTube: Transcripts, channel videos
- Pipeline Integration: Pre-configured handlers for ResearchPipeline
"""

from .web_search import (
    web_search,
    search_duckduckgo,
    search_duckduckgo_news,
    search_naver,
    search_google_news_rss,
    search_and_store_to_rag,
    SearchResult,
    WEB_SEARCH_TOOL_DEFINITIONS,
    execute_web_search_tool,
)

from .rag_tool import (
    RAG_TOOL_DEFINITIONS,
    RAG_TOOL_FUNCTIONS,
    search_knowledge_base,
    list_knowledge_bases,
    execute_rag_tool,
)

from .youtube_tool import (
    get_transcript,
    get_channel_videos,
    get_transcript_and_store_to_rag,
    get_channel_videos_and_store_to_rag,
    get_channel_presets,
    YouTubeVideo,
    YouTubeTranscript,
    YOUTUBE_TOOL_DEFINITIONS,
    execute_youtube_tool,
    KOREAN_INVESTMENT_CHANNELS,
)

from .pipeline_tools import (
    get_pipeline_tool_handlers,
    get_tool_descriptions,
    create_configured_pipeline,
    quick_research,
    # Individual handlers
    stock_data_handler,
    financials_handler,
    technical_analysis_handler,
    rag_search_handler,
    web_search_handler,
    news_search_handler,
    youtube_handler,
)

__all__ = [
    # Web Search
    "web_search",
    "search_duckduckgo",
    "search_duckduckgo_news",
    "search_naver",
    "search_google_news_rss",
    "search_and_store_to_rag",
    "SearchResult",
    "WEB_SEARCH_TOOL_DEFINITIONS",
    "execute_web_search_tool",
    # RAG
    "RAG_TOOL_DEFINITIONS",
    "RAG_TOOL_FUNCTIONS",
    "search_knowledge_base",
    "list_knowledge_bases",
    "execute_rag_tool",
    # YouTube
    "get_transcript",
    "get_channel_videos",
    "get_transcript_and_store_to_rag",
    "get_channel_videos_and_store_to_rag",
    "get_channel_presets",
    "YouTubeVideo",
    "YouTubeTranscript",
    "YOUTUBE_TOOL_DEFINITIONS",
    "execute_youtube_tool",
    "KOREAN_INVESTMENT_CHANNELS",
    # Pipeline Integration
    "get_pipeline_tool_handlers",
    "get_tool_descriptions",
    "create_configured_pipeline",
    "quick_research",
    "stock_data_handler",
    "financials_handler",
    "technical_analysis_handler",
    "rag_search_handler",
    "web_search_handler",
    "news_search_handler",
    "youtube_handler",
]
