"""Test Research Pipeline with ToolRouter integration."""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from src.agents.research.agents.research_agent import (
    ResearchAgent,
    TOOL_NAME_TO_ROUTER_TYPE,
)
from src.agents.research.pipeline import ResearchPipeline
from src.agents.research.data_structures import TopicBlock, TopicStatus
from src.services.tool_router import ToolResult, ToolStatus


class TestResearchAgentToolRouter:
    """Test ResearchAgent with ToolRouter integration."""

    def test_tool_name_mapping(self):
        """Test tool name to router type mapping."""
        # Verify mapping exists for common tools
        assert TOOL_NAME_TO_ROUTER_TYPE["stock_data"] == "stock_price"
        assert TOOL_NAME_TO_ROUTER_TYPE["financials"] == "financial_ratios"
        assert TOOL_NAME_TO_ROUTER_TYPE["web_search"] == "web_search"
        assert TOOL_NAME_TO_ROUTER_TYPE["news_search"] == "news_search"
        assert TOOL_NAME_TO_ROUTER_TYPE["rag_search"] == "rag_search"
        assert TOOL_NAME_TO_ROUTER_TYPE["youtube"] == "youtube_transcript"
        assert TOOL_NAME_TO_ROUTER_TYPE["technical_analysis"] == "technical_indicators"

    @pytest.mark.asyncio
    async def test_execute_tool_via_router(self):
        """Test tool execution via ToolRouter."""
        # Mock ToolRouter
        mock_router = MagicMock()
        mock_result = ToolResult(
            tool_type="stock_price",
            status=ToolStatus.SUCCESS,
            data={"price": 150.0, "symbol": "AAPL"},
            query={"symbol": "AAPL", "market": "US"},
            execution_time=0.5,
            retries=0,
        )
        mock_router.execute = AsyncMock(return_value=mock_result)

        with patch(
            "src.agents.research.agents.research_agent.get_tool_router",
            return_value=mock_router,
        ):
            agent = ResearchAgent(use_tool_router=True)

            # Execute tool
            result_str, router_result = await agent._execute_tool_via_router(
                "stock_data", "AAPL", ["AAPL"]
            )

            # Verify router was called
            mock_router.execute.assert_called_once()
            call_args = mock_router.execute.call_args

            # Check tool type mapping
            assert call_args[0][0] == "stock_price"

            # Check result
            assert router_result is not None
            assert router_result.is_success
            assert "AAPL" in result_str or "150" in result_str

    @pytest.mark.asyncio
    async def test_execute_tool_legacy_fallback(self):
        """Test legacy tool handler fallback."""
        # Create agent without ToolRouter
        agent = ResearchAgent(use_tool_router=False)

        # Register a mock handler
        mock_handler = AsyncMock(return_value={"test": "data"})
        agent.register_tool("custom_tool", mock_handler, "Custom tool")

        # Execute tool
        result_str, router_result = await agent._execute_tool_legacy(
            "custom_tool", "test query", None
        )

        # Verify handler was called
        mock_handler.assert_called_once()

        # Router result should be None for legacy execution
        assert router_result is None
        assert "test" in result_str

    def test_build_router_args_stock_price(self):
        """Test router args building for stock_price."""
        with patch(
            "src.agents.research.agents.research_agent.get_tool_router"
        ):
            agent = ResearchAgent(use_tool_router=True)

            # US stock
            args = agent._build_router_args("stock_price", "AAPL", ["AAPL"])
            assert args["symbol"] == "AAPL"
            assert args["market"] == "US"
            assert args["period"] == "1mo"

            # Korean stock (6-digit number)
            args = agent._build_router_args("stock_price", "005930", ["005930"])
            assert args["symbol"] == "005930"
            assert args["market"] == "KR"

    def test_build_router_args_news_search(self):
        """Test router args building for news_search."""
        with patch(
            "src.agents.research.agents.research_agent.get_tool_router"
        ):
            agent = ResearchAgent(use_tool_router=True)

            args = agent._build_router_args("news_search", "Apple earnings", None)
            assert args["query"] == "Apple earnings"
            assert args["limit"] == 10


class TestResearchPipelineToolRouter:
    """Test ResearchPipeline with ToolRouter integration."""

    def test_pipeline_init_with_tool_router(self):
        """Test pipeline initializes with ToolRouter by default."""
        with patch(
            "src.agents.research.agents.research_agent.get_tool_router"
        ):
            pipeline = ResearchPipeline()
            assert pipeline.use_tool_router is True

    def test_pipeline_init_without_tool_router(self):
        """Test pipeline can be initialized without ToolRouter."""
        pipeline = ResearchPipeline(use_tool_router=False)
        assert pipeline.use_tool_router is False

    def test_register_tool_with_router_enabled(self):
        """Test tool registration logs warning when router enabled."""
        with patch(
            "src.agents.research.agents.research_agent.get_tool_router"
        ):
            pipeline = ResearchPipeline(use_tool_router=True)

            # Register a custom tool
            mock_handler = AsyncMock()
            pipeline.register_tool("custom_tool", mock_handler, "Custom tool")

            # Handler should still be registered
            assert "custom_tool" in pipeline._tool_handlers


class TestToolTraceWithRouterMetadata:
    """Test ToolTrace includes router execution metadata."""

    def test_create_tool_trace_with_router_result(self):
        """Test tool trace includes router metadata."""
        with patch(
            "src.agents.research.agents.research_agent.get_tool_router"
        ):
            agent = ResearchAgent(use_tool_router=True)

            # Create mock router result
            router_result = ToolResult(
                tool_type="stock_price",
                status=ToolStatus.SUCCESS,
                data={"price": 150.0},
                query={"symbol": "AAPL"},
                execution_time=0.5,
                retries=1,
            )

            trace = agent._create_tool_trace(
                block_id="block_1",
                tool_name="stock_data",
                query="AAPL",
                raw_answer="Price: 150.0",
                summary="Got stock price",
                router_result=router_result,
            )

            # Check router metadata
            assert "router" in trace.metadata
            assert trace.metadata["router"]["status"] == "success"
            assert trace.metadata["router"]["retries"] == 1
            assert trace.metadata["router"]["execution_time"] == 0.5

    def test_create_tool_trace_without_router_result(self):
        """Test tool trace without router metadata."""
        with patch(
            "src.agents.research.agents.research_agent.get_tool_router"
        ):
            agent = ResearchAgent(use_tool_router=True)

            trace = agent._create_tool_trace(
                block_id="block_1",
                tool_name="custom_tool",
                query="test",
                raw_answer="Result",
                summary="Got result",
                router_result=None,
            )

            # No router metadata
            assert "router" not in trace.metadata
            assert "block_id" in trace.metadata


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
