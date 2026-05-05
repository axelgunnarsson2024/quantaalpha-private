import json
import logging
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import yfinance as yf

from paper_trading.config import SP500_TICKERS

logger = logging.getLogger(__name__)


def get_sp500_tickers(cache_path: Path = SP500_TICKERS) -> list[str]:
    """Return S&P 500 ticker list, scraping Wikipedia and caching the result."""
    if cache_path.exists():
        with open(cache_path) as f:
            tickers = json.load(f)
        logger.info(f"Loaded {len(tickers)} tickers from cache")
        return tickers

    logger.info("Scraping S&P 500 tickers from Wikipedia...")
    table = pd.read_html(
        "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies",
        attrs={"id": "constituents"},
    )[0]
    # BRK.B → BRK-B for yfinance compatibility
    tickers = [t.replace(".", "-") for t in table["Symbol"].tolist()]

    with open(cache_path, "w") as f:
        json.dump(tickers, f)
    logger.info(f"Cached {len(tickers)} tickers to {cache_path}")
    return tickers


def fetch_ohlcv(tickers: list[str], start: str, end: str) -> pd.DataFrame:
    """
    Download OHLCV from yfinance and reshape to MultiIndex (datetime, instrument)
    with columns [$open, $high, $low, $close, $volume].

    Dollar-sign column names are required by parse_symbol() in expr_parser.py.
    Index level names 'datetime' and 'instrument' are required by function_lib.py.
    """
    logger.info(f"Fetching OHLCV for {len(tickers)} tickers: {start} → {end}")

    raw = yf.download(
        tickers,
        start=start,
        end=end,
        auto_adjust=True,
        progress=False,
        group_by="column",
    )

    if raw.empty:
        raise ValueError("yfinance returned empty DataFrame — check tickers and date range")

    rename_map = {
        "Open": "$open",
        "High": "$high",
        "Low": "$low",
        "Close": "$close",
        "Volume": "$volume",
    }

    frames = []
    single_ticker = len(tickers) == 1

    for ticker in tickers:
        try:
            if single_ticker:
                sub = raw[["Open", "High", "Low", "Close", "Volume"]].copy()
            else:
                sub = raw.xs(ticker, axis=1, level=1)[
                    ["Open", "High", "Low", "Close", "Volume"]
                ].copy()
        except KeyError:
            continue

        sub = sub.rename(columns=rename_map)
        sub = sub.dropna(subset=["$close"])
        if sub.empty:
            continue

        sub.index = pd.to_datetime(sub.index)
        sub.index.name = "datetime"
        sub["instrument"] = ticker
        frames.append(sub.reset_index().set_index(["datetime", "instrument"]))

    if not frames:
        raise ValueError("No usable OHLCV data returned from yfinance")

    df = pd.concat(frames).sort_index()
    logger.info(f"Fetched {len(df)} rows, {df.index.get_level_values('instrument').nunique()} instruments")
    return df


def fetch_recent_ohlcv(tickers: list[str], lookback_calendar_days: int = 90) -> pd.DataFrame:
    """Fetch the last N calendar days of OHLCV (guarantees enough trading days for rolling windows)."""
    end = datetime.today().strftime("%Y-%m-%d")
    start = (datetime.today() - timedelta(days=lookback_calendar_days)).strftime("%Y-%m-%d")
    return fetch_ohlcv(tickers, start, end)
