"""Intent Analyzer Service.

Analyzes user queries to detect intent and extract stock symbols.

Example:
    from src.services.intent_analyzer import get_intent_analyzer

    analyzer = get_intent_analyzer()
    intent = analyzer.analyze("삼성전자 주가 알려줘")

    print(intent.intent_type)  # IntentType.STOCK_QUERY
    print(intent.symbols)  # [ExtractedSymbol(symbol="005930", market=KR)]
    print(intent.suggested_tools)  # ["stock_price", "stock_info", "news_search"]
"""

from .types import (
    IntentType,
    MarketType,
    ExtractedSymbol,
    QueryIntent,
    INTENT_TOOL_MAP,
)
from .analyzer import IntentAnalyzer, get_intent_analyzer

__all__ = [
    "IntentType",
    "MarketType",
    "ExtractedSymbol",
    "QueryIntent",
    "INTENT_TOOL_MAP",
    "IntentAnalyzer",
    "get_intent_analyzer",
]
