"""Recommendation Agent for comprehensive stock recommendations.

Integrates multiple analysis sources:
- Technical Analysis
- Fundamental Analysis
- Sentiment Analysis
- Valuation Analysis

Provides weighted recommendations with confidence levels.
"""

import logging
from typing import Any

from src.agents.base_agent import BaseAgent
from src.agents.technical import TechnicalAnalysisAgent
from src.agents.fundamental import FundamentalAnalysisAgent
from src.agents.sentiment import SentimentAgent
from src.agents.valuation import ValuationAgent

logger = logging.getLogger(__name__)


RECOMMENDATION_SYSTEM_PROMPT = """You are a senior investment advisor providing stock recommendations.

Your role is to synthesize multiple analysis dimensions and provide actionable investment advice.

Analysis Dimensions:
1. **Technical Analysis**: Price trends, support/resistance, indicators
2. **Fundamental Analysis**: Financial health, profitability, growth
3. **Sentiment Analysis**: News and social media sentiment
4. **Valuation Analysis**: Fair value vs current price

Recommendation Scale:
- Strong Buy (Score: 80-100): Highly attractive across all dimensions
- Buy (Score: 60-80): Generally favorable with minor concerns
- Hold (Score: 40-60): Mixed signals, maintain current position
- Sell (Score: 20-40): Generally unfavorable, consider reducing
- Strong Sell (Score: 0-20): Significant concerns across dimensions

For each recommendation, consider:
- Time horizon (short-term, medium-term, long-term)
- Risk tolerance alignment
- Position sizing suggestion
- Key catalysts and risk factors

Output your recommendation as JSON:
{
    "recommendation": "Strong Buy|Buy|Hold|Sell|Strong Sell",
    "overall_score": 0-100,
    "confidence": 0.0-1.0,
    "time_horizon": "short|medium|long",
    "dimension_scores": {
        "technical": {"score": 0-100, "weight": 0.0-1.0, "summary": "brief"},
        "fundamental": {"score": 0-100, "weight": 0.0-1.0, "summary": "brief"},
        "sentiment": {"score": 0-100, "weight": 0.0-1.0, "summary": "brief"},
        "valuation": {"score": 0-100, "weight": 0.0-1.0, "summary": "brief"}
    },
    "catalysts": ["catalyst1", "catalyst2"],
    "risks": ["risk1", "risk2"],
    "entry_price": float or null,
    "target_price": float or null,
    "stop_loss": float or null,
    "position_sizing": "small|medium|large",
    "summary": "2-3 sentence investment thesis"
}

Use Korean if any of the input analysis is in Korean, otherwise use English."""


RECOMMENDATION_TEMPLATE = """Provide a comprehensive investment recommendation for {symbol}:

## Company Overview
- Name: {company_name}
- Market: {market}
- Sector: {sector}
- Current Price: {current_price}

## Technical Analysis Summary
{technical_summary}

## Fundamental Analysis Summary
{fundamental_summary}

## Sentiment Analysis Summary
{sentiment_summary}

## Valuation Analysis Summary
{valuation_summary}

Based on all available analysis, provide a weighted recommendation.
Consider the investor profile: {investor_profile}
Time horizon preference: {time_horizon}"""


class RecommendAgent(BaseAgent):
    """Agent for comprehensive stock recommendations."""

    # Default weights for each dimension
    DEFAULT_WEIGHTS = {
        "technical": 0.2,
        "fundamental": 0.35,
        "sentiment": 0.15,
        "valuation": 0.3,
    }

    # Weights by investment style
    STYLE_WEIGHTS = {
        "growth": {
            "technical": 0.25,
            "fundamental": 0.30,
            "sentiment": 0.15,
            "valuation": 0.30,
        },
        "value": {
            "technical": 0.15,
            "fundamental": 0.35,
            "sentiment": 0.10,
            "valuation": 0.40,
        },
        "momentum": {
            "technical": 0.40,
            "fundamental": 0.15,
            "sentiment": 0.25,
            "valuation": 0.20,
        },
        "balanced": {
            "technical": 0.25,
            "fundamental": 0.25,
            "sentiment": 0.25,
            "valuation": 0.25,
        },
    }

    def __init__(self, **kwargs):
        super().__init__(temperature=0.3, **kwargs)

        # Initialize sub-agents
        self._technical_agent = TechnicalAnalysisAgent()
        self._fundamental_agent = FundamentalAnalysisAgent()
        self._sentiment_agent = SentimentAgent()
        self._valuation_agent = ValuationAgent()

    async def recommend(
        self,
        symbol: str,
        market: str = "US",
        investment_style: str = "balanced",
        time_horizon: str = "medium",
        youtube_channel: str | None = None,
        include_technical: bool = True,
        include_fundamental: bool = True,
        include_sentiment: bool = True,
        include_valuation: bool = True,
    ) -> dict[str, Any]:
        """Generate comprehensive stock recommendation.

        Args:
            symbol: Stock symbol.
            market: Market code ('US' or 'KR').
            investment_style: 'growth', 'value', 'momentum', or 'balanced'.
            time_horizon: 'short' (< 3 months), 'medium' (3-12 months), 'long' (> 1 year).
            youtube_channel: Optional YouTube channel for sentiment analysis.
            include_technical: Include technical analysis.
            include_fundamental: Include fundamental analysis.
            include_sentiment: Include sentiment analysis.
            include_valuation: Include valuation analysis.

        Returns:
            Comprehensive recommendation with all analysis.
        """
        # Get weights based on style
        weights = self.STYLE_WEIGHTS.get(investment_style, self.DEFAULT_WEIGHTS)

        # Collect all analyses
        analyses = {}
        current_price = None
        company_name = symbol
        sector = "N/A"

        # Technical Analysis
        if include_technical:
            try:
                technical = await self._technical_agent.analyze(symbol, market)
                analyses["technical"] = technical
                if technical.get("data", {}).get("prices"):
                    prices = technical["data"]["prices"]
                    if prices:
                        current_price = prices[-1].get("close")
            except Exception as e:
                logger.warning(f"Technical analysis failed: {e}")
                analyses["technical"] = {"error": str(e)}

        # Fundamental Analysis
        if include_fundamental:
            try:
                fundamental = await self._fundamental_agent.analyze(symbol, market)
                analyses["fundamental"] = fundamental
                if fundamental.get("data", {}).get("info"):
                    info = fundamental["data"]["info"]
                    company_name = info.get("name", symbol)
                    sector = info.get("sector", "N/A")
                    if not current_price:
                        current_price = info.get("current_price")
            except Exception as e:
                logger.warning(f"Fundamental analysis failed: {e}")
                analyses["fundamental"] = {"error": str(e)}

        # Sentiment Analysis
        if include_sentiment:
            try:
                if youtube_channel:
                    sentiment = await self._sentiment_agent.analyze_combined_sentiment(
                        symbol=symbol,
                        market=market,
                        youtube_channel=youtube_channel,
                    )
                else:
                    sentiment = await self._sentiment_agent.analyze_news_sentiment(
                        symbol=symbol,
                        market=market,
                    )
                analyses["sentiment"] = sentiment
            except Exception as e:
                logger.warning(f"Sentiment analysis failed: {e}")
                analyses["sentiment"] = {"error": str(e)}

        # Valuation Analysis
        if include_valuation:
            try:
                valuation = await self._valuation_agent.quick_valuation(symbol, market)
                analyses["valuation"] = valuation
                if not current_price and valuation.get("current_price"):
                    current_price = valuation["current_price"]
            except Exception as e:
                logger.warning(f"Valuation analysis failed: {e}")
                analyses["valuation"] = {"error": str(e)}

        # Format summaries for LLM
        summaries = self._format_analysis_summaries(analyses)

        # Generate recommendation
        prompt = RECOMMENDATION_TEMPLATE.format(
            symbol=symbol,
            company_name=company_name,
            market=market,
            sector=sector,
            current_price=current_price or "N/A",
            technical_summary=summaries.get("technical", "Not available"),
            fundamental_summary=summaries.get("fundamental", "Not available"),
            sentiment_summary=summaries.get("sentiment", "Not available"),
            valuation_summary=summaries.get("valuation", "Not available"),
            investor_profile=investment_style,
            time_horizon=time_horizon,
        )

        messages = [
            {"role": "system", "content": RECOMMENDATION_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]

        response = await self.call_llm(messages)
        result = self._parse_recommendation_response(response)

        # Calculate weighted overall score if not provided
        if not result.get("overall_score"):
            result["overall_score"] = self._calculate_overall_score(
                analyses, weights
            )

        # Get target_price from LLM or fallback to valuation fair_value
        target_price = result.get("target_price")
        if not target_price and "valuation" in analyses and not analyses["valuation"].get("error"):
            target_price = analyses["valuation"].get("fair_value_base")
            result["target_price"] = target_price

        # Calculate upside_potential from current_price and target_price
        upside_potential = None
        if current_price and target_price:
            upside_potential = ((target_price - current_price) / current_price) * 100

        return {
            "success": True,
            "symbol": symbol,
            "market": market,
            "company_name": company_name,
            "current_price": current_price,
            "investment_style": investment_style,
            "time_horizon": time_horizon,
            "weights": weights,
            "upside_potential": upside_potential,
            "analyses": {
                "technical": self._extract_summary(analyses.get("technical")),
                "fundamental": self._extract_summary(analyses.get("fundamental")),
                "sentiment": self._extract_summary(analyses.get("sentiment")),
                "valuation": self._extract_summary(analyses.get("valuation")),
            },
            **result,
        }

    async def quick_recommend(
        self,
        symbol: str,
        market: str = "US",
    ) -> dict[str, Any]:
        """Quick recommendation based on valuation and simple metrics.

        Args:
            symbol: Stock symbol.
            market: Market code.

        Returns:
            Quick recommendation result.
        """
        # Get quick valuation
        valuation = await self._valuation_agent.quick_valuation(symbol, market)

        if not valuation.get("success"):
            return {
                "success": False,
                "error": "Could not get valuation data",
            }

        # Convert valuation to recommendation
        upside = valuation.get("upside_potential", 0)
        status = valuation.get("valuation_status", "Fairly Valued")

        if upside > 30:
            recommendation = "Strong Buy"
            score = 85
        elif upside > 15:
            recommendation = "Buy"
            score = 70
        elif upside > 0:
            recommendation = "Hold"
            score = 55
        elif upside > -15:
            recommendation = "Hold"
            score = 45
        elif upside > -30:
            recommendation = "Sell"
            score = 30
        else:
            recommendation = "Strong Sell"
            score = 15

        return {
            "success": True,
            "symbol": symbol,
            "market": market,
            "recommendation": recommendation,
            "overall_score": score,
            "confidence": 0.5,  # Quick analysis = lower confidence
            "current_price": valuation.get("current_price"),
            "target_price": valuation.get("fair_value_base"),
            "upside_potential": upside,
            "valuation_status": status,
            "summary": f"{symbol} is {status.lower()} with {upside:.1f}% upside. Recommendation: {recommendation}.",
        }

    async def compare_recommendations(
        self,
        symbols: list[str],
        market: str = "US",
    ) -> dict[str, Any]:
        """Compare recommendations across multiple stocks.

        Args:
            symbols: List of stock symbols.
            market: Market code.

        Returns:
            Comparison of recommendations.
        """
        results = []

        for symbol in symbols[:5]:  # Limit to 5
            try:
                rec = await self.quick_recommend(symbol, market)
                if rec.get("success"):
                    results.append({
                        "symbol": symbol,
                        "recommendation": rec.get("recommendation"),
                        "score": rec.get("overall_score"),
                        "upside": rec.get("upside_potential"),
                        "current_price": rec.get("current_price"),
                        "target_price": rec.get("target_price"),
                    })
            except Exception as e:
                logger.warning(f"Error recommending {symbol}: {e}")

        # Sort by score
        results.sort(key=lambda x: x.get("score", 0), reverse=True)

        return {
            "success": True,
            "recommendations": results,
            "top_pick": results[0]["symbol"] if results else None,
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
        """Process recommendation request.

        Args:
            symbol: Single stock symbol.
            symbols: Multiple symbols for comparison.
            market: Market code.
            quick: Use quick recommendation.
            **kwargs: Additional parameters.

        Returns:
            Recommendation results.
        """
        if symbols and len(symbols) > 1:
            return await self.compare_recommendations(symbols, market)
        elif symbol:
            if quick:
                return await self.quick_recommend(symbol, market)
            else:
                return await self.recommend(symbol, market, **kwargs)
        else:
            return {
                "success": False,
                "error": "Please provide a symbol or list of symbols.",
            }

    def _format_analysis_summaries(self, analyses: dict) -> dict[str, str]:
        """Format analysis results into summaries for LLM."""
        summaries = {}

        # Technical summary
        if "technical" in analyses and not analyses["technical"].get("error"):
            tech = analyses["technical"]
            summaries["technical"] = tech.get("summary", "Technical analysis completed.")
        else:
            summaries["technical"] = "Technical analysis not available."

        # Fundamental summary
        if "fundamental" in analyses and not analyses["fundamental"].get("error"):
            fund = analyses["fundamental"]
            summaries["fundamental"] = fund.get("summary", "Fundamental analysis completed.")
        else:
            summaries["fundamental"] = "Fundamental analysis not available."

        # Sentiment summary
        if "sentiment" in analyses and not analyses["sentiment"].get("error"):
            sent = analyses["sentiment"]
            score = sent.get("sentiment_score", 0.5)
            label = sent.get("sentiment_label", "Neutral")
            summaries["sentiment"] = f"Sentiment: {label} (Score: {score:.2f}). {sent.get('summary', '')}"
        else:
            summaries["sentiment"] = "Sentiment analysis not available."

        # Valuation summary
        if "valuation" in analyses and not analyses["valuation"].get("error"):
            val = analyses["valuation"]
            status = val.get("valuation_status", "Unknown")
            upside = val.get("upside_potential", 0)
            fair_value = val.get("fair_value_base")
            summaries["valuation"] = f"Valuation: {status} (Upside: {upside:.1f}%, Fair Value: {fair_value})"
        else:
            summaries["valuation"] = "Valuation analysis not available."

        return summaries

    def _extract_summary(self, analysis: dict | None) -> dict[str, Any]:
        """Extract key summary from analysis result."""
        if not analysis or analysis.get("error"):
            return {"available": False, "error": analysis.get("error") if analysis else "Not performed"}

        return {
            "available": True,
            "summary": analysis.get("summary", "")[:200],
        }

    def _calculate_overall_score(
        self,
        analyses: dict,
        weights: dict,
    ) -> float:
        """Calculate weighted overall score from all analyses."""
        total_weight = 0
        weighted_score = 0

        # Technical score
        if "technical" in analyses and not analyses["technical"].get("error"):
            # Infer score from technical summary
            tech_score = 50  # Default neutral
            total_weight += weights.get("technical", 0)
            weighted_score += tech_score * weights.get("technical", 0)

        # Fundamental score
        if "fundamental" in analyses and not analyses["fundamental"].get("error"):
            fund_score = 50
            total_weight += weights.get("fundamental", 0)
            weighted_score += fund_score * weights.get("fundamental", 0)

        # Sentiment score
        if "sentiment" in analyses and not analyses["sentiment"].get("error"):
            sent = analyses["sentiment"]
            sent_score = sent.get("sentiment_score", 0.5) * 100
            total_weight += weights.get("sentiment", 0)
            weighted_score += sent_score * weights.get("sentiment", 0)

        # Valuation score
        if "valuation" in analyses and not analyses["valuation"].get("error"):
            val = analyses["valuation"]
            upside = val.get("upside_potential", 0)
            # Convert upside to score (0-100)
            val_score = min(100, max(0, 50 + upside * 1.5))
            total_weight += weights.get("valuation", 0)
            weighted_score += val_score * weights.get("valuation", 0)

        if total_weight > 0:
            return round(weighted_score / total_weight)
        return 50

    def _parse_recommendation_response(self, response: str) -> dict[str, Any]:
        """Parse LLM recommendation response."""
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
                "recommendation": result.get("recommendation", "Hold"),
                "overall_score": result.get("overall_score"),
                "confidence": result.get("confidence", 0.5),
                "time_horizon": result.get("time_horizon", "medium"),
                "dimension_scores": result.get("dimension_scores", {}),
                "catalysts": result.get("catalysts", []),
                "risks": result.get("risks", []),
                "entry_price": result.get("entry_price"),
                "target_price": result.get("target_price"),
                "stop_loss": result.get("stop_loss"),
                "position_sizing": result.get("position_sizing", "medium"),
                "summary": result.get("summary", ""),
            }

        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Failed to parse recommendation response: {e}")
            return {
                "recommendation": "Hold",
                "overall_score": 50,
                "confidence": 0.3,
                "time_horizon": "medium",
                "dimension_scores": {},
                "catalysts": [],
                "risks": [],
                "entry_price": None,
                "target_price": None,
                "stop_loss": None,
                "position_sizing": "small",
                "summary": response[:500] if response else "",
            }
