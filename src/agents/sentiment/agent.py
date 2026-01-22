"""Sentiment Analysis Agent for news and YouTube content.

Analyzes sentiment from multiple sources:
- News articles
- YouTube video transcripts
- Social media mentions (future)

Provides sentiment scores and key insights.
"""

import logging
from typing import Any

from src.agents.base_agent import BaseAgent
from src.tools.news_search import search_news
from src.tools.youtube_tool import get_transcript, get_channel_videos

logger = logging.getLogger(__name__)


SENTIMENT_SYSTEM_PROMPT = """You are a financial sentiment analyst specializing in market sentiment analysis.

Your role is to analyze news articles, video transcripts, and other content to determine market sentiment.

When analyzing sentiment, consider:
1. Overall tone (positive, negative, neutral)
2. Key themes and topics mentioned
3. Market implications
4. Risk factors highlighted
5. Confidence level of the assessment

Sentiment Scale:
- Very Bullish (0.8 to 1.0): Strongly positive outlook
- Bullish (0.5 to 0.8): Positive outlook
- Neutral (0.3 to 0.5): Mixed or balanced outlook
- Bearish (0.1 to 0.3): Negative outlook
- Very Bearish (0.0 to 0.1): Strongly negative outlook

Output your analysis as JSON:
{
    "sentiment_score": 0.0-1.0,
    "sentiment_label": "Very Bullish|Bullish|Neutral|Bearish|Very Bearish",
    "confidence": 0.0-1.0,
    "key_themes": ["theme1", "theme2"],
    "positive_factors": ["factor1", "factor2"],
    "negative_factors": ["factor1", "factor2"],
    "market_implications": "brief summary",
    "summary": "overall sentiment summary in 2-3 sentences"
}

Use Korean if the content is in Korean, otherwise use English."""


NEWS_ANALYSIS_TEMPLATE = """Analyze the sentiment of the following news articles about {symbol}:

{news_content}

Provide a comprehensive sentiment analysis based on these articles."""


YOUTUBE_ANALYSIS_TEMPLATE = """Analyze the sentiment of the following YouTube video transcript about {topic}:

Video Title: {title}
Channel: {channel}

Transcript:
{transcript}

Provide a comprehensive sentiment analysis based on this video content."""


COMBINED_ANALYSIS_TEMPLATE = """Analyze the overall market sentiment for {symbol} based on the following sources:

## News Sentiment
{news_sentiment}

## YouTube Sentiment
{youtube_sentiment}

Provide a combined sentiment analysis that weighs both news and video content appropriately.
News should be weighted {news_weight}% and YouTube content {youtube_weight}%."""


class SentimentAgent(BaseAgent):
    """Agent for sentiment analysis of news and YouTube content."""

    def __init__(self, **kwargs):
        super().__init__(temperature=0.3, **kwargs)

    async def analyze_news_sentiment(
        self,
        symbol: str,
        market: str = "US",
        news_limit: int = 10,
    ) -> dict[str, Any]:
        """Analyze sentiment from news articles.

        Args:
            symbol: Stock symbol to analyze.
            market: Market code ('US' or 'KR').
            news_limit: Maximum number of news articles.

        Returns:
            Sentiment analysis results.
        """
        # Fetch news
        news = await search_news(symbol, market=market, limit=news_limit)

        if not news:
            return {
                "success": False,
                "error": "No news articles found",
                "sentiment_score": 0.5,
                "sentiment_label": "Neutral",
            }

        # Format news for analysis
        news_content = self._format_news_for_analysis(news)

        messages = [
            {"role": "system", "content": SENTIMENT_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": NEWS_ANALYSIS_TEMPLATE.format(
                    symbol=symbol,
                    news_content=news_content,
                ),
            },
        ]

        response = await self.call_llm(messages)
        result = self._parse_sentiment_response(response)

        return {
            "success": True,
            "source": "news",
            "symbol": symbol,
            "articles_analyzed": len(news),
            "news_titles": [n.get("title", "") for n in news[:5]],
            **result,
        }

    async def analyze_youtube_sentiment(
        self,
        video_url_or_id: str | None = None,
        channel: str | None = None,
        topic: str | None = None,
        max_videos: int = 3,
    ) -> dict[str, Any]:
        """Analyze sentiment from YouTube videos.

        Args:
            video_url_or_id: Specific video URL or ID to analyze.
            channel: YouTube channel to get recent videos from.
            topic: Topic for context in analysis.
            max_videos: Maximum videos to analyze from channel.

        Returns:
            Sentiment analysis results.
        """
        transcripts = []

        if video_url_or_id:
            # Analyze specific video
            transcript = await get_transcript(video_url_or_id)
            if transcript:
                transcripts.append(transcript)
        elif channel:
            # Get recent videos from channel
            videos = await get_channel_videos(channel, max_results=max_videos)
            for video in videos[:max_videos]:
                transcript = await get_transcript(video.video_id)
                if transcript:
                    transcripts.append(transcript)

        if not transcripts:
            return {
                "success": False,
                "error": "No transcripts available",
                "sentiment_score": 0.5,
                "sentiment_label": "Neutral",
            }

        # Analyze each transcript
        all_results = []
        for transcript in transcripts:
            # Truncate long transcripts
            text = transcript.text[:8000] if len(transcript.text) > 8000 else transcript.text

            messages = [
                {"role": "system", "content": SENTIMENT_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": YOUTUBE_ANALYSIS_TEMPLATE.format(
                        topic=topic or "investment analysis",
                        title=transcript.title,
                        channel=transcript.channel_name,
                        transcript=text,
                    ),
                },
            ]

            response = await self.call_llm(messages)
            result = self._parse_sentiment_response(response)
            result["video_id"] = transcript.video_id
            result["video_title"] = transcript.title
            result["channel"] = transcript.channel_name
            all_results.append(result)

        # Aggregate results if multiple videos
        if len(all_results) == 1:
            aggregated = all_results[0]
        else:
            aggregated = self._aggregate_sentiments(all_results)

        return {
            "success": True,
            "source": "youtube",
            "videos_analyzed": len(transcripts),
            "video_details": [
                {
                    "video_id": r.get("video_id"),
                    "title": r.get("video_title"),
                    "channel": r.get("channel"),
                    "sentiment_score": r.get("sentiment_score", 0.5),
                }
                for r in all_results
            ],
            **aggregated,
        }

    async def analyze_combined_sentiment(
        self,
        symbol: str,
        market: str = "US",
        youtube_channel: str | None = None,
        news_weight: float = 0.6,
        youtube_weight: float = 0.4,
        news_limit: int = 10,
        youtube_videos: int = 3,
    ) -> dict[str, Any]:
        """Analyze combined sentiment from news and YouTube.

        Args:
            symbol: Stock symbol to analyze.
            market: Market code.
            youtube_channel: Optional YouTube channel for video analysis.
            news_weight: Weight for news sentiment (0-1).
            youtube_weight: Weight for YouTube sentiment (0-1).
            news_limit: Maximum news articles.
            youtube_videos: Maximum YouTube videos.

        Returns:
            Combined sentiment analysis.
        """
        # Get news sentiment
        news_result = await self.analyze_news_sentiment(
            symbol=symbol,
            market=market,
            news_limit=news_limit,
        )

        # Get YouTube sentiment if channel provided
        youtube_result = None
        if youtube_channel:
            youtube_result = await self.analyze_youtube_sentiment(
                channel=youtube_channel,
                topic=f"{symbol} stock analysis",
                max_videos=youtube_videos,
            )

        # If no YouTube, use only news
        if not youtube_result or not youtube_result.get("success"):
            return {
                **news_result,
                "combined": False,
                "sources": ["news"],
            }

        # Calculate combined sentiment
        news_score = news_result.get("sentiment_score", 0.5)
        youtube_score = youtube_result.get("sentiment_score", 0.5)

        # Normalize weights
        total_weight = news_weight + youtube_weight
        news_weight = news_weight / total_weight
        youtube_weight = youtube_weight / total_weight

        combined_score = (news_score * news_weight) + (youtube_score * youtube_weight)

        # Get combined analysis from LLM
        news_sentiment_summary = f"""
Score: {news_score:.2f}
Label: {news_result.get('sentiment_label', 'Neutral')}
Key Themes: {', '.join(news_result.get('key_themes', []))}
Summary: {news_result.get('summary', 'N/A')}
"""

        youtube_sentiment_summary = f"""
Score: {youtube_score:.2f}
Label: {youtube_result.get('sentiment_label', 'Neutral')}
Key Themes: {', '.join(youtube_result.get('key_themes', []))}
Summary: {youtube_result.get('summary', 'N/A')}
"""

        messages = [
            {"role": "system", "content": SENTIMENT_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": COMBINED_ANALYSIS_TEMPLATE.format(
                    symbol=symbol,
                    news_sentiment=news_sentiment_summary,
                    youtube_sentiment=youtube_sentiment_summary,
                    news_weight=int(news_weight * 100),
                    youtube_weight=int(youtube_weight * 100),
                ),
            },
        ]

        response = await self.call_llm(messages)
        combined_result = self._parse_sentiment_response(response)

        # Override with weighted score
        combined_result["sentiment_score"] = combined_score
        combined_result["sentiment_label"] = self._score_to_label(combined_score)

        return {
            "success": True,
            "combined": True,
            "symbol": symbol,
            "sources": ["news", "youtube"],
            "news_sentiment": {
                "score": news_score,
                "label": news_result.get("sentiment_label"),
                "articles": news_result.get("articles_analyzed", 0),
            },
            "youtube_sentiment": {
                "score": youtube_score,
                "label": youtube_result.get("sentiment_label"),
                "videos": youtube_result.get("videos_analyzed", 0),
            },
            "weights": {
                "news": news_weight,
                "youtube": youtube_weight,
            },
            **combined_result,
        }

    async def process(
        self,
        symbol: str | None = None,
        market: str = "US",
        video_url: str | None = None,
        youtube_channel: str | None = None,
        source: str = "combined",
        **kwargs,
    ) -> dict[str, Any]:
        """Process sentiment analysis request.

        Args:
            symbol: Stock symbol for news analysis.
            market: Market code.
            video_url: Specific YouTube video URL.
            youtube_channel: YouTube channel for video analysis.
            source: 'news', 'youtube', or 'combined'.
            **kwargs: Additional parameters.

        Returns:
            Sentiment analysis results.
        """
        if source == "news" and symbol:
            return await self.analyze_news_sentiment(symbol, market, **kwargs)
        elif source == "youtube":
            return await self.analyze_youtube_sentiment(
                video_url_or_id=video_url,
                channel=youtube_channel,
                topic=symbol,
                **kwargs,
            )
        elif source == "combined" and symbol:
            return await self.analyze_combined_sentiment(
                symbol=symbol,
                market=market,
                youtube_channel=youtube_channel,
                **kwargs,
            )
        else:
            return {
                "success": False,
                "error": "Invalid parameters. Provide symbol for news/combined or video_url/youtube_channel for youtube.",
            }

    def _format_news_for_analysis(self, news: list[dict]) -> str:
        """Format news articles for LLM analysis."""
        parts = []
        for i, article in enumerate(news, 1):
            parts.append(f"""
Article {i}:
Title: {article.get('title', 'N/A')}
Source: {article.get('source', 'N/A')}
Date: {article.get('date', 'N/A')}
Summary: {article.get('summary', 'N/A')}
""")
        return "\n".join(parts)

    def _parse_sentiment_response(self, response: str) -> dict[str, Any]:
        """Parse LLM sentiment response."""
        import json

        try:
            # Try to extract JSON from response
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

            # Ensure required fields
            return {
                "sentiment_score": result.get("sentiment_score", 0.5),
                "sentiment_label": result.get("sentiment_label", "Neutral"),
                "confidence": result.get("confidence", 0.5),
                "key_themes": result.get("key_themes", []),
                "positive_factors": result.get("positive_factors", []),
                "negative_factors": result.get("negative_factors", []),
                "market_implications": result.get("market_implications", ""),
                "summary": result.get("summary", ""),
            }

        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Failed to parse sentiment response: {e}")
            return {
                "sentiment_score": 0.5,
                "sentiment_label": "Neutral",
                "confidence": 0.3,
                "key_themes": [],
                "positive_factors": [],
                "negative_factors": [],
                "market_implications": "",
                "summary": response[:500] if response else "",
            }

    def _aggregate_sentiments(self, results: list[dict]) -> dict[str, Any]:
        """Aggregate multiple sentiment results."""
        if not results:
            return {
                "sentiment_score": 0.5,
                "sentiment_label": "Neutral",
            }

        # Calculate weighted average (by confidence)
        total_weight = 0
        weighted_score = 0
        all_themes = []
        all_positive = []
        all_negative = []

        for r in results:
            confidence = r.get("confidence", 0.5)
            score = r.get("sentiment_score", 0.5)
            weighted_score += score * confidence
            total_weight += confidence

            all_themes.extend(r.get("key_themes", []))
            all_positive.extend(r.get("positive_factors", []))
            all_negative.extend(r.get("negative_factors", []))

        avg_score = weighted_score / total_weight if total_weight > 0 else 0.5

        # Deduplicate themes
        unique_themes = list(dict.fromkeys(all_themes))[:5]
        unique_positive = list(dict.fromkeys(all_positive))[:5]
        unique_negative = list(dict.fromkeys(all_negative))[:5]

        return {
            "sentiment_score": avg_score,
            "sentiment_label": self._score_to_label(avg_score),
            "confidence": total_weight / len(results) if results else 0.5,
            "key_themes": unique_themes,
            "positive_factors": unique_positive,
            "negative_factors": unique_negative,
            "market_implications": "",
            "summary": f"Aggregated sentiment from {len(results)} videos",
        }

    def _score_to_label(self, score: float) -> str:
        """Convert sentiment score to label."""
        if score >= 0.8:
            return "Very Bullish"
        elif score >= 0.5:
            return "Bullish"
        elif score >= 0.3:
            return "Neutral"
        elif score >= 0.1:
            return "Bearish"
        else:
            return "Very Bearish"
