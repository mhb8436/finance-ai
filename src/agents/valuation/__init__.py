"""Valuation Agent.

Calculates fair value using multiple valuation methods.

Example:
    from src.agents.valuation import ValuationAgent

    agent = ValuationAgent()

    # Full valuation analysis
    result = await agent.calculate_fair_value("AAPL", market="US")

    # Quick valuation
    result = await agent.quick_valuation("005930", market="KR")

    # Compare multiple stocks
    result = await agent.compare_valuations(["AAPL", "MSFT", "GOOGL"])
"""

from .agent import ValuationAgent

__all__ = ["ValuationAgent"]
