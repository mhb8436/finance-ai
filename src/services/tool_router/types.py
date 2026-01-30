"""Tool Router Types."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class ToolStatus(str, Enum):
    """Tool execution status."""
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    RETRIED = "retried"


class ToolType(str, Enum):
    """Available tool types."""
    STOCK_PRICE = "stock_price"
    STOCK_INFO = "stock_info"
    FINANCIAL_RATIOS = "financial_ratios"
    FINANCIAL_STATEMENTS = "financial_statements"
    TECHNICAL_INDICATORS = "technical_indicators"
    NEWS_SEARCH = "news_search"
    WEB_SEARCH = "web_search"
    FINANCE_NEWS = "finance_news"
    RAG_SEARCH = "rag_search"
    YOUTUBE_TRANSCRIPT = "youtube_transcript"
    YOUTUBE_CHANNEL = "youtube_channel"


@dataclass
class ToolConfig:
    """Configuration for tool execution."""
    timeout: float = 30.0  # seconds
    max_retries: int = 2
    retry_delay: float = 1.0  # seconds between retries
    max_result_size: int = 50000  # bytes, truncate if larger


@dataclass
class ToolResult:
    """Unified tool execution result."""
    tool_type: str
    query: dict[str, Any]  # Original query parameters
    status: ToolStatus
    data: dict[str, Any] | None = None
    error: str | None = None
    retries: int = 0
    execution_time: float = 0.0  # seconds
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    @property
    def is_success(self) -> bool:
        """Check if tool execution was successful."""
        return self.status == ToolStatus.SUCCESS

    @property
    def has_data(self) -> bool:
        """Check if result has data."""
        return self.data is not None and bool(self.data)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "tool_type": self.tool_type,
            "query": self.query,
            "status": self.status.value,
            "data": self.data,
            "error": self.error,
            "retries": self.retries,
            "execution_time": self.execution_time,
            "timestamp": self.timestamp,
        }

    def to_context_string(self, max_length: int = 5000) -> str:
        """Convert to string for LLM context.

        Args:
            max_length: Maximum length of the string.

        Returns:
            Formatted string for LLM context.
        """
        if not self.is_success or not self.has_data:
            return f"[{self.tool_type}] Error: {self.error or 'No data available'}"

        import json

        # Format based on tool type
        if self.tool_type == ToolType.STOCK_PRICE.value:
            return self._format_stock_price()
        elif self.tool_type == ToolType.STOCK_INFO.value:
            return self._format_stock_info()
        elif self.tool_type == ToolType.FINANCIAL_RATIOS.value:
            return self._format_financial_ratios()
        elif self.tool_type == ToolType.FINANCIAL_STATEMENTS.value:
            return self._format_financial_statements()
        elif self.tool_type == ToolType.NEWS_SEARCH.value:
            return self._format_news()
        elif self.tool_type == ToolType.WEB_SEARCH.value:
            return self._format_web_search()
        else:
            # Generic JSON format
            result = json.dumps(self.data, ensure_ascii=False, indent=2)
            if len(result) > max_length:
                result = result[:max_length] + "\n... (truncated)"
            return f"[{self.tool_type}]\n{result}"

    def _format_stock_price(self) -> str:
        """Format stock price data."""
        data = self.data or {}
        prices = data.get("prices", data)

        if isinstance(prices, list) and prices:
            # Get latest price
            latest = prices[-1] if prices else {}
            lines = [
                f"[Stock Price: {self.query.get('symbol', 'N/A')}]",
                f"Date: {latest.get('date', 'N/A')}",
                f"Close: {latest.get('close', 'N/A')}",
                f"Open: {latest.get('open', 'N/A')}",
                f"High: {latest.get('high', 'N/A')}",
                f"Low: {latest.get('low', 'N/A')}",
                f"Volume: {latest.get('volume', 'N/A'):,}" if isinstance(latest.get('volume'), (int, float)) else f"Volume: {latest.get('volume', 'N/A')}",
            ]

            # Add price history summary
            if len(prices) > 1:
                first = prices[0]
                change = ((latest.get('close', 0) - first.get('close', 1)) / first.get('close', 1) * 100)
                lines.append(f"Period Change: {change:.2f}%")
                lines.append(f"Data Points: {len(prices)}")

            return "\n".join(lines)

        return f"[Stock Price] No data available for {self.query.get('symbol', 'N/A')}"

    def _format_stock_info(self) -> str:
        """Format stock info data."""
        data = self.data or {}

        lines = [
            f"[Stock Info: {data.get('symbol', 'N/A')}]",
            f"Name: {data.get('name', 'N/A')}",
            f"Market: {data.get('market', 'N/A')}",
        ]

        if data.get('sector'):
            lines.append(f"Sector: {data['sector']}")
        if data.get('industry'):
            lines.append(f"Industry: {data['industry']}")
        if data.get('market_cap'):
            cap = data['market_cap']
            if cap >= 1e12:
                lines.append(f"Market Cap: ${cap/1e12:.2f}T")
            elif cap >= 1e9:
                lines.append(f"Market Cap: ${cap/1e9:.2f}B")
            else:
                lines.append(f"Market Cap: ${cap/1e6:.2f}M")
        if data.get('pe_ratio'):
            lines.append(f"P/E Ratio: {data['pe_ratio']:.2f}")
        if data.get('pb_ratio'):
            lines.append(f"P/B Ratio: {data['pb_ratio']:.2f}")
        if data.get('dividend_yield'):
            lines.append(f"Dividend Yield: {data['dividend_yield']*100:.2f}%")
        if data.get('52_week_high'):
            lines.append(f"52 Week High: ${data['52_week_high']:.2f}")
        if data.get('52_week_low'):
            lines.append(f"52 Week Low: ${data['52_week_low']:.2f}")
        if data.get('description'):
            desc = data['description']
            if len(desc) > 300:
                desc = desc[:300] + "..."
            lines.append(f"Description: {desc}")

        return "\n".join(lines)

    def _format_financial_ratios(self) -> str:
        """Format financial ratios data."""
        data = self.data or {}

        lines = [f"[Financial Ratios: {self.query.get('symbol', 'N/A')}]"]

        for key, value in data.items():
            if value is not None:
                if isinstance(value, float):
                    lines.append(f"{key}: {value:.2f}")
                else:
                    lines.append(f"{key}: {value}")

        return "\n".join(lines)

    def _format_financial_statements(self) -> str:
        """Format financial statements data (from OpenDART or yfinance)."""
        data = self.data or {}

        lines = [f"[Financial Statements: {self.query.get('symbol', 'N/A')}]"]

        if data.get("source"):
            lines.append(f"Source: {data['source']}")
        if data.get("year"):
            lines.append(f"Year: {data['year']}")

        # Income Statement
        income = data.get("income_statement", {})
        if income:
            lines.append("\n[Income Statement]")
            for key, value in income.items():
                if value is not None:
                    if isinstance(value, (int, float)) and abs(value) > 1000000:
                        lines.append(f"  {key}: {value:,.0f}")
                    elif isinstance(value, float):
                        lines.append(f"  {key}: {value:.2%}")
                    else:
                        lines.append(f"  {key}: {value}")

        # Balance Sheet
        balance = data.get("balance_sheet", {})
        if balance:
            lines.append("\n[Balance Sheet]")
            for key, value in balance.items():
                if value is not None:
                    if isinstance(value, (int, float)) and abs(value) > 1000000:
                        lines.append(f"  {key}: {value:,.0f}")
                    elif isinstance(value, float):
                        lines.append(f"  {key}: {value:.2f}")
                    else:
                        lines.append(f"  {key}: {value}")

        # Cash Flow
        cashflow = data.get("cash_flow", {})
        if cashflow:
            lines.append("\n[Cash Flow]")
            for key, value in cashflow.items():
                if value is not None:
                    if isinstance(value, (int, float)) and abs(value) > 1000000:
                        lines.append(f"  {key}: {value:,.0f}")
                    else:
                        lines.append(f"  {key}: {value}")

        return "\n".join(lines)

    def _format_news(self) -> str:
        """Format news search results."""
        data = self.data or {}
        articles = data.get("articles", data.get("results", []))

        if not articles:
            return f"[News Search] No results for '{self.query.get('query', 'N/A')}'"

        lines = [f"[News Search: '{self.query.get('query', 'N/A')}']"]

        for i, article in enumerate(articles[:5], 1):
            title = article.get("title", "No title")
            source = article.get("source", "Unknown")
            date = article.get("date", article.get("published", ""))
            summary = article.get("summary", article.get("snippet", ""))

            lines.append(f"\n{i}. {title}")
            lines.append(f"   Source: {source} | Date: {date}")
            if summary:
                if len(summary) > 150:
                    summary = summary[:150] + "..."
                lines.append(f"   {summary}")

        return "\n".join(lines)

    def _format_web_search(self) -> str:
        """Format web search results."""
        data = self.data or {}
        results = data.get("results", [])

        if not results:
            return f"[Web Search] No results for '{self.query.get('query', 'N/A')}'"

        lines = [f"[Web Search: '{self.query.get('query', 'N/A')}']"]

        for i, result in enumerate(results[:5], 1):
            title = result.get("title", "No title")
            url = result.get("url", "")
            snippet = result.get("snippet", "")
            source = result.get("source", "")

            lines.append(f"\n{i}. {title}")
            if source:
                lines.append(f"   Source: {source}")
            if snippet:
                if len(snippet) > 150:
                    snippet = snippet[:150] + "..."
                lines.append(f"   {snippet}")

        return "\n".join(lines)


@dataclass
class ToolTrace:
    """Trace of tool execution for reporting."""
    tool_id: str
    tool_type: str
    query: dict[str, Any]
    raw_result: ToolResult
    summary: str | None = None
    citation_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "tool_id": self.tool_id,
            "tool_type": self.tool_type,
            "query": self.query,
            "raw_result": self.raw_result.to_dict(),
            "summary": self.summary,
            "citation_id": self.citation_id,
        }
