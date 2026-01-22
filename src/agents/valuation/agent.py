"""Valuation Agent for fair value calculation.

Calculates intrinsic value using multiple methods:
- DCF (Discounted Cash Flow)
- PER (Price-to-Earnings Ratio) based
- PBR (Price-to-Book Ratio) based
- Gordon Growth Model (for dividend stocks)
- Peer Comparison

Provides comprehensive valuation analysis with target prices.
"""

import logging
from typing import Any

from src.agents.base_agent import BaseAgent
from src.tools.stock_data import get_stock_info, get_stock_price
from src.tools.financials import get_financial_statements, get_financial_ratios

logger = logging.getLogger(__name__)


VALUATION_SYSTEM_PROMPT = """You are a professional equity analyst specializing in company valuation.

Your role is to calculate fair value for stocks using multiple valuation methods and provide investment recommendations.

Valuation Methods to Consider:
1. **DCF (Discounted Cash Flow)**: Project future free cash flows and discount to present value
2. **PER-based**: Compare to historical P/E and industry average P/E
3. **PBR-based**: Compare to historical P/B and industry average P/B
4. **Gordon Growth Model**: For dividend-paying stocks (Value = D1 / (r - g))
5. **EV/EBITDA Multiple**: Enterprise value approach
6. **Peer Comparison**: Compare valuation multiples to similar companies

For each method, consider:
- Growth assumptions (conservative, base, optimistic)
- Discount rate / required return
- Terminal value / exit multiple
- Industry-specific factors
- Market conditions

Output your valuation as JSON:
{
    "fair_value_low": float,
    "fair_value_base": float,
    "fair_value_high": float,
    "current_price": float,
    "upside_potential": float (percentage),
    "valuation_status": "Undervalued|Fairly Valued|Overvalued",
    "confidence": float (0-1),
    "methods_used": [
        {
            "method": "DCF|PER|PBR|Gordon|EV/EBITDA|Peer",
            "fair_value": float,
            "weight": float (0-1),
            "assumptions": "key assumptions"
        }
    ],
    "key_drivers": ["driver1", "driver2"],
    "risks": ["risk1", "risk2"],
    "recommendation": "Strong Buy|Buy|Hold|Sell|Strong Sell",
    "summary": "valuation summary in 2-3 sentences"
}

Use Korean if the user's query is in Korean, otherwise use English."""


VALUATION_ANALYSIS_TEMPLATE = """Perform a comprehensive valuation analysis for {symbol} ({company_name}):

## Company Information
- Market: {market}
- Sector: {sector}
- Industry: {industry}
- Market Cap: {market_cap}
- Current Price: {current_price}

## Valuation Multiples
- P/E Ratio: {pe_ratio}
- P/B Ratio: {pb_ratio}
- EV/EBITDA: {ev_ebitda}
- Price/Sales: {ps_ratio}

## Financial Data
{financial_data}

## Growth Metrics
- Revenue Growth: {revenue_growth}
- Earnings Growth: {earnings_growth}
- 5-Year Growth Rate: {growth_rate_5y}

## Dividend Information
- Dividend Yield: {dividend_yield}
- Payout Ratio: {payout_ratio}

## Historical Price Range
- 52-Week High: {high_52w}
- 52-Week Low: {low_52w}
- Current vs 52W High: {vs_high}%
- Current vs 52W Low: {vs_low}%

Calculate fair value using appropriate methods based on the company characteristics.
Weight each method based on relevance and reliability for this company."""


class ValuationAgent(BaseAgent):
    """Agent for stock valuation and fair value calculation."""

    # Industry average multiples for comparison
    INDUSTRY_MULTIPLES = {
        "Technology": {"pe": 25, "pb": 5, "ev_ebitda": 15},
        "Financial Services": {"pe": 12, "pb": 1.2, "ev_ebitda": 8},
        "Healthcare": {"pe": 20, "pb": 4, "ev_ebitda": 12},
        "Consumer Cyclical": {"pe": 18, "pb": 3, "ev_ebitda": 10},
        "Consumer Defensive": {"pe": 22, "pb": 4, "ev_ebitda": 12},
        "Energy": {"pe": 10, "pb": 1.5, "ev_ebitda": 5},
        "Industrials": {"pe": 18, "pb": 3, "ev_ebitda": 10},
        "Basic Materials": {"pe": 12, "pb": 2, "ev_ebitda": 7},
        "Utilities": {"pe": 18, "pb": 1.5, "ev_ebitda": 10},
        "Real Estate": {"pe": 35, "pb": 2, "ev_ebitda": 15},
        "Communication Services": {"pe": 20, "pb": 3, "ev_ebitda": 10},
        "default": {"pe": 18, "pb": 2.5, "ev_ebitda": 10},
    }

    def __init__(self, **kwargs):
        super().__init__(temperature=0.2, **kwargs)

    async def calculate_fair_value(
        self,
        symbol: str,
        market: str = "US",
        methods: list[str] | None = None,
        discount_rate: float | None = None,
        growth_assumption: str = "base",
    ) -> dict[str, Any]:
        """Calculate fair value using multiple valuation methods.

        Args:
            symbol: Stock symbol.
            market: Market code ('US' or 'KR').
            methods: List of methods to use. If None, uses all applicable.
            discount_rate: Discount rate for DCF. If None, calculates based on risk.
            growth_assumption: 'conservative', 'base', or 'optimistic'.

        Returns:
            Comprehensive valuation analysis.
        """
        # Fetch all required data
        stock_info = await get_stock_info(symbol, market)
        financials = await get_financial_statements(symbol, market)
        ratios = await get_financial_ratios(symbol, market)
        prices = await get_stock_price(symbol, market, period="1y")

        # Calculate price statistics
        price_stats = self._calculate_price_stats(prices, stock_info)

        # Get industry multiples
        sector = stock_info.get("sector", "default")
        industry_multiples = self.INDUSTRY_MULTIPLES.get(
            sector, self.INDUSTRY_MULTIPLES["default"]
        )

        # Prepare financial data summary
        financial_data = self._format_financial_data(financials, ratios)

        # Calculate growth metrics
        growth_metrics = self._calculate_growth_metrics(financials)

        # Format prompt
        analysis_prompt = VALUATION_ANALYSIS_TEMPLATE.format(
            symbol=symbol,
            company_name=stock_info.get("name", symbol),
            market=market,
            sector=sector,
            industry=stock_info.get("industry", "N/A"),
            market_cap=self._format_number(stock_info.get("market_cap")),
            current_price=price_stats.get("current_price", "N/A"),
            pe_ratio=self._format_ratio(stock_info.get("pe_ratio")),
            pb_ratio=self._format_ratio(stock_info.get("pb_ratio")),
            ev_ebitda=self._format_ratio(ratios.get("ev_ebitda")),
            ps_ratio=self._format_ratio(ratios.get("price_to_sales")),
            financial_data=financial_data,
            revenue_growth=self._format_percent(growth_metrics.get("revenue_growth")),
            earnings_growth=self._format_percent(growth_metrics.get("earnings_growth")),
            growth_rate_5y=self._format_percent(growth_metrics.get("growth_rate_5y")),
            dividend_yield=self._format_percent(stock_info.get("dividend_yield")),
            payout_ratio=self._format_percent(ratios.get("payout_ratio")),
            high_52w=price_stats.get("high_52w", "N/A"),
            low_52w=price_stats.get("low_52w", "N/A"),
            vs_high=price_stats.get("vs_high", "N/A"),
            vs_low=price_stats.get("vs_low", "N/A"),
        )

        messages = [
            {"role": "system", "content": VALUATION_SYSTEM_PROMPT},
            {"role": "user", "content": analysis_prompt},
        ]

        response = await self.call_llm(messages)
        result = self._parse_valuation_response(response)

        # Add raw data
        result["raw_data"] = {
            "current_price": price_stats.get("current_price"),
            "market_cap": stock_info.get("market_cap"),
            "pe_ratio": stock_info.get("pe_ratio"),
            "pb_ratio": stock_info.get("pb_ratio"),
            "dividend_yield": stock_info.get("dividend_yield"),
            "sector": sector,
            "industry_multiples": industry_multiples,
        }

        return {
            "success": True,
            "symbol": symbol,
            "market": market,
            **result,
        }

    async def quick_valuation(
        self,
        symbol: str,
        market: str = "US",
    ) -> dict[str, Any]:
        """Quick valuation using simple multiple-based methods.

        Args:
            symbol: Stock symbol.
            market: Market code.

        Returns:
            Quick valuation result.
        """
        stock_info = await get_stock_info(symbol, market)
        ratios = await get_financial_ratios(symbol, market)

        current_price = stock_info.get("current_price") or stock_info.get("close")
        pe_ratio = stock_info.get("pe_ratio")
        pb_ratio = stock_info.get("pb_ratio")

        if not current_price:
            return {
                "success": False,
                "error": "Could not get current price",
            }

        sector = stock_info.get("sector", "default")
        industry_multiples = self.INDUSTRY_MULTIPLES.get(
            sector, self.INDUSTRY_MULTIPLES["default"]
        )

        valuations = []

        # PER-based valuation
        if pe_ratio and pe_ratio > 0:
            eps = current_price / pe_ratio
            target_pe = industry_multiples["pe"]
            per_fair_value = eps * target_pe
            valuations.append({
                "method": "PER",
                "fair_value": per_fair_value,
                "weight": 0.4,
                "assumptions": f"Target P/E: {target_pe} (industry avg)",
            })

        # PBR-based valuation
        if pb_ratio and pb_ratio > 0:
            bps = current_price / pb_ratio
            target_pb = industry_multiples["pb"]
            pbr_fair_value = bps * target_pb
            valuations.append({
                "method": "PBR",
                "fair_value": pbr_fair_value,
                "weight": 0.3,
                "assumptions": f"Target P/B: {target_pb} (industry avg)",
            })

        # 52-week range midpoint
        high_52w = stock_info.get("52_week_high")
        low_52w = stock_info.get("52_week_low")
        if high_52w and low_52w:
            range_midpoint = (high_52w + low_52w) / 2
            valuations.append({
                "method": "52W Range",
                "fair_value": range_midpoint,
                "weight": 0.3,
                "assumptions": "Midpoint of 52-week range",
            })

        if not valuations:
            return {
                "success": False,
                "error": "Insufficient data for valuation",
            }

        # Calculate weighted fair value
        total_weight = sum(v["weight"] for v in valuations)
        weighted_fair_value = sum(
            v["fair_value"] * v["weight"] for v in valuations
        ) / total_weight

        # Calculate upside
        upside = ((weighted_fair_value - current_price) / current_price) * 100

        # Determine valuation status
        if upside > 20:
            status = "Undervalued"
            recommendation = "Buy"
        elif upside > 5:
            status = "Slightly Undervalued"
            recommendation = "Buy"
        elif upside > -5:
            status = "Fairly Valued"
            recommendation = "Hold"
        elif upside > -20:
            status = "Slightly Overvalued"
            recommendation = "Hold"
        else:
            status = "Overvalued"
            recommendation = "Sell"

        return {
            "success": True,
            "symbol": symbol,
            "market": market,
            "current_price": current_price,
            "fair_value_base": round(weighted_fair_value, 2),
            "fair_value_low": round(weighted_fair_value * 0.9, 2),
            "fair_value_high": round(weighted_fair_value * 1.1, 2),
            "upside_potential": round(upside, 1),
            "valuation_status": status,
            "recommendation": recommendation,
            "methods_used": valuations,
            "confidence": 0.6,
            "summary": f"{symbol} appears {status.lower()} with {upside:.1f}% upside potential based on multiple valuation.",
        }

    async def compare_valuations(
        self,
        symbols: list[str],
        market: str = "US",
    ) -> dict[str, Any]:
        """Compare valuations across multiple stocks.

        Args:
            symbols: List of stock symbols.
            market: Market code.

        Returns:
            Comparison of valuations.
        """
        results = []

        for symbol in symbols[:5]:  # Limit to 5 stocks
            try:
                valuation = await self.quick_valuation(symbol, market)
                if valuation.get("success"):
                    results.append({
                        "symbol": symbol,
                        "current_price": valuation.get("current_price"),
                        "fair_value": valuation.get("fair_value_base"),
                        "upside": valuation.get("upside_potential"),
                        "status": valuation.get("valuation_status"),
                        "recommendation": valuation.get("recommendation"),
                    })
            except Exception as e:
                logger.warning(f"Error valuating {symbol}: {e}")

        # Sort by upside potential
        results.sort(key=lambda x: x.get("upside", 0), reverse=True)

        return {
            "success": True,
            "comparison": results,
            "best_value": results[0]["symbol"] if results else None,
            "count": len(results),
        }

    async def process(
        self,
        symbol: str | None = None,
        symbols: list[str] | None = None,
        market: str = "US",
        quick: bool = False,
        **kwargs,
    ) -> dict[str, Any]:
        """Process valuation request.

        Args:
            symbol: Single stock symbol.
            symbols: Multiple symbols for comparison.
            market: Market code.
            quick: Use quick valuation method.
            **kwargs: Additional parameters.

        Returns:
            Valuation results.
        """
        if symbols and len(symbols) > 1:
            return await self.compare_valuations(symbols, market)
        elif symbol:
            if quick:
                return await self.quick_valuation(symbol, market)
            else:
                return await self.calculate_fair_value(symbol, market, **kwargs)
        else:
            return {
                "success": False,
                "error": "Please provide a symbol or list of symbols.",
            }

    def _calculate_price_stats(
        self,
        prices: list[dict] | None,
        stock_info: dict,
    ) -> dict[str, Any]:
        """Calculate price statistics."""
        result: dict[str, Any] = {}

        # Current price
        if prices and len(prices) > 0:
            result["current_price"] = prices[-1].get("close")
        else:
            result["current_price"] = stock_info.get("current_price")

        # 52-week range
        high_52w = stock_info.get("52_week_high")
        low_52w = stock_info.get("52_week_low")

        if high_52w:
            result["high_52w"] = high_52w
        if low_52w:
            result["low_52w"] = low_52w

        # Calculate vs high/low
        current = result.get("current_price")
        if current and high_52w:
            result["vs_high"] = round(((current - high_52w) / high_52w) * 100, 1)
        if current and low_52w:
            result["vs_low"] = round(((current - low_52w) / low_52w) * 100, 1)

        return result

    def _format_financial_data(
        self,
        financials: dict | None,
        ratios: dict | None,
    ) -> str:
        """Format financial data for analysis."""
        lines = []

        if financials:
            if "income_statement" in financials:
                income = financials["income_statement"]
                lines.append(f"- Revenue: {self._format_number(income.get('revenue'))}")
                lines.append(f"- Net Income: {self._format_number(income.get('net_income'))}")
                lines.append(f"- Operating Income: {self._format_number(income.get('operating_income'))}")

            if "balance_sheet" in financials:
                balance = financials["balance_sheet"]
                lines.append(f"- Total Assets: {self._format_number(balance.get('total_assets'))}")
                lines.append(f"- Total Equity: {self._format_number(balance.get('total_equity'))}")
                lines.append(f"- Total Debt: {self._format_number(balance.get('total_debt'))}")

            if "cash_flow" in financials:
                cf = financials["cash_flow"]
                lines.append(f"- Free Cash Flow: {self._format_number(cf.get('free_cash_flow'))}")

        if ratios:
            lines.append(f"- ROE: {self._format_percent(ratios.get('roe'))}")
            lines.append(f"- ROA: {self._format_percent(ratios.get('roa'))}")
            lines.append(f"- Profit Margin: {self._format_percent(ratios.get('profit_margin'))}")
            lines.append(f"- Debt/Equity: {self._format_ratio(ratios.get('debt_to_equity'))}")

        return "\n".join(lines) if lines else "Financial data not available"

    def _calculate_growth_metrics(self, financials: dict | None) -> dict[str, Any]:
        """Calculate growth metrics from financial data."""
        # This would ideally compare historical data
        # For now, return placeholders or extract from financials
        return {
            "revenue_growth": financials.get("revenue_growth") if financials else None,
            "earnings_growth": financials.get("earnings_growth") if financials else None,
            "growth_rate_5y": financials.get("growth_rate_5y") if financials else None,
        }

    def _format_number(self, value: float | None) -> str:
        """Format large numbers."""
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
        """Format percentage."""
        if value is None:
            return "N/A"
        return f"{value * 100:.2f}%" if abs(value) < 1 else f"{value:.2f}%"

    def _format_ratio(self, value: float | None) -> str:
        """Format ratio."""
        if value is None:
            return "N/A"
        return f"{value:.2f}"

    def _parse_valuation_response(self, response: str) -> dict[str, Any]:
        """Parse LLM valuation response."""
        import json

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
                    raise ValueError("No JSON found")

            result = json.loads(json_str)

            return {
                "fair_value_low": result.get("fair_value_low"),
                "fair_value_base": result.get("fair_value_base"),
                "fair_value_high": result.get("fair_value_high"),
                "current_price": result.get("current_price"),
                "upside_potential": result.get("upside_potential"),
                "valuation_status": result.get("valuation_status", "Fairly Valued"),
                "confidence": result.get("confidence", 0.5),
                "methods_used": result.get("methods_used", []),
                "key_drivers": result.get("key_drivers", []),
                "risks": result.get("risks", []),
                "recommendation": result.get("recommendation", "Hold"),
                "summary": result.get("summary", ""),
            }

        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Failed to parse valuation response: {e}")
            return {
                "fair_value_low": None,
                "fair_value_base": None,
                "fair_value_high": None,
                "valuation_status": "Unknown",
                "confidence": 0.3,
                "methods_used": [],
                "key_drivers": [],
                "risks": [],
                "recommendation": "Hold",
                "summary": response[:500] if response else "",
            }
