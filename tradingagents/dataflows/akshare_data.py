import math
import time
from datetime import datetime, date, timedelta
from typing import Dict, List, Tuple

import akshare as ak
import pandas as pd
import requests


def normalize_a_share_symbol(symbol: str) -> Tuple[str, str, str]:
    """
    Normalize various ticker formats (e.g., 600519, sh600519, 600519.SS)
    into Akshare friendly tickers and extract the numeric code.

    Returns:
        Tuple[str, str, str]: (akshare_symbol, numeric_code, exchange_prefix)
    """
    if not symbol:
        raise ValueError("Empty ticker symbol provided.")

    clean_symbol = symbol.strip().lower()
    clean_symbol = (
        clean_symbol.replace(".ss", "")
        .replace(".sz", "")
        .replace(".bj", "")
        .replace(".sh", "")
    )

    digits = "".join(ch for ch in clean_symbol if ch.isdigit())
    if len(digits) < 5:
        raise ValueError(f"Invalid A-share ticker format: {symbol}")
    digits = digits[-6:]

    exchange = None
    # Determine exchange from prefix hints
    if clean_symbol.startswith("sh"):
        exchange = "sh"
    elif clean_symbol.startswith("sz"):
        exchange = "sz"
    elif clean_symbol.startswith("bj"):
        exchange = "bj"
    else:
        first_two = digits[:2]
        first_one = digits[0]
        if digits.startswith(("68", "60", "59", "50", "51", "52")) or first_one in [
            "6",
            "9",
        ]:
            exchange = "sh"
        elif digits.startswith(("43", "83", "87", "88")):
            exchange = "bj"
        else:
            exchange = "sz"

    return f"{exchange}{digits}", digits, exchange


def _format_value(value) -> str:
    if value is None or (isinstance(value, float) and (math.isnan(value) or math.isinf(value))):
        return "N/A"
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def _call_akshare(func, *args, retries: int = 3, backoff: float = 1.0, **kwargs):
    """
    Invoke Akshare API with simple retry/backoff to handle intermittent Eastmoney failures.
    """
    last_err: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            return func(*args, **kwargs)
        except Exception as exc:
            # Retry on transient network errors
            transient = isinstance(exc, requests.exceptions.RequestException) or "HTTPSConnectionPool" in str(exc)
            if transient and attempt < retries:
                wait = backoff * attempt
                print(f"WARNING: Akshare request failed (attempt {attempt}/{retries}): {exc}. Retrying in {wait:.1f}s...")
                time.sleep(wait)
                last_err = exc
                continue
            last_err = exc
            break
    raise RuntimeError(f"Akshare request failed after {retries} attempts: {last_err}")


def _format_section(title: str, entries: List[str]) -> str:
    if not entries:
        return ""
    formatted = "\n".join(entries)
    return f"## {title}\n{formatted}\n"


def _latest_report_date(curr_date: str = None, freq: str = "quarterly") -> str:
    """Return the latest report date string accepted by Akshare interfaces."""
    freq = (freq or "quarterly").lower()
    if curr_date:
        ref_date = datetime.strptime(curr_date, "%Y-%m-%d").date()
    else:
        ref_date = date.today()

    quarter_points = [
        (3, 31),
        (6, 30),
        (9, 30),
        (12, 31),
    ]

    if freq == "annual":
        candidate = date(ref_date.year, 12, 31)
        if ref_date < candidate:
            candidate = date(ref_date.year - 1, 12, 31)
        return candidate.strftime("%Y%m%d")

    quarter_idx = (ref_date.month - 1) // 3
    quarter_month, quarter_day = quarter_points[quarter_idx]
    year = ref_date.year
    candidate = date(year, quarter_month, quarter_day)

    if ref_date < candidate:
        quarter_idx -= 1
        if quarter_idx < 0:
            quarter_idx = len(quarter_points) - 1
            year -= 1
        quarter_month, quarter_day = quarter_points[quarter_idx]
        candidate = date(year, quarter_month, quarter_day)

    return candidate.strftime("%Y%m%d")


def _format_eastmoney_df(df: pd.DataFrame) -> pd.DataFrame:
    rename_map = {
        "日期": "Date",
        "开盘": "Open",
        "收盘": "Close",
        "最高": "High",
        "最低": "Low",
        "成交量": "Volume",
        "成交额": "Turnover",
        "振幅": "Amplitude%",
        "涨跌幅": "PctChange%",
        "涨跌额": "Change",
        "换手率": "TurnoverRate%",
    }
    df = df.rename(columns=rename_map)
    df["Date"] = pd.to_datetime(df["Date"])
    return df


def _format_tencent_df(df: pd.DataFrame) -> pd.DataFrame:
    rename_map = {
        "date": "Date",
        "open": "Open",
        "close": "Close",
        "high": "High",
        "low": "Low",
        "amount": "Volume",
    }
    df = df.rename(columns=rename_map)
    df["Date"] = pd.to_datetime(df["Date"])
    return df


def get_standardized_ohlcv_dataframe(symbol: str, start_date: str, end_date: str, adjust: str = "qfq") -> Tuple[pd.DataFrame, str]:
    """
    Fetch OHLCV data using Akshare (Eastmoney) with fallback to Tencent securities.
    Returns (dataframe, source_label). DataFrame columns include Date (datetime), Open, High, Low, Close, Volume, Turnover (optional).
    """
    ak_symbol, digits, exchange = normalize_a_share_symbol(symbol)

    if start_date > end_date:
        raise ValueError("start_date must be earlier than end_date")

    start_fmt = start_date.replace("-", "")
    end_fmt = end_date.replace("-", "")

    df = ak.stock_zh_a_hist(
        symbol=ak_symbol,
        period="daily",
        start_date=start_fmt,
        end_date=end_fmt,
        adjust=adjust,
    )
    if df is not None and not df.empty:
        formatted = _format_eastmoney_df(df)
        return formatted, "stock_zh_a_hist"

    # Fallback to Tencent historical data (requires exchange prefix)
    tx_symbol = f"{exchange}{digits}"
    df_tx = ak.stock_zh_a_hist_tx(
        symbol=tx_symbol,
        start_date=start_fmt,
        end_date=end_fmt,
        adjust=adjust or "",
    )
    if df_tx is not None and not df_tx.empty:
        formatted = _format_tencent_df(df_tx)
        return formatted, "stock_zh_a_hist_tx"

    return None, ""


def get_stock(symbol: str, start_date: str, end_date: str) -> str:
    """Retrieve OHLCV data for mainland A-shares via Akshare with Tencent fallback."""
    df, source = get_standardized_ohlcv_dataframe(symbol, start_date, end_date)
    if df is None or df.empty:
        return f"Akshare: No stock data for {symbol} between {start_date} and {end_date}"

    df = df.copy()
    df["Date"] = df["Date"].dt.strftime("%Y-%m-%d")

    ordered_cols = [
        col
        for col in [
            "Date",
            "Open",
            "High",
            "Low",
            "Close",
            "Volume",
            "Turnover",
            "PctChange%",
            "Amplitude%",
            "Change",
            "TurnoverRate%",
        ]
        if col in df.columns
    ]
    df = df[ordered_cols]

    header = (
        f"# Akshare OHLCV for {symbol}\n"
        f"# Period: {start_date} → {end_date}\n"
        f"# Records: {len(df)} | Source: {source}\n"
        f"# Retrieved at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    )
    return header + df.to_csv(index=False)


def _format_dataset_row(row: pd.Series, title: str, alias_map: Dict[str, str]) -> str:
    highlights = []
    for column, label in alias_map.items():
        if column in row:
            highlights.append(f"- {label}: {_format_value(row[column])}")

    additional = []
    for column, value in row.items():
        if column in alias_map or pd.isna(value):
            continue
        additional.append(f"  {column}: {_format_value(value)}")

    sections = []
    sections.append(_format_section(title, highlights))
    if additional:
        sections.append(_format_section("Additional Fields", additional))
    return "\n".join(filter(None, sections))


def _get_dataset_row(df: pd.DataFrame, ticker: str, dataset_name: str) -> pd.Series:
    if df is None or df.empty:
        raise ValueError(f"Akshare returned no {dataset_name} data.")

    _, digits, _ = normalize_a_share_symbol(ticker)
    df["股票代码"] = df["股票代码"].astype(str).str.zfill(6)
    match = df[df["股票代码"] == digits]
    if match.empty:
        raise ValueError(f"No {dataset_name} entry found for ticker {digits}")
    return match.iloc[0]


def get_fundamentals(ticker: str, curr_date: str = None) -> str:
    report_date = _latest_report_date(curr_date, "quarterly")
    df = _call_akshare(ak.stock_yjbb_em, date=report_date)
    try:
        row = _get_dataset_row(df, ticker, "earnings bulletin")
    except ValueError as exc:
        raise RuntimeError(f"{exc} (report date {report_date})")

    alias_map = {
        "股票简称": "Stock Name",
        "每股收益": "EPS (CNY)",
        "营业总收入-营业总收入": "Revenue (CNY)",
        "营业总收入-同比增长": "Revenue YoY %",
        "营业总收入-季度环比增长": "Revenue QoQ %",
        "净利润-净利润": "Net Profit (CNY)",
        "净利润-同比增长": "Net Profit YoY %",
        "净利润-季度环比增长": "Net Profit QoQ %",
        "每股净资产": "BVPS (CNY)",
        "净资产收益率": "ROE %",
        "每股经营现金流量": "Operating Cash Flow / Share",
        "销售毛利率": "Gross Margin %",
        "所处行业": "Industry",
        "最新公告日期": "Announcement Date",
    }

    report_header = f"### Earnings Express ({report_date})\n- 股票代码: {row['股票代码']}\n"
    if "最新公告日期" in row:
        report_header += f"- 最新公告日期: {_format_value(row['最新公告日期'])}\n\n"

    return report_header + _format_dataset_row(row, "Key Metrics", alias_map)


def get_cashflow(ticker: str, freq: str = "quarterly", curr_date: str = None) -> str:
    report_date = _latest_report_date(curr_date, freq)
    df = _call_akshare(ak.stock_xjll_em, date=report_date)
    try:
        row = _get_dataset_row(df, ticker, "cashflow statement")
    except ValueError as exc:
        raise RuntimeError(f"{exc} (report date {report_date})")

    alias_map = {
        "净现金流-净现金流": "Net Cash Flow",
        "净现金流-同比增长": "Net Cash Flow YoY %",
        "经营性现金流-现金流量净额": "Operating CF Net",
        "经营性现金流-净现金流占比": "Operating CF as % of Net",
        "投资性现金流-现金流量净额": "Investing CF Net",
        "投资性现金流-净现金流占比": "Investing CF as % of Net",
        "融资性现金流-现金流量净额": "Financing CF Net",
        "融资性现金流-净现金流占比": "Financing CF as % of Net",
        "公告日期": "Announcement Date",
    }

    header = f"### Cash Flow Statement ({report_date}, freq={freq})\n- 股票代码: {row['股票代码']}\n\n"
    return header + _format_dataset_row(row, "Cash Flow Highlights", alias_map)


def get_balance_sheet(ticker: str, freq: str = "quarterly", curr_date: str = None) -> str:
    report_date = _latest_report_date(curr_date, freq)
    df = _call_akshare(ak.stock_zcfz_em, date=report_date)
    try:
        row = _get_dataset_row(df, ticker, "balance sheet")
    except ValueError as exc:
        raise RuntimeError(f"{exc} (report date {report_date})")

    alias_map = {
        "货币资金": "Cash & Cash Equivalents",
        "应收账款": "Accounts Receivable",
        "存货": "Inventory",
        "总资产": "Total Assets",
        "总负债": "Total Liabilities",
        "归属于母公司所有者权益": "Equity (Parent)",
        "股东权益合计(含少数股东权益)": "Total Equity",
    }

    header = f"### Balance Sheet ({report_date}, freq={freq})\n- 股票代码: {row['股票代码']}\n\n"
    return header + _format_dataset_row(row, "Balance Sheet Highlights", alias_map)


def get_income_statement(ticker: str, freq: str = "quarterly", curr_date: str = None) -> str:
    report_date = _latest_report_date(curr_date, freq)
    df = _call_akshare(ak.stock_lrb_em, date=report_date)
    try:
        row = _get_dataset_row(df, ticker, "income statement")
    except ValueError as exc:
        raise RuntimeError(f"{exc} (report date {report_date})")

    alias_map = {
        "营业总收入": "Revenue",
        "营业收入": "Operating Revenue",
        "营业利润": "Operating Profit",
        "利润总额": "Total Profit",
        "净利润": "Net Profit",
        "归属于母公司股东的净利润": "Net Profit (to parent)",
    }

    header = f"### Income Statement ({report_date}, freq={freq})\n- 股票代码: {row['股票代码']}\n\n"
    return header + _format_dataset_row(row, "Income Statement Highlights", alias_map)


def _format_news_entries(entries: List[Dict[str, str]], title: str) -> str:
    if not entries:
        return f"{title}\n- 暂无相关新闻\n"

    lines = [f"{title}"]
    for item in entries:
        headline = item.get("headline", "无标题")
        url = item.get("url", "")
        published = item.get("published", "")
        source = item.get("source", "")
        summary = item.get("summary", "")
        link_part = f"[{headline}]({url})" if url else headline
        lines.append(f"- {link_part} | 来源: {source} | 时间: {published}\n  摘要: {summary}")
    return "\n".join(lines) + "\n"


def get_news(ticker: str, start_date: str, end_date: str, limit: int = 20) -> str:
    """Fetch company-specific news from Eastmoney via Akshare."""
    _, digits, _ = normalize_a_share_symbol(ticker)
    df = _call_akshare(ak.stock_news_em, symbol=digits)
    if df is None or df.empty:
        return f"Akshare: No news data available for {digits}"

    df = df.copy()
    try:
        df["发布时间"] = pd.to_datetime(df["发布时间"])
    except Exception:
        pass

    start_dt = pd.to_datetime(start_date)
    end_dt = pd.to_datetime(end_date) + timedelta(days=1) - timedelta(seconds=1)
    if "发布时间" in df.columns:
        df = df[(df["发布时间"] >= start_dt) & (df["发布时间"] <= end_dt)]

    if df.empty:
        return f"Akshare: No news data for {digits} between {start_date} and {end_date}"

    records = []
    for _, row in df.head(limit).iterrows():
        records.append(
            {
                "headline": str(row.get("新闻标题", "")).strip(),
                "summary": str(row.get("新闻内容", "")).strip(),
                "published": row.get("发布时间", ""),
                "source": row.get("文章来源", ""),
                "url": row.get("新闻链接", ""),
            }
        )

    header = f"### 个股新闻（来源：东方财富，代码 {digits}）\n"
    return header + _format_news_entries(records, "最新新闻")


def get_global_news(curr_date: str, look_back_days: int = 7, limit: int = 20) -> str:
    """Fetch macro / curated finance news from Caixin data feed."""
    df = _call_akshare(ak.stock_news_main_cx)
    if df is None or df.empty:
        return "Akshare: 无法获取财新内容精选"

    df = df.copy()
    try:
        df["pub_time"] = pd.to_datetime(df["pub_time"])
    except Exception:
        pass

    end_dt = pd.to_datetime(curr_date)
    start_dt = end_dt - timedelta(days=int(look_back_days))
    if "pub_time" in df.columns:
        df = df[(df["pub_time"] >= start_dt) & (df["pub_time"] <= end_dt)]

    if df.empty:
        return f"Akshare: 在 {start_dt.date()} ~ {end_dt.date()} 区间内无财新精选新闻"

    records = []
    for _, row in df.head(limit).iterrows():
        records.append(
            {
                "headline": str(row.get("tag", "")).strip(),
                "summary": str(row.get("summary", "")).strip(),
                "published": row.get("pub_time", ""),
                "source": "财新数据通",
                "url": row.get("url", ""),
            }
        )

    header = f"### 宏观新闻精选（财新数据通，最近 {look_back_days} 天）\n"
    return header + _format_news_entries(records, "精选要闻")
