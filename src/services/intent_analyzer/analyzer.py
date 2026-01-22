"""Intent Analyzer - Query intent detection and symbol extraction.

Analyzes user queries to determine:
1. Intent type (stock query, news, analysis, etc.)
2. Mentioned stock symbols
3. Suggested tools for pre-fetching
"""

import logging
import re
from typing import Any

from .types import (
    ExtractedSymbol,
    IntentType,
    MarketType,
    QueryIntent,
    INTENT_TOOL_MAP,
)

logger = logging.getLogger(__name__)

# 한국 주요 종목 매핑 (이름 → 코드)
KR_COMPANY_MAP: dict[str, str] = {
    # 대형주
    "삼성전자": "005930",
    "삼성": "005930",
    "samsung": "005930",
    "SK하이닉스": "000660",
    "하이닉스": "000660",
    "LG에너지솔루션": "373220",
    "LG에너지": "373220",
    "현대차": "005380",
    "현대자동차": "005380",
    "기아": "000270",
    "기아차": "000270",
    "셀트리온": "068270",
    "카카오": "035720",
    "네이버": "035420",
    "NAVER": "035420",
    "LG화학": "051910",
    "포스코홀딩스": "005490",
    "포스코": "005490",
    "삼성SDI": "006400",
    "삼성바이오로직스": "207940",
    "삼성바이오": "207940",
    "KB금융": "105560",
    "신한지주": "055550",
    "카카오뱅크": "323410",
    "토스뱅크": "000000",  # 비상장
    "현대모비스": "012330",
    "LG전자": "066570",
    "SK텔레콤": "017670",
    "SK": "034730",
    "KT": "030200",
    "하나금융": "086790",
    "우리금융": "316140",
    "롯데케미칼": "011170",
    "삼성물산": "028260",
    "엔씨소프트": "036570",
    "크래프톤": "259960",
    "두산에너빌리티": "034020",
    # 더 많은 종목 추가 가능
}

# 미국 주요 종목 매핑 (이름 → 티커)
US_COMPANY_MAP: dict[str, str] = {
    "apple": "AAPL",
    "애플": "AAPL",
    "microsoft": "MSFT",
    "마이크로소프트": "MSFT",
    "google": "GOOGL",
    "구글": "GOOGL",
    "alphabet": "GOOGL",
    "amazon": "AMZN",
    "아마존": "AMZN",
    "meta": "META",
    "메타": "META",
    "facebook": "META",
    "페이스북": "META",
    "tesla": "TSLA",
    "테슬라": "TSLA",
    "nvidia": "NVDA",
    "엔비디아": "NVDA",
    "amd": "AMD",
    "netflix": "NFLX",
    "넷플릭스": "NFLX",
    "disney": "DIS",
    "디즈니": "DIS",
    "intel": "INTC",
    "인텔": "INTC",
    "qualcomm": "QCOM",
    "퀄컴": "QCOM",
    "broadcom": "AVGO",
    "tsmc": "TSM",
    "taiwan semiconductor": "TSM",
    "jp morgan": "JPM",
    "jpmorgan": "JPM",
    "goldman sachs": "GS",
    "bank of america": "BAC",
    "visa": "V",
    "mastercard": "MA",
    "paypal": "PYPL",
    "salesforce": "CRM",
    "oracle": "ORCL",
    "오라클": "ORCL",
    "ibm": "IBM",
    "cisco": "CSCO",
    "시스코": "CSCO",
    "adobe": "ADBE",
    "어도비": "ADBE",
    "spotify": "SPOT",
    "uber": "UBER",
    "우버": "UBER",
    "airbnb": "ABNB",
    "에어비앤비": "ABNB",
    "berkshire": "BRK-B",
    "coca cola": "KO",
    "코카콜라": "KO",
    "pepsi": "PEP",
    "펩시": "PEP",
    "johnson": "JNJ",
    "pfizer": "PFE",
    "화이자": "PFE",
    "moderna": "MRNA",
    "모더나": "MRNA",
    "walmart": "WMT",
    "월마트": "WMT",
    "costco": "COST",
    "코스트코": "COST",
    "starbucks": "SBUX",
    "스타벅스": "SBUX",
    "mcdonald": "MCD",
    "맥도날드": "MCD",
    "boeing": "BA",
    "보잉": "BA",
    "exxon": "XOM",
    "엑슨": "XOM",
    "chevron": "CVX",
    # 더 많은 종목 추가 가능
}

# 의도 감지 패턴
INTENT_PATTERNS: dict[IntentType, list[str]] = {
    IntentType.STOCK_QUERY: [
        r"주가", r"시세", r"가격", r"현재가", r"종가", r"시가", r"stock price",
        r"price", r"quote", r"얼마", r"몇\s*원", r"몇\s*달러", r"how much",
    ],
    IntentType.NEWS_QUERY: [
        r"뉴스", r"소식", r"기사", r"news", r"최근", r"recent", r"latest",
        r"무슨\s*일", r"이슈", r"what happened", r"what's happening",
    ],
    IntentType.ANALYSIS_QUERY: [
        r"분석", r"전망", r"예측", r"analysis", r"forecast", r"predict",
        r"RSI", r"MACD", r"이동평균", r"볼린저", r"기술적", r"technical",
        r"PER", r"PBR", r"ROE", r"재무", r"financial", r"fundamental",
        r"실적", r"매출", r"영업이익", r"순이익", r"earnings",
    ],
    IntentType.COMPARISON_QUERY: [
        r"비교", r"compare", r"vs", r"versus", r"차이", r"difference",
        r"어떤\s*게\s*나", r"뭐가\s*나", r"which", r"better",
    ],
}

# 시간 범위 패턴
TIME_PATTERNS: dict[str, list[str]] = {
    "1d": [r"오늘", r"today", r"당일"],
    "1w": [r"이번\s*주", r"이번주", r"일주일", r"1주", r"this week", r"week"],
    "1mo": [r"이번\s*달", r"한\s*달", r"1개월", r"1달", r"this month", r"month"],
    "3mo": [r"3개월", r"분기", r"quarter"],
    "6mo": [r"6개월", r"반년", r"half year"],
    "1y": [r"1년", r"올해", r"연간", r"year", r"annual"],
}


class IntentAnalyzer:
    """Analyze user queries to detect intent and extract symbols."""

    def __init__(self) -> None:
        """Initialize IntentAnalyzer."""
        # Compile regex patterns for performance
        self._intent_patterns: dict[IntentType, list[re.Pattern]] = {}
        for intent, patterns in INTENT_PATTERNS.items():
            self._intent_patterns[intent] = [
                re.compile(p, re.IGNORECASE) for p in patterns
            ]

        self._time_patterns: dict[str, list[re.Pattern]] = {}
        for time_range, patterns in TIME_PATTERNS.items():
            self._time_patterns[time_range] = [
                re.compile(p, re.IGNORECASE) for p in patterns
            ]

        # US ticker pattern (1-5 uppercase letters)
        self._us_ticker_pattern = re.compile(r"\b([A-Z]{1,5})\b")

        # KR code pattern (6 digits)
        self._kr_code_pattern = re.compile(r"\b(\d{6})\b")

    def analyze(self, query: str) -> QueryIntent:
        """Analyze user query to detect intent and extract symbols.

        Args:
            query: User's query string.

        Returns:
            QueryIntent with detected intent, symbols, and suggested tools.
        """
        # Detect language
        language = self._detect_language(query)

        # Extract symbols
        symbols = self._extract_symbols(query)

        # Detect intent
        intent_type, confidence = self._detect_intent(query, symbols)

        # Detect time range
        time_range = self._detect_time_range(query)

        # Extract keywords
        keywords = self._extract_keywords(query, symbols)

        # Get suggested tools based on intent
        suggested_tools = INTENT_TOOL_MAP.get(intent_type, []).copy()

        return QueryIntent(
            intent_type=intent_type,
            confidence=confidence,
            symbols=symbols,
            keywords=keywords,
            time_range=time_range,
            language=language,
            suggested_tools=suggested_tools,
        )

    def _detect_language(self, query: str) -> str:
        """Detect query language (ko or en)."""
        # Count Korean characters
        korean_chars = len(re.findall(r"[가-힣]", query))
        total_chars = len(re.findall(r"[a-zA-Z가-힣]", query))

        if total_chars == 0:
            return "ko"

        korean_ratio = korean_chars / total_chars
        return "ko" if korean_ratio > 0.3 else "en"

    def _extract_symbols(self, query: str) -> list[ExtractedSymbol]:
        """Extract stock symbols from query."""
        symbols: list[ExtractedSymbol] = []
        seen_symbols: set[str] = set()  # Track seen symbols to avoid duplicates
        query_lower = query.lower()

        # 1. Check Korean company names (longer names first to avoid partial matches)
        kr_names_sorted = sorted(KR_COMPANY_MAP.items(), key=lambda x: len(x[0]), reverse=True)
        for name, code in kr_names_sorted:
            if name.lower() in query_lower:
                # Skip if code already added
                if code not in seen_symbols:
                    symbols.append(ExtractedSymbol(
                        symbol=code,
                        market=MarketType.KR,
                        company_name=name,
                        confidence=0.95,
                    ))
                    seen_symbols.add(code)

        # 2. Check US company names (longer names first)
        us_names_sorted = sorted(US_COMPANY_MAP.items(), key=lambda x: len(x[0]), reverse=True)
        for name, ticker in us_names_sorted:
            if name.lower() in query_lower:
                # Skip if already added (avoid duplicates)
                if ticker not in seen_symbols:
                    symbols.append(ExtractedSymbol(
                        symbol=ticker,
                        market=MarketType.US,
                        company_name=name,
                        confidence=0.95,
                    ))
                    seen_symbols.add(ticker)

        # 3. Extract US tickers (uppercase letters, 1-5 chars)
        us_tickers = self._us_ticker_pattern.findall(query)
        for ticker in us_tickers:
            # Skip common words
            if ticker in {"A", "I", "IT", "AI", "US", "KR", "UK", "EU", "THE", "AND", "FOR", "OR", "IS", "BE", "TO", "IN", "ON", "AT"}:
                continue
            # Skip if already added
            if ticker not in seen_symbols:
                symbols.append(ExtractedSymbol(
                    symbol=ticker,
                    market=MarketType.US,
                    confidence=0.7,  # Lower confidence for raw ticker extraction
                ))
                seen_symbols.add(ticker)

        # 4. Extract Korean stock codes (6 digits)
        kr_codes = self._kr_code_pattern.findall(query)
        for code in kr_codes:
            # Skip if already added
            if code not in seen_symbols:
                symbols.append(ExtractedSymbol(
                    symbol=code,
                    market=MarketType.KR,
                    confidence=0.9,
                ))
                seen_symbols.add(code)

        return symbols

    def _detect_intent(
        self, query: str, symbols: list[ExtractedSymbol]
    ) -> tuple[IntentType, float]:
        """Detect query intent.

        Args:
            query: User query.
            symbols: Extracted symbols.

        Returns:
            Tuple of (IntentType, confidence).
        """
        intent_scores: dict[IntentType, float] = {
            intent: 0.0 for intent in IntentType
        }

        # Check each intent pattern
        for intent, patterns in self._intent_patterns.items():
            for pattern in patterns:
                if pattern.search(query):
                    intent_scores[intent] += 1.0

        # Find highest scoring intent
        max_intent = IntentType.GENERAL_QUERY
        max_score = 0.0

        for intent, score in intent_scores.items():
            if score > max_score:
                max_score = score
                max_intent = intent

        # If no intent detected but symbols found, default to STOCK_QUERY
        if max_score == 0.0 and symbols:
            max_intent = IntentType.STOCK_QUERY
            max_score = 0.5

        # Calculate confidence (normalized)
        confidence = min(max_score / 3.0, 1.0) if max_score > 0 else 0.3

        return max_intent, confidence

    def _detect_time_range(self, query: str) -> str | None:
        """Detect time range from query."""
        for time_range, patterns in self._time_patterns.items():
            for pattern in patterns:
                if pattern.search(query):
                    return time_range
        return None

    def _extract_keywords(
        self, query: str, symbols: list[ExtractedSymbol]
    ) -> list[str]:
        """Extract relevant keywords from query."""
        keywords: list[str] = []

        # Add symbol names as keywords
        for symbol in symbols:
            if symbol.company_name:
                keywords.append(symbol.company_name)
            keywords.append(symbol.symbol)

        # Extract other meaningful words (simplified)
        # In production, you might use NLP tokenization
        meaningful_words = re.findall(r"[가-힣]{2,}|[a-zA-Z]{3,}", query)
        for word in meaningful_words:
            word_lower = word.lower()
            # Skip common words
            if word_lower not in {"the", "and", "for", "주식", "종목", "회사", "stock", "company"}:
                if word not in keywords:
                    keywords.append(word)

        return keywords[:10]  # Limit to 10 keywords


# Global instance
_intent_analyzer: IntentAnalyzer | None = None


def get_intent_analyzer() -> IntentAnalyzer:
    """Get or create global IntentAnalyzer instance."""
    global _intent_analyzer

    if _intent_analyzer is None:
        _intent_analyzer = IntentAnalyzer()

    return _intent_analyzer
