import csv
import json
import logging
import sqlite3
from datetime import date
from pathlib import Path

import pandas as pd

from paper_trading.config import PNL_DB, TRADES_CSV

logger = logging.getLogger(__name__)

_TRADES_HEADER = ["date", "ticker", "side", "factor_score", "run_timestamp"]
_PNL_SCHEMA = """
CREATE TABLE IF NOT EXISTS pnl (
    date TEXT,
    portfolio_value REAL,
    cash REAL,
    positions_json TEXT,
    run_timestamp TEXT
)
"""


def log_trades(
    buys: list[str],
    sells: list[str],
    scores: pd.Series,
    today: date,
    csv_path: Path = TRADES_CSV,
):
    """Append buy/sell records to trades.csv."""
    timestamp = pd.Timestamp.now().isoformat()
    write_header = not csv_path.exists()

    with open(csv_path, "a", newline="") as f:
        writer = csv.writer(f)
        if write_header:
            writer.writerow(_TRADES_HEADER)
        for ticker in buys:
            writer.writerow([today, ticker, "BUY", scores.get(ticker, ""), timestamp])
        for ticker in sells:
            writer.writerow([today, ticker, "SELL", scores.get(ticker, ""), timestamp])

    logger.info(f"Logged {len(buys)} buys and {len(sells)} sells to {csv_path.name}")


def log_pnl(client, today: date, db_path: Path = PNL_DB):
    """Insert a daily P&L snapshot into SQLite."""
    from alpaca.trading.client import TradingClient

    timestamp = pd.Timestamp.now().isoformat()

    account = client.get_account()
    portfolio_value = float(account.portfolio_value)
    cash = float(account.cash)

    positions = client.get_all_positions()
    positions_json = json.dumps({p.symbol: float(p.market_value) for p in positions})

    con = sqlite3.connect(db_path)
    con.execute(_PNL_SCHEMA)
    con.execute(
        "INSERT INTO pnl VALUES (?, ?, ?, ?, ?)",
        (str(today), portfolio_value, cash, positions_json, timestamp),
    )
    con.commit()
    con.close()
    logger.info(f"P&L logged: portfolio=${portfolio_value:,.2f}, cash=${cash:,.2f}")
