"""Test Phase 5 Agents: Sentiment, Valuation, Recommend."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from src.agents.sentiment import SentimentAgent
from src.agents.valuation import ValuationAgent
from src.agents.recommend import RecommendAgent


class TestSentimentAgent:
    """Test SentimentAgent functionality."""

    def test_init(self):
        """Test agent initialization."""
        agent = SentimentAgent()
        assert agent.temperature == 0.3

    def test_score_to_label(self):
        """Test sentiment score to label conversion."""
        agent = SentimentAgent()

        assert agent._score_to_label(0.9) == "Very Bullish"
        assert agent._score_to_label(0.6) == "Bullish"
        assert agent._score_to_label(0.4) == "Neutral"
        assert agent._score_to_label(0.2) == "Bearish"
        assert agent._score_to_label(0.05) == "Very Bearish"

    def test_aggregate_sentiments(self):
        """Test sentiment aggregation."""
        agent = SentimentAgent()

        results = [
            {"sentiment_score": 0.8, "confidence": 0.9, "key_themes": ["growth"]},
            {"sentiment_score": 0.6, "confidence": 0.7, "key_themes": ["risk"]},
        ]

        aggregated = agent._aggregate_sentiments(results)

        assert 0.6 < aggregated["sentiment_score"] < 0.8
        assert "growth" in aggregated["key_themes"]
        assert "risk" in aggregated["key_themes"]

    @pytest.mark.asyncio
    async def test_analyze_news_no_results(self):
        """Test news sentiment with no news."""
        agent = SentimentAgent()

        with patch("src.agents.sentiment.agent.search_news", new_callable=AsyncMock) as mock_search:
            mock_search.return_value = []

            result = await agent.analyze_news_sentiment("AAPL", "US")

            assert result["success"] is False
            assert "No news" in result.get("error", "")


class TestValuationAgent:
    """Test ValuationAgent functionality."""

    def test_init(self):
        """Test agent initialization."""
        agent = ValuationAgent()
        assert agent.temperature == 0.2

    def test_industry_multiples(self):
        """Test industry multiples are defined."""
        assert "Technology" in ValuationAgent.INDUSTRY_MULTIPLES
        assert "Financial Services" in ValuationAgent.INDUSTRY_MULTIPLES
        assert "default" in ValuationAgent.INDUSTRY_MULTIPLES

    def test_format_number(self):
        """Test number formatting."""
        agent = ValuationAgent()

        assert "T" in agent._format_number(1_500_000_000_000)
        assert "B" in agent._format_number(1_500_000_000)
        assert "M" in agent._format_number(1_500_000)
        assert agent._format_number(None) == "N/A"

    def test_format_percent(self):
        """Test percentage formatting."""
        agent = ValuationAgent()

        assert "%" in agent._format_percent(0.15)
        assert agent._format_percent(None) == "N/A"

    @pytest.mark.asyncio
    async def test_quick_valuation(self):
        """Test quick valuation with mocked data."""
        agent = ValuationAgent()

        mock_info = {
            "name": "Apple Inc.",
            "sector": "Technology",
            "current_price": 150.0,
            "pe_ratio": 25.0,
            "pb_ratio": 10.0,
            "52_week_high": 180.0,
            "52_week_low": 120.0,
        }

        mock_ratios = {}

        with patch("src.agents.valuation.agent.get_stock_info", new_callable=AsyncMock) as mock_stock:
            with patch("src.agents.valuation.agent.get_financial_ratios", new_callable=AsyncMock) as mock_fin:
                mock_stock.return_value = mock_info
                mock_fin.return_value = mock_ratios

                result = await agent.quick_valuation("AAPL", "US")

                assert result["success"] is True
                assert result["symbol"] == "AAPL"
                assert "fair_value_base" in result
                assert "recommendation" in result


class TestRecommendAgent:
    """Test RecommendAgent functionality."""

    def test_init(self):
        """Test agent initialization."""
        agent = RecommendAgent()
        assert agent.temperature == 0.3
        assert agent._technical_agent is not None
        assert agent._fundamental_agent is not None
        assert agent._sentiment_agent is not None
        assert agent._valuation_agent is not None

    def test_style_weights(self):
        """Test investment style weights."""
        assert "growth" in RecommendAgent.STYLE_WEIGHTS
        assert "value" in RecommendAgent.STYLE_WEIGHTS
        assert "momentum" in RecommendAgent.STYLE_WEIGHTS
        assert "balanced" in RecommendAgent.STYLE_WEIGHTS

        # Check weights sum to 1
        for style, weights in RecommendAgent.STYLE_WEIGHTS.items():
            total = sum(weights.values())
            assert abs(total - 1.0) < 0.01, f"{style} weights don't sum to 1"

    def test_calculate_overall_score(self):
        """Test overall score calculation."""
        agent = RecommendAgent()

        analyses = {
            "valuation": {
                "upside_potential": 20,  # Should give ~80 score
            },
            "sentiment": {
                "sentiment_score": 0.7,  # Should give 70 score
            },
        }

        weights = {"valuation": 0.5, "sentiment": 0.5, "technical": 0, "fundamental": 0}

        score = agent._calculate_overall_score(analyses, weights)

        # Should be around (80 + 70) / 2 = 75
        assert 70 < score < 80

    @pytest.mark.asyncio
    async def test_quick_recommend(self):
        """Test quick recommendation."""
        agent = RecommendAgent()

        mock_valuation = {
            "success": True,
            "current_price": 150.0,
            "fair_value_base": 180.0,
            "upside_potential": 20.0,
            "valuation_status": "Undervalued",
        }

        with patch.object(agent._valuation_agent, "quick_valuation", new_callable=AsyncMock) as mock:
            mock.return_value = mock_valuation

            result = await agent.quick_recommend("AAPL", "US")

            assert result["success"] is True
            assert result["symbol"] == "AAPL"
            assert result["recommendation"] in ["Strong Buy", "Buy", "Hold", "Sell", "Strong Sell"]


class TestAPIEndpoints:
    """Test API endpoint models and structure."""

    def test_request_models_import(self):
        """Test that request models can be imported."""
        from src.api.routers.analysis import (
            SentimentAnalysisRequest,
            ValuationRequest,
            RecommendationRequest,
        )

        # Test default values
        sentiment_req = SentimentAnalysisRequest()
        assert sentiment_req.market == "US"
        assert sentiment_req.source == "combined"

        valuation_req = ValuationRequest()
        assert valuation_req.quick is True

        recommend_req = RecommendationRequest()
        assert recommend_req.investment_style == "balanced"
        assert recommend_req.time_horizon == "medium"

    def test_response_models_import(self):
        """Test that response models can be imported."""
        from src.api.routers.analysis import (
            SentimentResponse,
            ValuationResponse,
            RecommendationResponse,
        )

        # Test basic instantiation
        sentiment_resp = SentimentResponse(success=True, source="news")
        assert sentiment_resp.success is True

        valuation_resp = ValuationResponse(success=True, market="US")
        assert valuation_resp.success is True

        recommend_resp = RecommendationResponse(success=True, market="US")
        assert recommend_resp.success is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
