"""Technical Analysis Agent for stock analysis."""

from typing import Any

from src.agents.base_agent import BaseAgent
from src.tools.stock_data import get_stock_price
from src.tools.indicators import calculate_indicators


SYSTEM_PROMPT = """You are a professional technical analyst specializing in stock market analysis.
Your role is to analyze stock price data and technical indicators to provide insights.

When analyzing, consider:
1. Trend analysis (uptrend, downtrend, sideways)
2. Support and resistance levels
3. Technical indicator signals (RSI, MACD, Moving Averages, etc.)
4. Volume analysis
5. Pattern recognition

Provide clear, actionable insights based on the data. Always explain your reasoning.
Use Korean if the user's query is in Korean, otherwise use English."""


class TechnicalAnalysisAgent(BaseAgent):
    """Agent for technical analysis of stocks."""

    def __init__(self, **kwargs):
        super().__init__(temperature=0.3, **kwargs)

    async def analyze(
        self,
        symbol: str,
        market: str = "US",
        indicators: list[str] | None = None,
        period: str = "6mo",
    ) -> dict[str, Any]:
        """Perform technical analysis on a stock.

        Args:
            symbol: Stock symbol (e.g., 'AAPL', '005930')
            market: Market code ('US' or 'KR')
            indicators: List of indicators to calculate
            period: Data period

        Returns:
            Analysis results with data and summary.
        """
        if indicators is None:
            indicators = ["sma_20", "sma_50", "ema_12", "ema_26", "rsi_14", "macd"]

        # Fetch price data
        price_data = await get_stock_price(symbol, market, period, "1d")

        if not price_data:
            return {
                "data": {},
                "summary": f"Failed to fetch data for {symbol}",
            }

        # Calculate indicators
        indicator_data = await calculate_indicators(price_data, indicators)

        # Prepare analysis prompt
        latest_data = price_data[-1] if price_data else {}
        latest_indicators = {k: v[-1] if isinstance(v, list) and v else v for k, v in indicator_data.items()}

        analysis_prompt = f"""
Analyze the following stock data for {symbol} ({market} market):

Latest Price Data:
- Date: {latest_data.get('date', 'N/A')}
- Open: {latest_data.get('open', 'N/A')}
- High: {latest_data.get('high', 'N/A')}
- Low: {latest_data.get('low', 'N/A')}
- Close: {latest_data.get('close', 'N/A')}
- Volume: {latest_data.get('volume', 'N/A')}

Technical Indicators:
{self._format_indicators(latest_indicators)}

Price trend over {period}:
- Starting price: {price_data[0].get('close', 'N/A') if price_data else 'N/A'}
- Current price: {latest_data.get('close', 'N/A')}
- Change: {self._calculate_change(price_data)}

Provide a comprehensive technical analysis summary including:
1. Current trend assessment
2. Key support/resistance levels based on recent data
3. Indicator signals and what they suggest
4. Short-term outlook
"""

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": analysis_prompt},
        ]

        summary = await self.call_llm(messages)

        return {
            "data": {
                "price_data": price_data[-30:],  # Last 30 days
                "indicators": indicator_data,
                "latest": {
                    "price": latest_data,
                    "indicators": latest_indicators,
                },
            },
            "summary": summary,
        }

    async def process(self, *args, **kwargs) -> dict[str, Any]:
        """Process method implementation."""
        return await self.analyze(*args, **kwargs)

    def _format_indicators(self, indicators: dict) -> str:
        """Format indicators for the prompt."""
        lines = []
        for key, value in indicators.items():
            if value is not None:
                if isinstance(value, float):
                    lines.append(f"- {key}: {value:.2f}")
                else:
                    lines.append(f"- {key}: {value}")
        return "\n".join(lines) if lines else "No indicators available"

    def _calculate_change(self, price_data: list[dict]) -> str:
        """Calculate price change over the period."""
        if not price_data or len(price_data) < 2:
            return "N/A"

        start_price = price_data[0].get("close", 0)
        end_price = price_data[-1].get("close", 0)

        if start_price == 0:
            return "N/A"

        change_pct = ((end_price - start_price) / start_price) * 100
        return f"{change_pct:+.2f}%"
