"""Research Agent for executing research tasks with tools.

Executes research on specific topics using available tools
(RAG, web search, stock data, financials, etc.) and records findings.

Uses ToolRouter for unified tool execution with retry and timeout.
"""

import json
import logging
from datetime import datetime
from typing import Any, Callable, Awaitable

from src.agents.base_agent import BaseAgent
from src.services.tool_router import get_tool_router, ToolResult
from ..data_structures import TopicBlock, ToolTrace, ToolType

logger = logging.getLogger(__name__)


# Mapping from research tool names to ToolRouter tool types
TOOL_NAME_TO_ROUTER_TYPE: dict[str, str] = {
    "rag_search": "rag_search",
    "web_search": "web_search",
    "stock_data": "stock_price",
    "stock_info": "stock_info",
    "financials": "financial_ratios",
    "financial_ratios": "financial_ratios",
    "news_search": "news_search",
    "youtube": "youtube_transcript",
    "youtube_transcript": "youtube_transcript",
    "youtube_channel": "youtube_channel",
    "technical_analysis": "technical_indicators",
    "technical_indicators": "technical_indicators",
}

RESEARCH_SYSTEM_PROMPT = """You are a financial research analyst executing systematic research.

Your task is to research a specific topic using the available tools. For each research step:
1. Decide which tool to use and why
2. Formulate an effective query
3. Analyze the results
4. Determine if more research is needed

Available Tools:
{tools_description}

When using tools, think about:
- What information do we need?
- Which tool is most likely to provide it?
- How should we query to get relevant results?

Output your response as JSON:
{{
    "reasoning": "Why this approach",
    "tool_call": {{
        "tool": "tool_name",
        "query": "Your query or parameters"
    }} | null,
    "analysis": "Analysis of results (if tool was called)",
    "key_findings": ["Finding 1", "Finding 2"],
    "sufficient": true/false,
    "next_step": "What to do next if not sufficient"
}}"""

RESEARCH_USER_TEMPLATE = """Research Topic: {topic}
Overview: {overview}

{context}

{previous_findings}

Execute research using available tools. Call tools to gather information, then analyze results."""


class ResearchAgent(BaseAgent):
    """Agent for executing research tasks with tools.

    Performs actual research by calling tools (RAG, web search,
    stock data, etc.) and recording findings with citations.
    """

    # Default tool descriptions
    DEFAULT_TOOLS_DESCRIPTION = """
- rag_search: Search uploaded documents and knowledge base
- web_search: Search the web for recent information
- stock_data: Get stock price data and basic info
- financials: Get financial statements and ratios
- news_search: Search recent news articles
- youtube: Search YouTube for relevant analysis videos
- technical_analysis: Get technical indicators and patterns
- fundamental_analysis: Get fundamental analysis data
"""

    def __init__(
        self,
        model: str | None = None,
        temperature: float = 0.4,
        max_tokens: int = 8000,
        tool_handlers: dict[str, Callable[..., Awaitable[Any]]] | None = None,
        use_tool_router: bool = True,
    ):
        """Initialize the ResearchAgent.

        Args:
            model: LLM model to use.
            temperature: Temperature for generation.
            max_tokens: Max tokens for response (increased for reasoning models like gpt-5).
            tool_handlers: Dictionary mapping tool names to handler functions.
                          Only used if use_tool_router is False.
            use_tool_router: If True, use ToolRouter for unified tool execution.
        """
        super().__init__(model=model, temperature=temperature, max_tokens=max_tokens)
        self._tool_handlers = tool_handlers or {}
        self._tools_description = self.DEFAULT_TOOLS_DESCRIPTION
        self._citation_counter = 0
        self._use_tool_router = use_tool_router
        self._tool_router = get_tool_router() if use_tool_router else None

    def register_tool(
        self,
        tool_name: str,
        handler: Callable[..., Awaitable[Any]],
        description: str | None = None,
    ) -> None:
        """Register a tool handler.

        Args:
            tool_name: Name of the tool.
            handler: Async function to handle tool calls.
            description: Optional description for the tool.
        """
        self._tool_handlers[tool_name] = handler
        if description:
            self._tools_description += f"\n- {tool_name}: {description}"

    def set_tools_description(self, description: str) -> None:
        """Set the tools description for the prompt.

        Args:
            description: Description of available tools.
        """
        self._tools_description = description

    async def process(
        self,
        topic_block: TopicBlock,
        context: str = "",
        max_iterations: int = 5,
        symbols: list[str] | None = None,
    ) -> dict[str, Any]:
        """Execute research on a topic block.

        Args:
            topic_block: The topic block to research.
            context: Additional context for research.
            max_iterations: Maximum tool call iterations.
            symbols: Optional stock symbols for context.

        Returns:
            Dictionary with research results.
        """
        findings: list[str] = []
        tool_traces: list[ToolTrace] = []
        iteration = 0

        # Build symbols context
        symbols_context = ""
        if symbols:
            symbols_context = f"Target Symbols: {', '.join(symbols)}"

        while iteration < max_iterations:
            iteration += 1
            topic_block.iteration_count = iteration

            # Build previous findings summary
            previous_findings = ""
            if findings:
                previous_findings = "Previous Findings:\n" + "\n".join(f"- {f}" for f in findings[-5:])

            messages = [
                {
                    "role": "system",
                    "content": RESEARCH_SYSTEM_PROMPT.format(
                        tools_description=self._tools_description
                    ),
                },
                {
                    "role": "user",
                    "content": RESEARCH_USER_TEMPLATE.format(
                        topic=topic_block.sub_topic,
                        overview=topic_block.overview,
                        context=f"{context}\n{symbols_context}".strip(),
                        previous_findings=previous_findings,
                    ),
                },
            ]

            try:
                response = await self.call_llm(messages)
                result = self._parse_response(response)

                # Check if research is sufficient
                if result.get("sufficient", False):
                    logger.info(f"Research sufficient for: {topic_block.sub_topic}")
                    break

                # Execute tool call if specified
                tool_call = result.get("tool_call")
                if tool_call and tool_call.get("tool"):
                    tool_name = tool_call["tool"]
                    query = tool_call.get("query", "")

                    # Execute tool (returns tuple: result_string, ToolResult)
                    tool_result_str, router_result = await self._execute_tool(
                        tool_name, query, symbols
                    )

                    # Create tool trace with execution metadata
                    trace = self._create_tool_trace(
                        topic_block.block_id,
                        tool_name,
                        query,
                        tool_result_str,
                        result.get("analysis", ""),
                        router_result=router_result,
                    )
                    tool_traces.append(trace)
                    topic_block.add_tool_trace(trace)

                    # Add findings
                    key_findings = result.get("key_findings", [])
                    findings.extend(key_findings)

                else:
                    # No tool call, check if we should continue
                    if not result.get("next_step"):
                        break

            except Exception as e:
                logger.error(f"Error in research iteration {iteration}: {e}")
                findings.append(f"Error occurred: {str(e)}")
                break

        return {
            "topic": topic_block.sub_topic,
            "iterations": iteration,
            "findings": findings,
            "tool_traces": [t.to_dict() for t in tool_traces],
            "summary": self._summarize_findings(findings),
        }

    async def _execute_tool(
        self,
        tool_name: str,
        query: str,
        symbols: list[str] | None = None,
    ) -> tuple[str, ToolResult | None]:
        """Execute a tool call using ToolRouter or legacy handlers.

        Args:
            tool_name: Name of the tool to call.
            query: Query or parameters for the tool.
            symbols: Optional symbols for context.

        Returns:
            Tuple of (result_string, ToolResult or None).
        """
        # Use ToolRouter if enabled
        if self._use_tool_router and self._tool_router:
            return await self._execute_tool_via_router(tool_name, query, symbols)

        # Fallback to legacy handler execution
        return await self._execute_tool_legacy(tool_name, query, symbols)

    async def _execute_tool_via_router(
        self,
        tool_name: str,
        query: str,
        symbols: list[str] | None = None,
    ) -> tuple[str, ToolResult | None]:
        """Execute tool via ToolRouter with retry and timeout.

        Args:
            tool_name: Name of the tool to call.
            query: Query or parameters for the tool.
            symbols: Optional symbols for context.

        Returns:
            Tuple of (result_string, ToolResult).
        """
        # Map tool name to router type
        router_type = TOOL_NAME_TO_ROUTER_TYPE.get(tool_name)
        if not router_type:
            logger.warning(f"Tool not mapped to router: {tool_name}")
            return f"Tool '{tool_name}' is not available in ToolRouter.", None

        # Build arguments based on tool type
        kwargs = self._build_router_args(router_type, query, symbols)

        try:
            # Execute via ToolRouter (includes retry and timeout)
            result: ToolResult = await self._tool_router.execute(router_type, **kwargs)

            if result.is_success and result.has_data:
                # Use formatted context string for LLM
                result_str = result.to_context_string()
                logger.info(
                    f"Tool {tool_name} executed via router "
                    f"(status={result.status.value}, retries={result.retries}, "
                    f"time={result.execution_time:.2f}s)"
                )
                return result_str, result
            else:
                error_msg = f"Tool {tool_name} failed: {result.error or 'No data'}"
                logger.warning(error_msg)
                return error_msg, result

        except Exception as e:
            logger.error(f"Error executing tool {tool_name} via router: {e}")
            return f"Error executing {tool_name}: {str(e)}", None

    def _build_router_args(
        self,
        router_type: str,
        query: str,
        symbols: list[str] | None = None,
    ) -> dict[str, Any]:
        """Build arguments for ToolRouter based on tool type.

        Args:
            router_type: ToolRouter tool type.
            query: Query string from LLM.
            symbols: Optional stock symbols.

        Returns:
            Dictionary of arguments for router.execute().
        """
        # Default symbol (first one if provided)
        symbol = symbols[0] if symbols else None

        # Detect market from symbol
        market = "KR" if symbol and symbol.isdigit() and len(symbol) == 6 else "US"

        if router_type == "stock_price":
            return {
                "symbol": symbol or query,
                "market": market,
                "period": "1mo",
                "interval": "1d",
            }
        elif router_type == "stock_info":
            return {
                "symbol": symbol or query,
                "market": market,
            }
        elif router_type == "financial_ratios":
            return {
                "symbol": symbol or query,
                "market": market,
            }
        elif router_type == "technical_indicators":
            return {
                "symbol": symbol or query,
                "market": market,
                "period": "3mo",
            }
        elif router_type == "news_search":
            return {
                "query": query,
                "market": market,
                "limit": 10,
            }
        elif router_type == "web_search":
            return {
                "query": query,
                "max_results": 10,
            }
        elif router_type == "rag_search":
            return {
                "query": query,
                "kb_name": "default",
                "top_k": 5,
            }
        elif router_type == "youtube_transcript":
            return {
                "video_url": query,
            }
        elif router_type == "youtube_channel":
            return {
                "channel": query,
                "max_results": 5,
            }
        else:
            # Fallback: pass query as-is
            return {"query": query}

    async def _execute_tool_legacy(
        self,
        tool_name: str,
        query: str,
        symbols: list[str] | None = None,
    ) -> tuple[str, None]:
        """Execute tool via legacy handler (backward compatibility).

        Args:
            tool_name: Name of the tool to call.
            query: Query or parameters for the tool.
            symbols: Optional symbols for context.

        Returns:
            Tuple of (result_string, None).
        """
        if tool_name not in self._tool_handlers:
            logger.warning(f"Tool not available: {tool_name}")
            return f"Tool '{tool_name}' is not available.", None

        try:
            handler = self._tool_handlers[tool_name]
            result = await handler(query=query, symbols=symbols)

            # Convert result to string if needed
            if isinstance(result, dict):
                return json.dumps(result, ensure_ascii=False, indent=2), None
            return str(result), None

        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}")
            return f"Error executing {tool_name}: {str(e)}", None

    def _create_tool_trace(
        self,
        block_id: str,
        tool_name: str,
        query: str,
        raw_answer: str,
        summary: str,
        router_result: ToolResult | None = None,
    ) -> ToolTrace:
        """Create a tool trace record.

        Args:
            block_id: Parent block ID.
            tool_name: Name of the tool used.
            query: Query that was executed.
            raw_answer: Raw result from the tool.
            summary: Summary of the result.
            router_result: Optional ToolResult from ToolRouter (for metadata).

        Returns:
            ToolTrace object.
        """
        self._citation_counter += 1
        block_num = block_id.replace("block_", "")

        # Build metadata
        metadata: dict[str, Any] = {"block_id": block_id}

        # Add ToolRouter execution info if available
        if router_result:
            metadata["router"] = {
                "status": router_result.status.value,
                "retries": router_result.retries,
                "execution_time": router_result.execution_time,
            }

        return ToolTrace(
            tool_id=f"tool_{block_num}_{self._citation_counter}",
            citation_id=f"CIT-{block_num}-{self._citation_counter:02d}",
            tool_type=tool_name,
            query=query,
            raw_answer=raw_answer,
            summary=summary,
            timestamp=datetime.utcnow().isoformat(),
            metadata=metadata,
        )

    def _parse_response(self, response: str) -> dict[str, Any]:
        """Parse the LLM response.

        Args:
            response: Raw LLM response.

        Returns:
            Parsed dictionary.
        """
        try:
            if "```json" in response:
                start = response.find("```json") + 7
                end = response.find("```", start)
                json_str = response[start:end].strip()
            elif "```" in response:
                start = response.find("```") + 3
                end = response.find("```", start)
                json_str = response[start:end].strip()
            else:
                start = response.find("{")
                end = response.rfind("}") + 1
                if start >= 0 and end > start:
                    json_str = response[start:end]
                else:
                    json_str = response

            result = json.loads(json_str)
            # Ensure we return a dict, not a list
            if isinstance(result, dict):
                return result
            elif isinstance(result, list) and len(result) > 0 and isinstance(result[0], dict):
                return result[0]
            else:
                logger.warning(f"Unexpected JSON type: {type(result)}")
                return {
                    "reasoning": str(result),
                    "tool_call": None,
                    "key_findings": [],
                    "sufficient": True,
                }
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse research response: {response[:100]}...")
            return {
                "reasoning": response.strip(),
                "tool_call": None,
                "key_findings": [],
                "sufficient": True,
            }

    def _summarize_findings(self, findings: list[str]) -> str:
        """Create a summary of findings.

        Args:
            findings: List of finding strings.

        Returns:
            Summary text.
        """
        if not findings:
            return "No findings gathered."

        # Simple deduplication and formatting
        unique_findings = list(dict.fromkeys(findings))
        return "\n".join(f"- {f}" for f in unique_findings[:10])

    def reset_citation_counter(self) -> None:
        """Reset the citation counter for a new research session."""
        self._citation_counter = 0
