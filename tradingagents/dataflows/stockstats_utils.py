import os
from typing import Annotated

import pandas as pd
import yfinance as yf
from stockstats import wrap

from .akshare_data import normalize_a_share_symbol, get_standardized_ohlcv_dataframe
from .config import DATA_DIR, get_config


class StockstatsUtils:
    @staticmethod
    def get_stock_stats(
        symbol: Annotated[str, "ticker symbol for the company"],
        indicator: Annotated[
            str, "quantitative indicators based off of the stock data for the company"
        ],
        curr_date: Annotated[
            str, "curr date for retrieving stock price data, YYYY-mm-dd"
        ],
    ):
        """Calculate indicator value for a specific day."""
        config = get_config()
        vendor = config["data_vendors"].get("technical_indicators", "yfinance")
        online = vendor != "local"

        if not online:
            try:
                data = pd.read_csv(
                    os.path.join(
                        DATA_DIR,
                        f"{symbol}-YFin-data-2015-01-01-2025-03-25.csv",
                    )
                )
                df = wrap(data)
            except FileNotFoundError:
                raise Exception("Stockstats fail: Local Yahoo Finance cache missing.")
        else:
            today_date = pd.Timestamp.today()
            curr_date = pd.to_datetime(curr_date)

            end_date = today_date.strftime("%Y-%m-%d")
            start_date = (today_date - pd.DateOffset(years=15)).strftime("%Y-%m-%d")

            data = load_indicator_history(symbol, vendor, config, start_date, end_date)
            df = wrap(data)
            df["Date"] = df["Date"].dt.strftime("%Y-%m-%d")
            curr_date = curr_date.strftime("%Y-%m-%d")

        df[indicator]
        matching_rows = df[df["Date"].str.startswith(curr_date)]

        if not matching_rows.empty:
            return matching_rows[indicator].values[0]
        return "N/A: Not a trading day (weekend or holiday)"


def _sanitize_symbol(symbol: str) -> str:
    return symbol.replace("/", "_").replace("\\", "_").replace(":", "_")


def load_indicator_history(symbol: str, vendor: str, config, start_date: str, end_date: str) -> pd.DataFrame:
    """Fetch (or load cached) historical OHLCV data for indicator calculations."""
    os.makedirs(config["data_cache_dir"], exist_ok=True)
    safe_symbol = _sanitize_symbol(symbol)
    cache_file = os.path.join(
        config["data_cache_dir"],
        f"{safe_symbol}-{vendor}-data-{start_date}-{end_date}.csv",
    )

    if os.path.exists(cache_file):
        data = pd.read_csv(cache_file)
        if "Date" in data.columns:
            data["Date"] = pd.to_datetime(data["Date"])
        elif "date" in data.columns:
            data = data.rename(columns={"date": "Date"})
            data["Date"] = pd.to_datetime(data["Date"])
        else:
            raise ValueError(f"Cached data at {cache_file} missing Date column")
        return data

    data = _download_online_history(symbol, vendor, start_date, end_date)
    data.to_csv(cache_file, index=False)
    return data


def _download_online_history(symbol: str, vendor: str, start_date: str, end_date: str) -> pd.DataFrame:
    """Download OHLCV data from the configured vendor."""
    if vendor == "akshare":
        df, source = get_standardized_ohlcv_dataframe(symbol, start_date, end_date)
        if df is None or df.empty:
            raise ValueError(f"Akshare returned no historical data for {symbol}")
        df = df[["Date", "Open", "High", "Low", "Close", "Volume"]]
        return df

    yf_symbol = symbol
    try:
        _, digits, exchange = normalize_a_share_symbol(symbol)
        suffix_map = {"sh": ".SS", "sz": ".SZ", "bj": ".BJ"}
        yf_symbol = digits + suffix_map.get(exchange, "")
    except ValueError:
        yf_symbol = symbol

    data = yf.download(
        yf_symbol,
        start=start_date,
        end=end_date,
        multi_level_index=False,
        progress=False,
        auto_adjust=True,
    )
    if data.empty:
        raise ValueError(f"yfinance returned no historical data for {yf_symbol}")

    data = data.reset_index()
    data["Date"] = pd.to_datetime(data["Date"])
    return data[["Date", "Open", "High", "Low", "Close", "Volume"]]
