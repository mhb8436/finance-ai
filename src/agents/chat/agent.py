"""Chat Agent for AI-powered Q&A about stocks.

Integrated tools (via ToolRouter with retry/timeout):
- Stock data (price, info, financials)
- Web search (DuckDuckGo, Naver, Google News)
- YouTube (transcript, channel videos)
- RAG (knowledge base search)

Uses ToolRouter for:
- Retry logic (configurable retries)
- Timeout handling (30s default)
- Error handling and fallback
- Unified result format
"""

import json
from typing import Any, AsyncIterator

from src.agents.base_agent import BaseAgent
from src.services.llm import ToolCall


SYSTEM_PROMPT = """You are a helpful AI assistant specializing in stock market analysis and financial information.

## Your Capabilities

### 1. Stock Data
- Real-time stock prices and historical data
- Company information and key metrics
- Financial ratios and statements

### 2. Web Search
- Search the web for news, articles, and analysis
- Free providers: DuckDuckGo, Google News, Naver (Korean)
- Premium providers: Serper (Google SERP), Tavily (AI-powered)
- Finance-optimized search for stock news
- Can store search results in knowledge base for future reference

### 3. YouTube Analysis
- Extract transcripts from YouTube videos
- Get recent videos from investment channels
- Preset Korean channels: 삼프로TV, 슈카월드, 신사임당, 부읽남, 언더스탠딩, etc.
- Can store transcripts in knowledge base

### 4. Knowledge Base (RAG)
- Search through stored documents and information
- Combines user-uploaded documents, web search results, and YouTube transcripts

## Guidelines
- When users ask about stocks, use tools to fetch real-time data
- For recent news or events, use web_search tool
- For YouTube content analysis, use youtube tools
- Search knowledge base first if the query might be answered by stored documents
- Always cite your sources
- Respond in the same language as the user (Korean or English)
- If uncertain, say so rather than making up information

## Example Queries You Can Handle
- "삼성전자 주가 알려줘" → get_stock_price
- "애플 최근 뉴스 검색해줘" → web_search
- "삼프로TV 최근 영상 보여줘" → get_channel_recent_videos
- "이 유튜브 영상 분석해줘: [URL]" → get_youtube_transcript
- "저장된 문서에서 반도체 관련 내용 찾아줘" → search_knowledge_base
"""


# =============================================================================
# Tool Definitions
# =============================================================================

STOCK_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_stock_price",
            "description": "Get historical stock price data for a specific stock",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Stock symbol (e.g., AAPL, 005930, 삼성전자)",
                    },
                    "market": {
                        "type": "string",
                        "enum": ["US", "KR"],
                        "description": "Market (US for US stocks, KR for Korean stocks)",
                    },
                    "period": {
                        "type": "string",
                        "description": "Time period: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y",
                        "default": "1mo",
                    },
                },
                "required": ["symbol"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_stock_info",
            "description": "Get stock information including company details, sector, and key metrics",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Stock symbol",
                    },
                    "market": {
                        "type": "string",
                        "enum": ["US", "KR"],
                        "description": "Market",
                    },
                },
                "required": ["symbol"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_financial_ratios",
            "description": "Get financial ratios like P/E, P/B, ROE for a stock",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Stock symbol",
                    },
                    "market": {
                        "type": "string",
                        "enum": ["US", "KR"],
                        "description": "Market",
                    },
                },
                "required": ["symbol"],
            },
        },
    },
]


WEB_SEARCH_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": (
                "Search the web for information, news, articles. "
                "Supports multiple providers: duckduckgo (general, free), google_news (news, free), "
                "naver_news/naver_blog (Korean content), serper (Google SERP), "
                "tavily (AI-powered research). "
                "Can optionally store results in knowledge base for future reference."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query",
                    },
                    "providers": {
                        "type": "string",
                        "description": (
                            "Comma-separated search providers: duckduckgo, duckduckgo_news, "
                            "google_news, naver_news, naver_blog, serper, serper_news, tavily. "
                            "Default: duckduckgo,google_news"
                        ),
                    },
                    "topic": {
                        "type": "string",
                        "enum": ["general", "news", "finance"],
                        "description": "Topic filter for Tavily (default: general)",
                        "default": "general",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Max results per provider (default: 5)",
                        "default": 5,
                    },
                    "store_to_rag": {
                        "type": "boolean",
                        "description": "Store results in knowledge base for future reference",
                        "default": False,
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_finance_news",
            "description": (
                "Search for financial news and stock market information. "
                "Optimized for finding recent news about stocks, companies, and markets."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query (e.g., 'Tesla earnings', 'AAPL stock news')",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum results to return (default: 10)",
                        "default": 10,
                    },
                },
                "required": ["query"],
            },
        },
    },
]


YOUTUBE_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_youtube_transcript",
            "description": (
                "Get transcript (subtitles) from a YouTube video. "
                "Use this to analyze video content. Works without API key."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "video_url": {
                        "type": "string",
                        "description": "YouTube video URL or video ID",
                    },
                    "store_to_rag": {
                        "type": "boolean",
                        "description": "Store transcript in knowledge base",
                        "default": False,
                    },
                },
                "required": ["video_url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_channel_recent_videos",
            "description": (
                "Get recent videos from a YouTube channel. "
                "Supports preset Korean investment channels: "
                "삼프로TV, 슈카월드, 신사임당, 부읽남, 월급쟁이부자들TV, 언더스탠딩, etc. "
                "Can also use channel handle (@name) or channel ID."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "channel": {
                        "type": "string",
                        "description": (
                            "Channel name (preset), handle (@name), or channel ID. "
                            "Presets: 삼프로TV, 슈카월드, 신사임당, 부읽남, 언더스탠딩"
                        ),
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum videos to return (default: 5)",
                        "default": 5,
                    },
                },
                "required": ["channel"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_channel_transcripts_to_rag",
            "description": (
                "Get transcripts from recent videos of a channel and store in knowledge base. "
                "Useful for analyzing a channel's recent content."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "channel": {
                        "type": "string",
                        "description": "Channel name, handle, or ID",
                    },
                    "max_videos": {
                        "type": "integer",
                        "description": "Maximum videos to process (default: 3)",
                        "default": 3,
                    },
                    "kb_name": {
                        "type": "string",
                        "description": "Knowledge base name to store transcripts",
                        "default": "youtube",
                    },
                },
                "required": ["channel"],
            },
        },
    },
]


RAG_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_knowledge_base",
            "description": (
                "Search the knowledge base for relevant information. "
                "The knowledge base contains user-uploaded documents, "
                "web search results, and YouTube transcripts that were stored. "
                "Use this to find information from previously stored content."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query",
                    },
                    "kb_name": {
                        "type": "string",
                        "description": "Knowledge base name (default: 'default')",
                        "default": "default",
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Number of results (default: 5)",
                        "default": 5,
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_knowledge_bases",
            "description": "List all available knowledge bases and their statistics",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
]


# Combine all tools
ALL_TOOLS = STOCK_TOOLS + WEB_SEARCH_TOOLS + YOUTUBE_TOOLS + RAG_TOOLS


class ChatAgent(BaseAgent):
    """Agent for chat-based Q&A about stocks with integrated tools."""

    def __init__(self, **kwargs):
        super().__init__(temperature=0.7, **kwargs)

    async def chat(
        self,
        message: str,
        history: list[dict[str, str]] | None = None,
        context: dict | None = None,
        use_intent_analyzer: bool = True,
    ) -> dict[str, Any]:
        """Process a chat message and return a response.

        Args:
            message: User's message
            history: Conversation history
            context: Optional context (e.g., current stock being viewed)
            use_intent_analyzer: Whether to pre-analyze intent and enrich context

        Returns:
            Response with text and optional sources.
        """
        if history is None:
            history = []

        messages = [{"role": "system", "content": SYSTEM_PROMPT}]

        # Add context if provided
        if context:
            context_msg = f"Context: User is currently viewing {context.get('symbol', 'unknown')} ({context.get('market', 'US')} market)"
            messages.append({"role": "system", "content": context_msg})

        # Pre-analyze intent and enrich context
        enriched_sources: list[dict[str, Any]] = []
        if use_intent_analyzer:
            enriched_context, enriched_sources = await self._analyze_and_enrich_context(
                message, context
            )
            if enriched_context:
                messages.append({"role": "system", "content": enriched_context})

        # Add history
        messages.extend(history)

        # Add current message
        messages.append({"role": "user", "content": message})

        # Call LLM with tools using unified interface
        response = await self.call_llm_with_response(
            messages=messages,
            tools=ALL_TOOLS,
        )

        sources = enriched_sources.copy() if enriched_sources else []

        # Handle tool calls using unified ToolCall format
        if response.tool_calls:
            # Execute tool calls
            tool_results = await self._execute_tools(response.tool_calls)
            sources = tool_results.get("sources", [])

            # Add assistant message with tool calls to context
            messages.append({
                "role": "assistant",
                "content": response.content or "",
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.name,
                            "arguments": json.dumps(tc.arguments),
                        },
                    }
                    for tc in response.tool_calls
                ],
            })

            # Add tool results
            for tool_call in response.tool_calls:
                result_data = tool_results.get(tool_call.name, {})
                # Truncate large results
                result_str = json.dumps(result_data, ensure_ascii=False, default=str)
                if len(result_str) > 10000:
                    result_str = result_str[:10000] + "... (truncated)"

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result_str,
                })

            # Get final response
            final_response = await self.call_llm_with_response(messages=messages)
            response_text = final_response.content
        else:
            response_text = response.content

        return {
            "response": response_text,
            "sources": sources,
        }

    async def stream_chat(
        self,
        message: str,
        history: list[dict[str, str]] | None = None,
        context: dict | None = None,
    ) -> AsyncIterator[str]:
        """Stream a chat response.

        Note: Streaming doesn't support tool calls. For tool-using queries,
        use the regular chat method.

        Args:
            message: User's message
            history: Conversation history
            context: Optional context

        Yields:
            Response text chunks.
        """
        if history is None:
            history = []

        messages = [{"role": "system", "content": SYSTEM_PROMPT}]

        if context:
            context_msg = f"Context: User is currently viewing {context.get('symbol', 'unknown')} ({context.get('market', 'US')} market)"
            messages.append({"role": "system", "content": context_msg})

        messages.extend(history)
        messages.append({"role": "user", "content": message})

        async for chunk in self.stream_llm(messages):
            yield chunk

    async def _execute_tools(self, tool_calls: list[ToolCall]) -> dict[str, Any]:
        """Execute tool calls using ToolRouter with retry and timeout.

        Args:
            tool_calls: List of unified ToolCall objects.

        Returns:
            Dict with tool results and sources.
        """
        from src.services.tool_router import get_tool_router, ToolResult

        results: dict[str, Any] = {"sources": [], "_tool_results": []}
        router = get_tool_router()

        # Map function names to tool types
        TOOL_TYPE_MAP = {
            "get_stock_price": "stock_price",
            "get_stock_info": "stock_info",
            "get_financial_ratios": "financial_ratios",
            "search_news": "news_search",
            "web_search": "web_search",
            "search_finance_news": "finance_news",
            "get_youtube_transcript": "youtube_transcript",
            "get_channel_recent_videos": "youtube_channel",
            "search_knowledge_base": "rag_search",
        }

        for tool_call in tool_calls:
            func_name = tool_call.name
            args = tool_call.arguments

            # Get mapped tool type
            tool_type = TOOL_TYPE_MAP.get(func_name)

            if tool_type:
                # Prepare arguments for ToolRouter
                router_args = self._prepare_router_args(func_name, args)

                # Execute via ToolRouter (with retry and timeout)
                tool_result: ToolResult = await router.execute(tool_type, **router_args)

                # Store result
                if tool_result.is_success and tool_result.has_data:
                    results[func_name] = tool_result.data
                else:
                    results[func_name] = {
                        "error": tool_result.error or "No data available",
                        "status": tool_result.status.value,
                        "retries": tool_result.retries,
                    }

                # Store tool result for context building
                results["_tool_results"].append(tool_result)

                # Add source
                results["sources"].append({
                    "type": tool_type,
                    "status": tool_result.status.value,
                    "retries": tool_result.retries,
                    **router_args,
                })

            # Handle tools not in ToolRouter (YouTube RAG, etc.)
            elif func_name == "get_channel_transcripts_to_rag":
                try:
                    from src.tools.youtube_tool import get_channel_videos_and_store_to_rag

                    data = await get_channel_videos_and_store_to_rag(
                        channel_identifier=args["channel"],
                        kb_name=args.get("kb_name", "youtube"),
                        max_videos=args.get("max_videos", 3),
                    )
                    results[func_name] = data
                    results["sources"].append({
                        "type": "youtube_channel_to_rag",
                        "channel": args["channel"],
                    })
                except Exception as e:
                    results[func_name] = {"error": str(e)}

            elif func_name == "list_knowledge_bases":
                try:
                    from src.tools.rag_tool import list_knowledge_bases as list_kbs
                    data = await list_kbs()
                    results[func_name] = data
                except Exception as e:
                    results[func_name] = {"error": str(e)}

            else:
                results[func_name] = {"error": f"Unknown tool: {func_name}"}

        return results

    def _prepare_router_args(self, func_name: str, args: dict[str, Any]) -> dict[str, Any]:
        """Prepare arguments for ToolRouter based on function name.

        Args:
            func_name: Original function name from LLM.
            args: Arguments from LLM tool call.

        Returns:
            Arguments formatted for ToolRouter.
        """
        if func_name == "get_stock_price":
            return {
                "symbol": args["symbol"],
                "market": args.get("market", "US"),
                "period": args.get("period", "1mo"),
                "interval": "1d",
            }
        elif func_name == "get_stock_info":
            return {
                "symbol": args["symbol"],
                "market": args.get("market", "US"),
            }
        elif func_name == "get_financial_ratios":
            return {
                "symbol": args["symbol"],
                "market": args.get("market", "US"),
            }
        elif func_name == "search_news":
            return {
                "query": args.get("query", args.get("symbol", "")),
                "market": args.get("market", "US"),
                "limit": args.get("limit", 10),
            }
        elif func_name == "web_search":
            # Handle comma-separated providers string
            providers_str = args.get("providers", "")
            providers = [p.strip() for p in providers_str.split(",")] if providers_str else None
            return {
                "query": args["query"],
                "providers": providers,
                "max_results": args.get("max_results", 5),
                "topic": args.get("topic", "general"),
            }
        elif func_name == "search_finance_news":
            return {
                "query": args["query"],
                "max_results": args.get("max_results", 10),
            }
        elif func_name == "get_youtube_transcript":
            return {
                "video_url": args["video_url"],
            }
        elif func_name == "get_channel_recent_videos":
            return {
                "channel": args["channel"],
                "max_results": args.get("max_results", 5),
            }
        elif func_name == "search_knowledge_base":
            return {
                "query": args["query"],
                "kb_name": args.get("kb_name", "default"),
                "top_k": args.get("top_k", 5),
            }
        else:
            return args

    async def _analyze_and_enrich_context(
        self,
        message: str,
        context: dict | None = None,
    ) -> tuple[str, list[dict[str, Any]]]:
        """Analyze query intent and pre-fetch relevant data.

        Uses ContextEnricher service to detect intent, extract symbols,
        and pre-fetch relevant data via ToolRouter in parallel.

        Args:
            message: User's message.
            context: Optional existing context.

        Returns:
            Tuple of (enriched_context_string, sources).
        """
        from src.services.context_enricher import get_context_enricher

        enricher = get_context_enricher()
        enriched = await enricher.enrich(message, context)

        return enriched.context_string, enriched.sources

    async def process(self, *args, **kwargs) -> dict[str, Any]:
        """Process method implementation."""
        return await self.chat(*args, **kwargs)
