"""Financial data fetching tools."""

from typing import Any


async def get_financial_statements(
    symbol: str,
    market: str = "US",
) -> dict[str, Any]:
    """Get financial statements for a stock.

    Args:
        symbol: Stock symbol
        market: Market code

    Returns:
        Dictionary containing income statement, balance sheet, and cash flow.
    """
    try:
        if market == "KR":
            return await _get_kr_financials(symbol)
        else:
            return await _get_us_financials(symbol)
    except Exception as e:
        print(f"Error fetching financials for {symbol}: {e}")
        return {}


async def _get_us_financials(symbol: str) -> dict[str, Any]:
    """Get US company financials using yfinance."""
    import yfinance as yf

    ticker = yf.Ticker(symbol)

    result = {}

    # Income Statement
    try:
        income = ticker.income_stmt
        if not income.empty:
            latest = income.iloc[:, 0]
            result["income_statement"] = {
                "revenue": float(latest.get("Total Revenue", 0)),
                "gross_profit": float(latest.get("Gross Profit", 0)),
                "operating_income": float(latest.get("Operating Income", 0)),
                "net_income": float(latest.get("Net Income", 0)),
                "ebitda": float(latest.get("EBITDA", 0)),
                "gross_margin": (
                    float(latest.get("Gross Profit", 0)) / float(latest.get("Total Revenue", 1))
                    if latest.get("Total Revenue") else None
                ),
            }
    except Exception:
        pass

    # Balance Sheet
    try:
        balance = ticker.balance_sheet
        if not balance.empty:
            latest = balance.iloc[:, 0]
            result["balance_sheet"] = {
                "total_assets": float(latest.get("Total Assets", 0)),
                "total_liabilities": float(latest.get("Total Liabilities Net Minority Interest", 0)),
                "total_equity": float(latest.get("Stockholders Equity", 0)),
                "total_debt": float(latest.get("Total Debt", 0)),
                "cash": float(latest.get("Cash And Cash Equivalents", 0)),
                "current_assets": float(latest.get("Current Assets", 0)),
                "current_liabilities": float(latest.get("Current Liabilities", 0)),
            }
    except Exception:
        pass

    # Cash Flow
    try:
        cashflow = ticker.cashflow
        if not cashflow.empty:
            latest = cashflow.iloc[:, 0]
            result["cash_flow"] = {
                "operating_cash_flow": float(latest.get("Operating Cash Flow", 0)),
                "investing_cash_flow": float(latest.get("Investing Cash Flow", 0)),
                "financing_cash_flow": float(latest.get("Financing Cash Flow", 0)),
                "free_cash_flow": float(latest.get("Free Cash Flow", 0)),
                "capex": float(latest.get("Capital Expenditure", 0)),
            }
    except Exception:
        pass

    return result


async def _get_kr_financials(symbol: str) -> dict[str, Any]:
    """Get Korean company financials using OpenDART or fallback."""
    import os

    dart_key = os.getenv("OPENDART_API_KEY")

    if dart_key:
        try:
            return await _get_kr_financials_dart(symbol, dart_key)
        except Exception:
            pass

    # Fallback to yfinance with .KS suffix
    return await _get_us_financials(f"{symbol}.KS")


async def _get_kr_financials_dart(symbol: str, api_key: str) -> dict[str, Any]:
    """Get Korean financials from OpenDART API."""
    import httpx

    # This is a simplified implementation
    # Full implementation would need proper DART API integration
    base_url = "https://opendart.fss.or.kr/api"

    async with httpx.AsyncClient() as client:
        # Get corp code first
        # Then get financial statements
        # This requires proper DART API setup
        pass

    return {}


async def get_financial_ratios(
    symbol: str,
    market: str = "US",
) -> dict[str, Any]:
    """Calculate financial ratios for a stock.

    Args:
        symbol: Stock symbol
        market: Market code

    Returns:
        Dictionary of financial ratios.
    """
    try:
        import yfinance as yf

        ticker_symbol = f"{symbol}.KS" if market == "KR" else symbol
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.info

        # Get financial data
        financials = await get_financial_statements(symbol, market)

        ratios = {}

        # Profitability Ratios
        if info.get("returnOnEquity"):
            ratios["roe"] = info["returnOnEquity"]
        if info.get("returnOnAssets"):
            ratios["roa"] = info["returnOnAssets"]
        if info.get("profitMargins"):
            ratios["profit_margin"] = info["profitMargins"]
        if info.get("grossMargins"):
            ratios["gross_margin"] = info["grossMargins"]
        if info.get("operatingMargins"):
            ratios["operating_margin"] = info["operatingMargins"]

        # Liquidity Ratios
        if info.get("currentRatio"):
            ratios["current_ratio"] = info["currentRatio"]
        if info.get("quickRatio"):
            ratios["quick_ratio"] = info["quickRatio"]

        # Leverage Ratios
        if info.get("debtToEquity"):
            ratios["debt_to_equity"] = info["debtToEquity"] / 100  # Convert to decimal

        # Valuation Ratios
        if info.get("trailingPE"):
            ratios["pe_ratio"] = info["trailingPE"]
        if info.get("forwardPE"):
            ratios["forward_pe"] = info["forwardPE"]
        if info.get("priceToBook"):
            ratios["pb_ratio"] = info["priceToBook"]
        if info.get("priceToSalesTrailing12Months"):
            ratios["ps_ratio"] = info["priceToSalesTrailing12Months"]
        if info.get("enterpriseToEbitda"):
            ratios["ev_to_ebitda"] = info["enterpriseToEbitda"]

        # Growth Ratios
        if info.get("revenueGrowth"):
            ratios["revenue_growth"] = info["revenueGrowth"]
        if info.get("earningsGrowth"):
            ratios["earnings_growth"] = info["earningsGrowth"]

        return ratios

    except Exception as e:
        print(f"Error calculating ratios for {symbol}: {e}")
        return {}
