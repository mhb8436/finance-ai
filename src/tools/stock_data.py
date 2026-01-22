"""Stock data fetching tools using yfinance and pykrx."""

from typing import Any


async def get_stock_price(
    symbol: str,
    market: str = "US",
    period: str = "1mo",
    interval: str = "1d",
) -> list[dict[str, Any]]:
    """Get historical stock price data.

    Args:
        symbol: Stock symbol (e.g., 'AAPL' for US, '005930' for KR)
        market: Market code ('US' or 'KR')
        period: Data period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, max)
        interval: Data interval (1m, 5m, 15m, 30m, 1h, 1d, 1wk, 1mo)

    Returns:
        List of price data dictionaries.
    """
    try:
        if market == "KR":
            return await _get_kr_stock_price(symbol, period, interval)
        else:
            return await _get_us_stock_price(symbol, period, interval)
    except Exception as e:
        print(f"Error fetching stock price for {symbol}: {e}")
        return []


async def _get_us_stock_price(
    symbol: str,
    period: str,
    interval: str,
) -> list[dict[str, Any]]:
    """Get US stock price using yfinance."""
    import yfinance as yf

    ticker = yf.Ticker(symbol)
    hist = ticker.history(period=period, interval=interval)

    if hist.empty:
        return []

    data = []
    for date, row in hist.iterrows():
        data.append({
            "date": date.strftime("%Y-%m-%d"),
            "open": round(row["Open"], 2),
            "high": round(row["High"], 2),
            "low": round(row["Low"], 2),
            "close": round(row["Close"], 2),
            "volume": int(row["Volume"]),
        })

    return data


async def _get_kr_stock_price(
    symbol: str,
    period: str,
    interval: str,
) -> list[dict[str, Any]]:
    """Get Korean stock price using pykrx."""
    from datetime import datetime, timedelta

    try:
        from pykrx import stock
    except ImportError:
        # Fallback to yfinance with .KS suffix
        return await _get_us_stock_price(f"{symbol}.KS", period, interval)

    # Convert period to date range
    end_date = datetime.now()
    period_days = {
        "1d": 1,
        "5d": 5,
        "1mo": 30,
        "3mo": 90,
        "6mo": 180,
        "1y": 365,
        "2y": 730,
        "5y": 1825,
        "max": 3650,
    }
    days = period_days.get(period, 30)
    start_date = end_date - timedelta(days=days)

    df = stock.get_market_ohlcv_by_date(
        start_date.strftime("%Y%m%d"),
        end_date.strftime("%Y%m%d"),
        symbol,
    )

    if df.empty:
        return []

    data = []
    for date, row in df.iterrows():
        data.append({
            "date": date.strftime("%Y-%m-%d"),
            "open": int(row["시가"]),
            "high": int(row["고가"]),
            "low": int(row["저가"]),
            "close": int(row["종가"]),
            "volume": int(row["거래량"]),
        })

    return data


async def get_stock_info(symbol: str, market: str = "US") -> dict[str, Any]:
    """Get stock information.

    Args:
        symbol: Stock symbol
        market: Market code

    Returns:
        Stock information dictionary.
    """
    try:
        if market == "KR":
            return await _get_kr_stock_info(symbol)
        else:
            return await _get_us_stock_info(symbol)
    except Exception as e:
        print(f"Error fetching stock info for {symbol}: {e}")
        return {
            "symbol": symbol,
            "name": "Unknown",
            "market": market,
            "sector": None,
            "industry": None,
            "market_cap": None,
            "pe_ratio": None,
            "pb_ratio": None,
            "dividend_yield": None,
        }


async def _get_us_stock_info(symbol: str) -> dict[str, Any]:
    """Get US stock info using yfinance."""
    import yfinance as yf

    ticker = yf.Ticker(symbol)
    info = ticker.info

    # Get current price from various possible fields
    current_price = (
        info.get("currentPrice")
        or info.get("regularMarketPrice")
        or info.get("previousClose")
    )

    return {
        "symbol": symbol,
        "name": info.get("longName", info.get("shortName", "Unknown")),
        "market": "US",
        "sector": info.get("sector"),
        "industry": info.get("industry"),
        "market_cap": info.get("marketCap"),
        "current_price": current_price,
        "pe_ratio": info.get("trailingPE"),
        "pb_ratio": info.get("priceToBook"),
        "dividend_yield": info.get("trailingAnnualDividendYield") or info.get("dividendYield"),
        "52_week_high": info.get("fiftyTwoWeekHigh"),
        "52_week_low": info.get("fiftyTwoWeekLow"),
        "avg_volume": info.get("averageVolume"),
        "description": info.get("longBusinessSummary"),
    }


async def _get_kr_stock_info(symbol: str) -> dict[str, Any]:
    """Get Korean stock info."""
    try:
        from pykrx import stock

        # Get basic info
        name = stock.get_market_ticker_name(symbol)

        # Get fundamental data and current price
        from datetime import datetime
        today = datetime.now().strftime("%Y%m%d")
        fund = stock.get_market_fundamental_by_ticker(today, market="ALL")

        # Get current price from OHLCV
        current_price = None
        try:
            ohlcv = stock.get_market_ohlcv_by_date(today, today, symbol)
            if not ohlcv.empty:
                current_price = int(ohlcv.iloc[-1]["종가"])
        except Exception:
            pass

        if symbol in fund.index:
            row = fund.loc[symbol]
            return {
                "symbol": symbol,
                "name": name,
                "market": "KR",
                "sector": None,  # pykrx doesn't provide sector directly
                "industry": None,
                "market_cap": int(row.get("시가총액", 0)) if "시가총액" in row else None,
                "current_price": current_price,
                "pe_ratio": float(row.get("PER", 0)) if row.get("PER") else None,
                "pb_ratio": float(row.get("PBR", 0)) if row.get("PBR") else None,
                "dividend_yield": float(row.get("DIV", 0)) / 100 if row.get("DIV") else None,
            }
    except Exception:
        pass

    # Fallback to yfinance
    return await _get_us_stock_info(f"{symbol}.KS")


async def search_stocks(
    query: str,
    market: str = "US",
    limit: int = 10,
) -> list[dict[str, Any]]:
    """Search for stocks by name or symbol.

    Args:
        query: Search query
        market: Market filter
        limit: Maximum results

    Returns:
        List of matching stocks.
    """
    results = []

    if market in ["US", "ALL"]:
        # Search US stocks using yfinance
        try:
            import yfinance as yf
            # yfinance doesn't have a direct search, so we try the symbol
            ticker = yf.Ticker(query.upper())
            info = ticker.info
            if info.get("symbol"):
                results.append({
                    "symbol": info.get("symbol"),
                    "name": info.get("longName", info.get("shortName", "")),
                    "market": "US",
                    "exchange": info.get("exchange", ""),
                })
        except Exception:
            pass

    if market in ["KR", "ALL"]:
        # Search Korean stocks
        try:
            from pykrx import stock
            from datetime import datetime

            today = datetime.now().strftime("%Y%m%d")
            tickers = stock.get_market_ticker_list(today, market="ALL")

            for ticker in tickers:
                name = stock.get_market_ticker_name(ticker)
                if query.lower() in name.lower() or query in ticker:
                    results.append({
                        "symbol": ticker,
                        "name": name,
                        "market": "KR",
                        "exchange": "KRX",
                    })
                    if len(results) >= limit:
                        break
        except Exception:
            pass

    return results[:limit]
