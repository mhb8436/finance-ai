"""Technical indicators calculation tools."""

from typing import Any
import numpy as np


async def calculate_indicators(
    price_data: list[dict[str, Any]],
    indicators: list[str],
) -> dict[str, Any]:
    """Calculate technical indicators from price data.

    Args:
        price_data: List of OHLCV dictionaries
        indicators: List of indicator names to calculate

    Returns:
        Dictionary of calculated indicators.
    """
    if not price_data:
        return {}

    # Extract price arrays
    closes = np.array([d["close"] for d in price_data], dtype=float)
    highs = np.array([d["high"] for d in price_data], dtype=float)
    lows = np.array([d["low"] for d in price_data], dtype=float)
    volumes = np.array([d["volume"] for d in price_data], dtype=float)

    result = {}

    for indicator in indicators:
        try:
            if indicator.startswith("sma_"):
                period = int(indicator.split("_")[1])
                result[indicator] = _calculate_sma(closes, period).tolist()

            elif indicator.startswith("ema_"):
                period = int(indicator.split("_")[1])
                result[indicator] = _calculate_ema(closes, period).tolist()

            elif indicator.startswith("rsi_") or indicator == "rsi":
                period = int(indicator.split("_")[1]) if "_" in indicator else 14
                result[indicator] = _calculate_rsi(closes, period).tolist()

            elif indicator == "macd":
                macd_line, signal_line, histogram = _calculate_macd(closes)
                result["macd_line"] = macd_line.tolist()
                result["macd_signal"] = signal_line.tolist()
                result["macd_histogram"] = histogram.tolist()

            elif indicator == "bollinger" or indicator.startswith("bollinger_"):
                period = 20
                std_dev = 2
                if "_" in indicator:
                    parts = indicator.split("_")
                    if len(parts) >= 2:
                        period = int(parts[1])
                    if len(parts) >= 3:
                        std_dev = int(parts[2])
                upper, middle, lower = _calculate_bollinger(closes, period, std_dev)
                result["bollinger_upper"] = upper.tolist()
                result["bollinger_middle"] = middle.tolist()
                result["bollinger_lower"] = lower.tolist()

            elif indicator == "atr" or indicator.startswith("atr_"):
                period = int(indicator.split("_")[1]) if "_" in indicator else 14
                result[indicator] = _calculate_atr(highs, lows, closes, period).tolist()

            elif indicator == "obv":
                result["obv"] = _calculate_obv(closes, volumes).tolist()

            elif indicator == "vwap":
                result["vwap"] = _calculate_vwap(highs, lows, closes, volumes).tolist()

            elif indicator == "stochastic" or indicator.startswith("stoch_"):
                k_period = 14
                d_period = 3
                k, d = _calculate_stochastic(highs, lows, closes, k_period, d_period)
                result["stoch_k"] = k.tolist()
                result["stoch_d"] = d.tolist()

        except Exception as e:
            print(f"Error calculating {indicator}: {e}")
            result[indicator] = None

    return result


def _calculate_sma(data: np.ndarray, period: int) -> np.ndarray:
    """Calculate Simple Moving Average."""
    result = np.full(len(data), np.nan)
    for i in range(period - 1, len(data)):
        result[i] = np.mean(data[i - period + 1:i + 1])
    return result


def _calculate_ema(data: np.ndarray, period: int) -> np.ndarray:
    """Calculate Exponential Moving Average."""
    result = np.full(len(data), np.nan)
    multiplier = 2 / (period + 1)

    # Start with SMA for the first EMA value
    result[period - 1] = np.mean(data[:period])

    # Calculate EMA for remaining values
    for i in range(period, len(data)):
        result[i] = (data[i] - result[i - 1]) * multiplier + result[i - 1]

    return result


def _calculate_rsi(data: np.ndarray, period: int = 14) -> np.ndarray:
    """Calculate Relative Strength Index."""
    result = np.full(len(data), np.nan)

    # Calculate price changes
    deltas = np.diff(data)

    # Separate gains and losses
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)

    # Calculate average gains and losses
    avg_gain = np.zeros(len(data) - 1)
    avg_loss = np.zeros(len(data) - 1)

    # First average
    avg_gain[period - 1] = np.mean(gains[:period])
    avg_loss[period - 1] = np.mean(losses[:period])

    # Subsequent averages using smoothing
    for i in range(period, len(data) - 1):
        avg_gain[i] = (avg_gain[i - 1] * (period - 1) + gains[i]) / period
        avg_loss[i] = (avg_loss[i - 1] * (period - 1) + losses[i]) / period

    # Calculate RSI
    for i in range(period - 1, len(data) - 1):
        if avg_loss[i] == 0:
            result[i + 1] = 100
        else:
            rs = avg_gain[i] / avg_loss[i]
            result[i + 1] = 100 - (100 / (1 + rs))

    return result


def _calculate_macd(
    data: np.ndarray,
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Calculate MACD."""
    fast_ema = _calculate_ema(data, fast_period)
    slow_ema = _calculate_ema(data, slow_period)

    macd_line = fast_ema - slow_ema
    signal_line = _calculate_ema(macd_line[~np.isnan(macd_line)], signal_period)

    # Pad signal line to match length
    padded_signal = np.full(len(data), np.nan)
    start_idx = len(data) - len(signal_line)
    padded_signal[start_idx:] = signal_line

    histogram = macd_line - padded_signal

    return macd_line, padded_signal, histogram


def _calculate_bollinger(
    data: np.ndarray,
    period: int = 20,
    std_dev: float = 2,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Calculate Bollinger Bands."""
    middle = _calculate_sma(data, period)

    std = np.full(len(data), np.nan)
    for i in range(period - 1, len(data)):
        std[i] = np.std(data[i - period + 1:i + 1])

    upper = middle + (std * std_dev)
    lower = middle - (std * std_dev)

    return upper, middle, lower


def _calculate_atr(
    highs: np.ndarray,
    lows: np.ndarray,
    closes: np.ndarray,
    period: int = 14,
) -> np.ndarray:
    """Calculate Average True Range."""
    result = np.full(len(highs), np.nan)

    # Calculate True Range
    tr = np.zeros(len(highs))
    tr[0] = highs[0] - lows[0]

    for i in range(1, len(highs)):
        tr[i] = max(
            highs[i] - lows[i],
            abs(highs[i] - closes[i - 1]),
            abs(lows[i] - closes[i - 1]),
        )

    # Calculate ATR using EMA of TR
    result[period - 1] = np.mean(tr[:period])
    multiplier = 2 / (period + 1)

    for i in range(period, len(highs)):
        result[i] = (tr[i] - result[i - 1]) * multiplier + result[i - 1]

    return result


def _calculate_obv(closes: np.ndarray, volumes: np.ndarray) -> np.ndarray:
    """Calculate On-Balance Volume."""
    result = np.zeros(len(closes))
    result[0] = volumes[0]

    for i in range(1, len(closes)):
        if closes[i] > closes[i - 1]:
            result[i] = result[i - 1] + volumes[i]
        elif closes[i] < closes[i - 1]:
            result[i] = result[i - 1] - volumes[i]
        else:
            result[i] = result[i - 1]

    return result


def _calculate_vwap(
    highs: np.ndarray,
    lows: np.ndarray,
    closes: np.ndarray,
    volumes: np.ndarray,
) -> np.ndarray:
    """Calculate Volume Weighted Average Price."""
    typical_price = (highs + lows + closes) / 3
    cumulative_tp_vol = np.cumsum(typical_price * volumes)
    cumulative_vol = np.cumsum(volumes)

    return cumulative_tp_vol / cumulative_vol


def _calculate_stochastic(
    highs: np.ndarray,
    lows: np.ndarray,
    closes: np.ndarray,
    k_period: int = 14,
    d_period: int = 3,
) -> tuple[np.ndarray, np.ndarray]:
    """Calculate Stochastic Oscillator."""
    k = np.full(len(closes), np.nan)

    for i in range(k_period - 1, len(closes)):
        highest_high = np.max(highs[i - k_period + 1:i + 1])
        lowest_low = np.min(lows[i - k_period + 1:i + 1])

        if highest_high - lowest_low == 0:
            k[i] = 50
        else:
            k[i] = 100 * (closes[i] - lowest_low) / (highest_high - lowest_low)

    # %D is SMA of %K
    d = _calculate_sma(k[~np.isnan(k)], d_period)
    padded_d = np.full(len(closes), np.nan)
    start_idx = len(closes) - len(d)
    padded_d[start_idx:] = d

    return k, padded_d
