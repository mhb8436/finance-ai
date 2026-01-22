"""Fundamental Analysis Agent for stock analysis."""

from typing import Any

from src.agents.base_agent import BaseAgent
from src.tools.stock_data import get_stock_info
from src.tools.financials import get_financial_statements, get_financial_ratios


SYSTEM_PROMPT = """You are a professional fundamental analyst specializing in company valuation and financial analysis.
Your role is to analyze company financials and provide investment insights.

When analyzing, consider:
1. Valuation metrics (P/E, P/B, P/S, EV/EBITDA)
2. Profitability (ROE, ROA, profit margins)
3. Financial health (debt ratios, current ratio, quick ratio)
4. Growth metrics (revenue growth, earnings growth)
5. Dividend analysis (yield, payout ratio)
6. Competitive position and moat

Provide clear, actionable insights based on the data. Always explain your reasoning.
Compare with industry averages when possible.
Use Korean if the user's query is in Korean, otherwise use English."""


class FundamentalAnalysisAgent(BaseAgent):
    """Agent for fundamental analysis of stocks."""

    def __init__(self, **kwargs):
        super().__init__(temperature=0.3, **kwargs)

    async def analyze(
        self,
        symbol: str,
        market: str = "US",
        include_financials: bool = True,
        include_ratios: bool = True,
    ) -> dict[str, Any]:
        """Perform fundamental analysis on a stock.

        Args:
            symbol: Stock symbol
            market: Market code ('US' or 'KR')
            include_financials: Include financial statements
            include_ratios: Include financial ratios

        Returns:
            Analysis results with data and summary.
        """
        # Fetch stock info
        stock_info = await get_stock_info(symbol, market)

        data = {
            "info": stock_info,
        }

        # Fetch financial statements if requested
        if include_financials:
            financials = await get_financial_statements(symbol, market)
            data["financials"] = financials

        # Fetch financial ratios if requested
        if include_ratios:
            ratios = await get_financial_ratios(symbol, market)
            data["ratios"] = ratios

        # Prepare analysis prompt
        analysis_prompt = f"""
Analyze the following company data for {symbol} ({market} market):

Company Information:
- Name: {stock_info.get('name', 'N/A')}
- Sector: {stock_info.get('sector', 'N/A')}
- Industry: {stock_info.get('industry', 'N/A')}
- Market Cap: {self._format_number(stock_info.get('market_cap'))}

Valuation Metrics:
- P/E Ratio: {stock_info.get('pe_ratio', 'N/A')}
- P/B Ratio: {stock_info.get('pb_ratio', 'N/A')}
- Dividend Yield: {self._format_percent(stock_info.get('dividend_yield'))}

{self._format_financials(data.get('financials', {}))}

{self._format_ratios(data.get('ratios', {}))}

Provide a comprehensive fundamental analysis summary including:
1. Valuation assessment (undervalued, fairly valued, overvalued)
2. Financial health evaluation
3. Profitability analysis
4. Growth outlook
5. Key risks and concerns
6. Investment thesis
"""

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": analysis_prompt},
        ]

        summary = await self.call_llm(messages)

        return {
            "data": data,
            "summary": summary,
        }

    async def process(self, *args, **kwargs) -> dict[str, Any]:
        """Process method implementation."""
        return await self.analyze(*args, **kwargs)

    def _format_number(self, value: float | None) -> str:
        """Format large numbers with suffixes."""
        if value is None:
            return "N/A"

        if value >= 1_000_000_000_000:
            return f"${value / 1_000_000_000_000:.2f}T"
        if value >= 1_000_000_000:
            return f"${value / 1_000_000_000:.2f}B"
        if value >= 1_000_000:
            return f"${value / 1_000_000:.2f}M"
        return f"${value:,.0f}"

    def _format_percent(self, value: float | None) -> str:
        """Format percentage values."""
        if value is None:
            return "N/A"
        return f"{value * 100:.2f}%"

    def _format_financials(self, financials: dict) -> str:
        """Format financial statements for the prompt."""
        if not financials:
            return "Financial Statements: Not available"

        lines = ["Financial Statements (Latest):"]

        if "income_statement" in financials:
            income = financials["income_statement"]
            lines.append(f"- Revenue: {self._format_number(income.get('revenue'))}")
            lines.append(f"- Net Income: {self._format_number(income.get('net_income'))}")
            lines.append(f"- Gross Margin: {self._format_percent(income.get('gross_margin'))}")

        if "balance_sheet" in financials:
            balance = financials["balance_sheet"]
            lines.append(f"- Total Assets: {self._format_number(balance.get('total_assets'))}")
            lines.append(f"- Total Debt: {self._format_number(balance.get('total_debt'))}")
            lines.append(f"- Cash: {self._format_number(balance.get('cash'))}")

        return "\n".join(lines)

    def _format_ratios(self, ratios: dict) -> str:
        """Format financial ratios for the prompt."""
        if not ratios:
            return "Financial Ratios: Not available"

        lines = ["Financial Ratios:"]

        ratio_names = {
            "roe": "ROE",
            "roa": "ROA",
            "current_ratio": "Current Ratio",
            "debt_to_equity": "Debt/Equity",
            "profit_margin": "Profit Margin",
        }

        for key, name in ratio_names.items():
            value = ratios.get(key)
            if value is not None:
                if "ratio" in key.lower() or "equity" in key.lower():
                    lines.append(f"- {name}: {value:.2f}")
                else:
                    lines.append(f"- {name}: {self._format_percent(value)}")

        return "\n".join(lines)
