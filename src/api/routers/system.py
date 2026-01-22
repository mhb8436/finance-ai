"""System API endpoints."""

from fastapi import APIRouter
from pydantic import BaseModel

from src.core.config import get_config, get_llm_config, get_data_provider_config

router = APIRouter()


class SystemStatus(BaseModel):
    status: str
    version: str
    llm_configured: bool
    data_providers: list[str]


class ConfigResponse(BaseModel):
    llm_model: str
    default_market: str
    available_indicators: list[str]


@router.get("/status")
async def get_status() -> SystemStatus:
    """Get system status."""
    llm_config = get_llm_config()
    data_config = get_data_provider_config()

    providers = ["yfinance"]  # Always available
    if data_config.get("alpha_vantage_key"):
        providers.append("alpha_vantage")
    if data_config.get("opendart_key"):
        providers.append("opendart")

    return SystemStatus(
        status="running",
        version="0.1.0",
        llm_configured=bool(llm_config.get("api_key")),
        data_providers=providers,
    )


@router.get("/config")
async def get_system_config() -> ConfigResponse:
    """Get system configuration."""
    config = get_config()
    llm_config = get_llm_config()

    return ConfigResponse(
        llm_model=llm_config.get("model", "gpt-4o"),
        default_market=config.get("default_market", "US"),
        available_indicators=config.get("indicators", {}).get("available", [
            "sma", "ema", "rsi", "macd", "bollinger", "atr", "obv", "vwap"
        ]),
    )
