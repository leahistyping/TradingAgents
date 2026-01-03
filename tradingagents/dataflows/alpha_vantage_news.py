from datetime import datetime, timedelta

from .alpha_vantage_common import _make_api_request, format_datetime_for_api

def _clean_params(params: dict) -> dict:
    """Remove empty/None parameters before making the API call."""
    return {k: v for k, v in params.items() if v not in (None, "", [])}

def _normalize_topics(topics: str | list[str] | None) -> str | None:
    """Convert topics input to comma-separated format accepted by Alpha Vantage."""
    if topics is None:
        return None
    if isinstance(topics, str):
        return topics
    return ",".join(topic.strip() for topic in topics if topic and topic.strip())

def get_news(ticker, start_date, end_date) -> dict[str, str] | str:
    """Returns live and historical market news & sentiment data from premier news outlets worldwide.

    Covers stocks, cryptocurrencies, forex, and topics like fiscal policy, mergers & acquisitions, IPOs.

    Args:
        ticker: Stock symbol for news articles.
        start_date: Start date for news search.
        end_date: End date for news search.

    Returns:
        Dictionary containing news sentiment data or JSON string.
    """

    params = _clean_params(
        {
            "tickers": ticker,
            "time_from": format_datetime_for_api(start_date),
            "time_to": format_datetime_for_api(end_date),
            "sort": "LATEST",
            "limit": "50",
        }
    )

    return _make_api_request("NEWS_SENTIMENT", params)

def get_global_news(curr_date: str, look_back_days: int = 7, limit: int = 5) -> dict[str, str] | str:
    """Returns macro / market-wide news & sentiment data using Alpha Vantage's NEWS_SENTIMENT endpoint."""

    try:
        end_dt = datetime.strptime(curr_date, "%Y-%m-%d")
    except ValueError as exc:
        raise ValueError(f"curr_date must be in YYYY-MM-DD format, got {curr_date}") from exc

    start_dt = end_dt - timedelta(days=int(look_back_days))

    params = _clean_params(
        {
            # Focus on broad market/economy topics to mimic a macro news feed
            "topics": _normalize_topics(["financial_markets", "finance", "economy_macro"]),
            "time_from": format_datetime_for_api(start_dt.strftime("%Y-%m-%d")),
            "time_to": format_datetime_for_api(end_dt.strftime("%Y-%m-%d")),
            "sort": "LATEST",
            "limit": str(limit),
        }
    )

    return _make_api_request("NEWS_SENTIMENT", params)

def get_insider_transactions(symbol: str) -> dict[str, str] | str:
    """Returns latest and historical insider transactions by key stakeholders.

    Covers transactions by founders, executives, board members, etc.

    Args:
        symbol: Ticker symbol. Example: "IBM".

    Returns:
        Dictionary containing insider transaction data or JSON string.
    """

    params = {
        "symbol": symbol,
    }

    return _make_api_request("INSIDER_TRANSACTIONS", params)
