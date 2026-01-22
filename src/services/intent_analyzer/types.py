"""Intent Analyzer Types."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class IntentType(str, Enum):
    """User query intent types."""
    STOCK_QUERY = "stock_query"  # 주가 조회, 종목 정보
    NEWS_QUERY = "news_query"  # 뉴스 검색, 최근 소식
    ANALYSIS_QUERY = "analysis_query"  # 기술적/기본적 분석
    COMPARISON_QUERY = "comparison_query"  # 종목 비교
    GENERAL_QUERY = "general_query"  # 일반 질문 (데이터 조회 불필요)


class MarketType(str, Enum):
    """Market types."""
    US = "US"
    KR = "KR"
    UNKNOWN = "UNKNOWN"


@dataclass
class ExtractedSymbol:
    """Extracted stock symbol from query."""
    symbol: str  # e.g., "AAPL", "005930"
    market: MarketType = MarketType.UNKNOWN
    company_name: str | None = None  # e.g., "Apple", "삼성전자"
    confidence: float = 1.0  # 0.0 ~ 1.0


@dataclass
class QueryIntent:
    """Analyzed query intent."""
    intent_type: IntentType
    confidence: float  # 0.0 ~ 1.0
    symbols: list[ExtractedSymbol] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)  # 추출된 키워드
    time_range: str | None = None  # e.g., "1d", "1w", "1mo"
    language: str = "ko"  # 쿼리 언어 (ko, en)

    # Pre-fetch 설정
    suggested_tools: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "intent_type": self.intent_type.value,
            "confidence": self.confidence,
            "symbols": [
                {
                    "symbol": s.symbol,
                    "market": s.market.value,
                    "company_name": s.company_name,
                    "confidence": s.confidence,
                }
                for s in self.symbols
            ],
            "keywords": self.keywords,
            "time_range": self.time_range,
            "language": self.language,
            "suggested_tools": self.suggested_tools,
        }


# 의도별 추천 도구 매핑
INTENT_TOOL_MAP: dict[IntentType, list[str]] = {
    IntentType.STOCK_QUERY: ["stock_price", "stock_info", "news_search"],
    IntentType.NEWS_QUERY: ["news_search", "web_search"],
    IntentType.ANALYSIS_QUERY: ["stock_price", "stock_info", "financial_ratios", "technical_indicators"],
    IntentType.COMPARISON_QUERY: ["stock_price", "stock_info", "financial_ratios"],
    IntentType.GENERAL_QUERY: [],
}
