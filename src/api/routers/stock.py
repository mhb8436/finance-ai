"""Stock data API endpoints."""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from src.tools.stock_data import get_stock_price, get_stock_info, search_stocks

router = APIRouter()


class StockPriceResponse(BaseModel):
    symbol: str
    market: str
    data: list[dict]


class StockInfoResponse(BaseModel):
    symbol: str
    name: str
    market: str
    sector: str | None
    industry: str | None
    market_cap: float | None
    current_price: float | None = None
    pe_ratio: float | None
    pb_ratio: float | None
    dividend_yield: float | None
    high_52_week: float | None = None
    low_52_week: float | None = None
    avg_volume: int | None = None

    model_config = {"extra": "ignore"}


@router.get("/price/{symbol}")
async def get_price(
    symbol: str,
    market: str = Query("US", description="Market: US, KR"),
    period: str = Query("1mo", description="Period: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, max"),
    interval: str = Query("1d", description="Interval: 1m, 5m, 15m, 30m, 1h, 1d, 1wk, 1mo"),
) -> StockPriceResponse:
    """Get stock price data."""
    try:
        data = await get_stock_price(symbol, market, period, interval)
        return StockPriceResponse(symbol=symbol, market=market, data=data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/info/{symbol}")
async def get_info(
    symbol: str,
    market: str = Query("US", description="Market: US, KR"),
) -> StockInfoResponse:
    """Get stock information."""
    try:
        info = await get_stock_info(symbol, market)
        # Map field names from stock_data to response model
        return StockInfoResponse(
            symbol=info.get("symbol", symbol),
            name=info.get("name", "Unknown"),
            market=info.get("market", market),
            sector=info.get("sector"),
            industry=info.get("industry"),
            market_cap=info.get("market_cap"),
            current_price=info.get("current_price"),
            pe_ratio=info.get("pe_ratio"),
            pb_ratio=info.get("pb_ratio"),
            dividend_yield=info.get("dividend_yield"),
            high_52_week=info.get("52_week_high"),
            low_52_week=info.get("52_week_low"),
            avg_volume=info.get("avg_volume"),
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/search")
async def search(
    query: str = Query(..., description="Search query"),
    market: str = Query("US", description="Market: US, KR, ALL"),
    limit: int = Query(10, description="Max results"),
) -> list[dict]:
    """Search for stocks by name or symbol."""
    try:
        results = await search_stocks(query, market, limit)
        return results
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
