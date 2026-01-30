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
    """Get Korean financials from OpenDART API.

    Args:
        symbol: Korean stock code (e.g., "005930" for Samsung)
        api_key: OpenDART API key

    Returns:
        Dictionary containing financial statements
    """
    import httpx
    import xml.etree.ElementTree as ET
    import zipfile
    import io
    import json
    from pathlib import Path
    from datetime import datetime

    base_url = "https://opendart.fss.or.kr/api"

    # Clean symbol (remove .KS suffix if present)
    symbol = symbol.replace(".KS", "").replace(".KQ", "")

    # Get corp_code from symbol
    corp_code = await _get_corp_code(symbol, api_key)
    if not corp_code:
        print(f"Could not find corp_code for symbol: {symbol}")
        return await _get_us_financials(f"{symbol}.KS")  # Fallback

    # Get current year and determine report period
    current_year = datetime.now().year
    # Try recent years (current year down to 3 years ago)
    years_to_try = [str(current_year), str(current_year - 1), str(current_year - 2)]

    result = {}

    async with httpx.AsyncClient(timeout=30.0) as client:
        for bsns_year in years_to_try:
            # reprt_code: 11011=1분기, 11012=반기, 11013=3분기, 11014=사업보고서(연간)
            for reprt_code in ["11014", "11013", "11012", "11011"]:
                try:
                    # 단일회사 주요계정 조회
                    response = await client.get(
                        f"{base_url}/fnlttSinglAcnt.json",
                        params={
                            "crtfc_key": api_key,
                            "corp_code": corp_code,
                            "bsns_year": bsns_year,
                            "reprt_code": reprt_code,
                        }
                    )

                    if response.status_code == 200:
                        data = response.json()
                        if data.get("status") == "000" and data.get("list"):
                            result = _parse_dart_financials(data["list"])
                            if result:
                                result["source"] = "OpenDART"
                                result["year"] = bsns_year
                                result["report_code"] = reprt_code
                                return result
                except Exception as e:
                    print(f"DART API error for {bsns_year}/{reprt_code}: {e}")
                    continue

    # If no data found, fallback to yfinance
    if not result:
        print(f"No DART data found for {symbol}, falling back to yfinance")
        return await _get_us_financials(f"{symbol}.KS")

    return result


async def _get_corp_code(symbol: str, api_key: str) -> str | None:
    """Get DART corporation code from stock symbol.

    Args:
        symbol: Stock code (e.g., "005930")
        api_key: OpenDART API key

    Returns:
        Corporation code or None if not found
    """
    import httpx
    import xml.etree.ElementTree as ET
    import zipfile
    import io
    from pathlib import Path
    import json

    # Cache directory for corp code mapping
    cache_dir = Path("./data/dart_cache")
    cache_file = cache_dir / "corp_codes.json"

    # Try to load from cache first
    if cache_file.exists():
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                corp_codes = json.load(f)
                if symbol in corp_codes:
                    return corp_codes[symbol]
        except Exception:
            pass

    # Download corp code list from DART
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(
                "https://opendart.fss.or.kr/api/corpCode.xml",
                params={"crtfc_key": api_key}
            )

            if response.status_code == 200:
                # Response is a zip file containing XML
                zip_data = io.BytesIO(response.content)

                corp_codes = {}
                with zipfile.ZipFile(zip_data, "r") as zf:
                    xml_filename = zf.namelist()[0]
                    with zf.open(xml_filename) as xml_file:
                        tree = ET.parse(xml_file)
                        root = tree.getroot()

                        for corp in root.findall(".//list"):
                            stock_code = corp.findtext("stock_code", "").strip()
                            corp_code = corp.findtext("corp_code", "").strip()
                            if stock_code and corp_code:
                                corp_codes[stock_code] = corp_code

                # Save to cache
                cache_dir.mkdir(parents=True, exist_ok=True)
                with open(cache_file, "w", encoding="utf-8") as f:
                    json.dump(corp_codes, f, ensure_ascii=False)

                return corp_codes.get(symbol)

    except Exception as e:
        print(f"Error fetching corp codes: {e}")

    return None


def _parse_dart_financials(data_list: list) -> dict[str, Any]:
    """Parse DART API financial data into structured format.

    Args:
        data_list: List of financial items from DART API

    Returns:
        Structured financial data dictionary
    """
    result = {
        "income_statement": {},
        "balance_sheet": {},
        "cash_flow": {},
    }

    # Mapping of DART account names to our structure
    # 연결재무제표(CFS) 우선, 없으면 개별재무제표(OFS) 사용

    for item in data_list:
        account_nm = item.get("account_nm", "")
        # Use consolidated (CFS) if available, otherwise individual (OFS)
        fs_div = item.get("fs_div", "")

        # Get the amount - try thstrm_amount first (당기), then frmtrm_amount (전기)
        amount_str = item.get("thstrm_amount", "") or item.get("frmtrm_amount", "")

        try:
            # Remove commas and convert to float
            amount = float(amount_str.replace(",", "")) if amount_str else 0
        except ValueError:
            amount = 0

        # Income Statement items
        if "매출액" in account_nm or "수익(매출액)" in account_nm:
            if fs_div == "CFS" or "revenue" not in result["income_statement"]:
                result["income_statement"]["revenue"] = amount
        elif "매출총이익" in account_nm:
            if fs_div == "CFS" or "gross_profit" not in result["income_statement"]:
                result["income_statement"]["gross_profit"] = amount
        elif "영업이익" in account_nm:
            if fs_div == "CFS" or "operating_income" not in result["income_statement"]:
                result["income_statement"]["operating_income"] = amount
        elif "당기순이익" in account_nm or "분기순이익" in account_nm:
            if fs_div == "CFS" or "net_income" not in result["income_statement"]:
                result["income_statement"]["net_income"] = amount

        # Balance Sheet items
        elif "자산총계" in account_nm:
            if fs_div == "CFS" or "total_assets" not in result["balance_sheet"]:
                result["balance_sheet"]["total_assets"] = amount
        elif "부채총계" in account_nm:
            if fs_div == "CFS" or "total_liabilities" not in result["balance_sheet"]:
                result["balance_sheet"]["total_liabilities"] = amount
        elif "자본총계" in account_nm:
            if fs_div == "CFS" or "total_equity" not in result["balance_sheet"]:
                result["balance_sheet"]["total_equity"] = amount
        elif "유동자산" in account_nm:
            if fs_div == "CFS" or "current_assets" not in result["balance_sheet"]:
                result["balance_sheet"]["current_assets"] = amount
        elif "유동부채" in account_nm:
            if fs_div == "CFS" or "current_liabilities" not in result["balance_sheet"]:
                result["balance_sheet"]["current_liabilities"] = amount

    # Calculate derived metrics
    if result["income_statement"].get("revenue") and result["income_statement"].get("gross_profit"):
        result["income_statement"]["gross_margin"] = (
            result["income_statement"]["gross_profit"] / result["income_statement"]["revenue"]
        )

    if result["balance_sheet"].get("total_assets") and result["balance_sheet"].get("total_liabilities"):
        result["balance_sheet"]["total_debt"] = result["balance_sheet"]["total_liabilities"]

    if result["balance_sheet"].get("current_assets") and result["balance_sheet"].get("current_liabilities"):
        result["balance_sheet"]["current_ratio"] = (
            result["balance_sheet"]["current_assets"] / result["balance_sheet"]["current_liabilities"]
        )

    return result


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
