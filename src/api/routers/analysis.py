"""Analysis API endpoints."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any

router = APIRouter()


class TechnicalAnalysisRequest(BaseModel):
    symbol: str
    market: str = "US"
    indicators: list[str] = ["sma", "ema", "rsi", "macd"]
    period: str = "6mo"


class FundamentalAnalysisRequest(BaseModel):
    symbol: str
    market: str = "US"
    include_financials: bool = True
    include_ratios: bool = True


class SentimentAnalysisRequest(BaseModel):
    symbol: str | None = None
    market: str = "US"
    video_url: str | None = None
    youtube_channel: str | None = None
    source: str = "combined"  # news, youtube, combined
    news_limit: int = 10


class ValuationRequest(BaseModel):
    symbol: str | None = None
    symbols: list[str] | None = None
    market: str = "US"
    quick: bool = True


class RecommendationRequest(BaseModel):
    symbol: str | None = None
    symbols: list[str] | None = None
    market: str = "US"
    investment_style: str = "balanced"  # growth, value, momentum, balanced
    time_horizon: str = "medium"  # short, medium, long
    youtube_channel: str | None = None
    quick: bool = False


class AnalysisResponse(BaseModel):
    symbol: str
    market: str
    analysis_type: str
    result: dict
    summary: str | None = None


class SentimentResponse(BaseModel):
    success: bool
    symbol: str | None = None
    source: str
    sentiment_score: float | None = None
    sentiment_label: str | None = None
    confidence: float | None = None
    key_themes: list[str] = []
    summary: str | None = None
    data: dict[str, Any] = {}


class ValuationResponse(BaseModel):
    success: bool
    symbol: str | None = None
    market: str
    current_price: float | None = None
    fair_value_base: float | None = None
    fair_value_low: float | None = None
    fair_value_high: float | None = None
    upside_potential: float | None = None
    valuation_status: str | None = None
    recommendation: str | None = None
    methods_used: list[dict] = []
    summary: str | None = None


class RecommendationResponse(BaseModel):
    success: bool
    symbol: str | None = None
    market: str
    recommendation: str | None = None
    overall_score: float | None = None
    confidence: float | None = None
    current_price: float | None = None
    target_price: float | None = None
    upside_potential: float | None = None
    catalysts: list[str] = []
    risks: list[str] = []
    summary: str | None = None
    analyses: dict[str, Any] = {}


@router.post("/technical")
async def technical_analysis(request: TechnicalAnalysisRequest) -> AnalysisResponse:
    """Perform technical analysis on a stock."""
    try:
        from src.agents.technical import TechnicalAnalysisAgent

        agent = TechnicalAnalysisAgent()
        result = await agent.analyze(
            symbol=request.symbol,
            market=request.market,
            indicators=request.indicators,
            period=request.period,
        )
        return AnalysisResponse(
            symbol=request.symbol,
            market=request.market,
            analysis_type="technical",
            result=result["data"],
            summary=result.get("summary"),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/fundamental")
async def fundamental_analysis(request: FundamentalAnalysisRequest) -> AnalysisResponse:
    """Perform fundamental analysis on a stock."""
    try:
        from src.agents.fundamental import FundamentalAnalysisAgent

        agent = FundamentalAnalysisAgent()
        result = await agent.analyze(
            symbol=request.symbol,
            market=request.market,
            include_financials=request.include_financials,
            include_ratios=request.include_ratios,
        )
        return AnalysisResponse(
            symbol=request.symbol,
            market=request.market,
            analysis_type="fundamental",
            result=result["data"],
            summary=result.get("summary"),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sentiment")
async def sentiment_analysis(request: SentimentAnalysisRequest) -> SentimentResponse:
    """Perform sentiment analysis from news and/or YouTube.

    Sources:
    - news: Analyze news articles only
    - youtube: Analyze YouTube videos only
    - combined: Analyze both news and YouTube (default)
    """
    try:
        from src.agents.sentiment import SentimentAgent

        agent = SentimentAgent()
        result = await agent.process(
            symbol=request.symbol,
            market=request.market,
            video_url=request.video_url,
            youtube_channel=request.youtube_channel,
            source=request.source,
            news_limit=request.news_limit,
        )

        return SentimentResponse(
            success=result.get("success", False),
            symbol=request.symbol,
            source=result.get("source", request.source),
            sentiment_score=result.get("sentiment_score"),
            sentiment_label=result.get("sentiment_label"),
            confidence=result.get("confidence"),
            key_themes=result.get("key_themes", []),
            summary=result.get("summary"),
            data=result,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/valuation")
async def valuation_analysis(request: ValuationRequest) -> ValuationResponse:
    """Calculate fair value for a stock.

    Methods:
    - quick=True: Simple multiple-based valuation (faster)
    - quick=False: Full DCF and multi-method analysis
    - symbols: Compare multiple stocks
    """
    try:
        from src.agents.valuation import ValuationAgent

        agent = ValuationAgent()
        result = await agent.process(
            symbol=request.symbol,
            symbols=request.symbols,
            market=request.market,
            quick=request.quick,
        )

        return ValuationResponse(
            success=result.get("success", False),
            symbol=request.symbol,
            market=request.market,
            current_price=result.get("current_price"),
            fair_value_base=result.get("fair_value_base"),
            fair_value_low=result.get("fair_value_low"),
            fair_value_high=result.get("fair_value_high"),
            upside_potential=result.get("upside_potential"),
            valuation_status=result.get("valuation_status"),
            recommendation=result.get("recommendation"),
            methods_used=result.get("methods_used", []),
            summary=result.get("summary"),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/recommend")
async def stock_recommendation(request: RecommendationRequest) -> RecommendationResponse:
    """Get comprehensive stock recommendation.

    Integrates technical, fundamental, sentiment, and valuation analyses.

    Investment Styles:
    - balanced: Equal weight across all dimensions
    - growth: Higher weight on growth metrics and momentum
    - value: Higher weight on valuation and fundamentals
    - momentum: Higher weight on technical and sentiment

    Time Horizons:
    - short: < 3 months
    - medium: 3-12 months
    - long: > 1 year
    """
    try:
        from src.agents.recommend import RecommendAgent

        agent = RecommendAgent()
        result = await agent.process(
            symbol=request.symbol,
            symbols=request.symbols,
            market=request.market,
            quick=request.quick,
            investment_style=request.investment_style,
            time_horizon=request.time_horizon,
            youtube_channel=request.youtube_channel,
        )

        return RecommendationResponse(
            success=result.get("success", False),
            symbol=request.symbol,
            market=request.market,
            recommendation=result.get("recommendation"),
            overall_score=result.get("overall_score"),
            confidence=result.get("confidence"),
            current_price=result.get("current_price"),
            target_price=result.get("target_price"),
            upside_potential=result.get("upside_potential"),
            catalysts=result.get("catalysts", []),
            risks=result.get("risks", []),
            summary=result.get("summary"),
            analyses=result.get("analyses", {}),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recommend/{symbol}")
async def quick_recommendation(
    symbol: str,
    market: str = "US",
    mode: str = "quick",  # quick or full
    investment_style: str = "balanced",  # growth, value, momentum, balanced
    time_horizon: str = "medium",  # short, medium, long
) -> RecommendationResponse:
    """Get stock recommendation.

    Modes:
    - quick: Fast valuation-based analysis only
    - full: Comprehensive analysis (technical + fundamental + sentiment + valuation)

    Investment Styles (for full mode):
    - balanced: Equal weight across all dimensions
    - growth: Higher weight on growth metrics and momentum
    - value: Higher weight on valuation and fundamentals
    - momentum: Higher weight on technical and sentiment
    """
    try:
        from src.agents.recommend import RecommendAgent

        agent = RecommendAgent()

        if mode == "full":
            # Comprehensive analysis
            result = await agent.recommend(
                symbol=symbol,
                market=market,
                investment_style=investment_style,
                time_horizon=time_horizon,
            )
        else:
            # Quick valuation-based analysis
            result = await agent.quick_recommend(symbol, market)

        return RecommendationResponse(
            success=result.get("success", False),
            symbol=symbol,
            market=market,
            recommendation=result.get("recommendation"),
            overall_score=result.get("overall_score"),
            confidence=result.get("confidence"),
            current_price=result.get("current_price"),
            target_price=result.get("target_price"),
            upside_potential=result.get("upside_potential"),
            catalysts=result.get("catalysts", []),
            risks=result.get("risks", []),
            summary=result.get("summary"),
            analyses=result.get("analyses", {}),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
