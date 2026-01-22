"""Research Agent for generating comprehensive stock/industry reports."""

from datetime import datetime
from pathlib import Path
from typing import Any

from src.agents.base_agent import BaseAgent
from src.core.config import get_project_root
from src.tools.stock_data import get_stock_info, get_stock_price
from src.tools.financials import get_financial_statements
from src.tools.news_search import search_news


SYSTEM_PROMPT = """You are a professional equity research analyst.
Your role is to create comprehensive research reports on stocks and industries.

Your reports should include:
1. Executive Summary
2. Company/Industry Overview
3. Financial Analysis
4. Competitive Position
5. Growth Drivers and Risks
6. Valuation Analysis
7. Investment Recommendation

Write in a professional, objective tone. Support claims with data.
Use Korean if the topic is about Korean stocks, otherwise use English."""


class ResearchAgent(BaseAgent):
    """Agent for generating research reports."""

    def __init__(self, **kwargs):
        super().__init__(temperature=0.5, max_tokens=8192, **kwargs)

    async def research(
        self,
        topic: str,
        symbols: list[str] | None = None,
        market: str = "US",
        depth: str = "medium",
        research_id: str | None = None,
    ) -> dict[str, Any]:
        """Generate a research report.

        Args:
            topic: Research topic
            symbols: List of stock symbols to analyze
            market: Market code
            depth: Research depth (quick, medium, deep)
            research_id: Optional ID for the research

        Returns:
            Research results with report path.
        """
        if research_id is None:
            research_id = f"research_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        if symbols is None:
            symbols = []

        # Gather data
        data = await self._gather_data(symbols, market, depth)

        # Generate report
        report = await self._generate_report(topic, symbols, market, data, depth)

        # Save report
        report_path = await self._save_report(research_id, topic, report)

        return {
            "research_id": research_id,
            "topic": topic,
            "report": report,
            "report_path": str(report_path),
            "data": data,
        }

    async def _gather_data(
        self,
        symbols: list[str],
        market: str,
        depth: str,
    ) -> dict[str, Any]:
        """Gather data for research."""
        data = {
            "stocks": {},
            "news": [],
        }

        for symbol in symbols:
            stock_data = {}

            # Basic info
            stock_data["info"] = await get_stock_info(symbol, market)

            # Price data
            period = "1y" if depth == "deep" else "6mo" if depth == "medium" else "3mo"
            stock_data["price"] = await get_stock_price(symbol, market, period, "1d")

            # Financials for medium/deep research
            if depth in ["medium", "deep"]:
                stock_data["financials"] = await get_financial_statements(symbol, market)

            data["stocks"][symbol] = stock_data

        # News search
        if symbols:
            news_query = " ".join(symbols[:3])  # Limit query
            data["news"] = await search_news(news_query, market, limit=10)

        return data

    async def _generate_report(
        self,
        topic: str,
        symbols: list[str],
        market: str,
        data: dict[str, Any],
        depth: str,
    ) -> str:
        """Generate the research report."""
        # Build context from data
        context_parts = [f"Research Topic: {topic}\nMarket: {market}\n"]

        for symbol, stock_data in data.get("stocks", {}).items():
            info = stock_data.get("info", {})
            context_parts.append(f"""
## {symbol} - {info.get('name', 'Unknown')}
- Sector: {info.get('sector', 'N/A')}
- Industry: {info.get('industry', 'N/A')}
- Market Cap: {info.get('market_cap', 'N/A')}
- P/E Ratio: {info.get('pe_ratio', 'N/A')}
- P/B Ratio: {info.get('pb_ratio', 'N/A')}
""")

        # Add news context
        if data.get("news"):
            context_parts.append("\n## Recent News:")
            for news in data["news"][:5]:
                context_parts.append(f"- {news.get('title', '')} ({news.get('date', '')})")

        context = "\n".join(context_parts)

        # Generate report
        depth_instruction = {
            "quick": "Write a brief 1-2 page summary report.",
            "medium": "Write a comprehensive 3-5 page research report.",
            "deep": "Write an in-depth 5-10 page research report with detailed analysis.",
        }

        prompt = f"""
Based on the following data, generate a professional research report.

{context}

{depth_instruction.get(depth, depth_instruction['medium'])}

The report should be in Markdown format with proper headings and structure.
Include specific data points and cite sources where applicable.
"""

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]

        return await self.call_llm(messages)

    async def _save_report(
        self,
        research_id: str,
        topic: str,
        report: str,
    ) -> Path:
        """Save the research report to file."""
        reports_dir = get_project_root() / "data" / "user" / "research"
        reports_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{research_id}.md"
        report_path = reports_dir / filename

        # Add header to report
        full_report = f"""# {topic}

*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
*Research ID: {research_id}*

---

{report}
"""

        report_path.write_text(full_report, encoding="utf-8")
        return report_path

    async def process(self, *args, **kwargs) -> dict[str, Any]:
        """Process method implementation."""
        return await self.research(*args, **kwargs)
