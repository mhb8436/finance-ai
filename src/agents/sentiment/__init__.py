"""Sentiment Analysis Agent.

Analyzes market sentiment from news and YouTube content.

Example:
    from src.agents.sentiment import SentimentAgent

    agent = SentimentAgent()

    # Analyze news sentiment
    result = await agent.analyze_news_sentiment("AAPL", market="US")

    # Analyze YouTube sentiment
    result = await agent.analyze_youtube_sentiment(channel="삼프로TV")

    # Combined analysis
    result = await agent.analyze_combined_sentiment(
        symbol="005930",
        market="KR",
        youtube_channel="삼프로TV",
    )
"""

from .agent import SentimentAgent

__all__ = ["SentimentAgent"]
