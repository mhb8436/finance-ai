"""Recommendation Agent.

Provides comprehensive stock recommendations by integrating
Technical, Fundamental, Sentiment, and Valuation analyses.

Example:
    from src.agents.recommend import RecommendAgent

    agent = RecommendAgent()

    # Full recommendation
    result = await agent.recommend(
        symbol="AAPL",
        market="US",
        investment_style="growth",
        time_horizon="medium",
    )

    # Quick recommendation
    result = await agent.quick_recommend("005930", market="KR")

    # Compare multiple stocks
    result = await agent.compare_recommendations(["AAPL", "MSFT", "GOOGL"])
"""

from .agent import RecommendAgent

__all__ = ["RecommendAgent"]
