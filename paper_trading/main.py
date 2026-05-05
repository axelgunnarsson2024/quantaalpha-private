#!/usr/bin/env python3
"""
QuantaAlpha Paper Trader

Usage:
  python paper_trading/main.py --train
  python paper_trading/main.py --run [--dry-run]
"""

import argparse
import logging
import sys
from datetime import datetime, date
from pathlib import Path
from zoneinfo import ZoneInfo

from paper_trading.config import (
    FACTOR_JSON,
    LOOKBACK_DAYS,
    MARKET_CLOSE_HOUR,
    MARKET_OPEN_HOUR,
    MARKET_OPEN_MINUTE,
    N_DROP,
    SP500_TICKERS,
    TOPK,
    TRAIN_END,
    VALID_END,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("paper_trader")


def _check_market_hours() -> bool:
    """Return True if current ET time is within trading hours on a weekday."""
    now_et = datetime.now(ZoneInfo("America/New_York"))
    if now_et.weekday() >= 5:
        logger.warning(f"Market closed (weekend). Current ET time: {now_et.strftime('%A %H:%M')}")
        return False
    open_time  = now_et.replace(hour=MARKET_OPEN_HOUR, minute=MARKET_OPEN_MINUTE, second=0, microsecond=0)
    close_time = now_et.replace(hour=MARKET_CLOSE_HOUR, minute=0, second=0, microsecond=0)
    if not (open_time <= now_et <= close_time):
        logger.warning(f"Outside market hours. Current ET time: {now_et.strftime('%H:%M')}. Hours: 09:30–16:00")
        return False
    return True


def run_train(factor_json: Path):
    from paper_trading.data_feed import fetch_ohlcv, get_sp500_tickers
    from paper_trading.factor_engine import compute_factors, load_factor_list
    from paper_trading.model import train

    logger.info("=== TRAIN MODE ===")

    tickers = get_sp500_tickers()

    logger.info(f"Fetching OHLCV {TRAIN_END[:4]} back to 2016 for {len(tickers)} tickers...")
    data_df = fetch_ohlcv(tickers, start="2016-01-01", end=VALID_END)

    factor_list = load_factor_list(factor_json)
    factor_df = compute_factors(data_df, factor_list)

    ic = train(data_df, factor_df)
    print(f"\n✓ Training complete. Validation IC: {ic:.4f}")
    print("  Model saved. Run '--run --dry-run' to test signal generation.")


def run_daily(factor_json: Path, dry_run: bool, skip_hours_check: bool = False):
    from paper_trading.broker import (
        execute_rebalance,
        get_account_equity,
        get_client,
        get_current_positions,
        save_positions,
    )
    from paper_trading.data_feed import fetch_recent_ohlcv
    from paper_trading.factor_engine import compute_factors, load_factor_list
    from paper_trading.logger import log_pnl, log_trades
    from paper_trading.model import load_model, predict
    from paper_trading.portfolio import topk_dropout

    logger.info("=== RUN MODE" + (" (DRY RUN)" if dry_run else "") + " ===")

    if not skip_hours_check and not dry_run:
        if not _check_market_hours():
            sys.exit(0)

    if not SP500_TICKERS.exists():
        logger.error("sp500_tickers.json not found. Run '--train' first.")
        sys.exit(1)

    import json
    with open(SP500_TICKERS) as f:
        tickers = json.load(f)

    logger.info(f"Fetching recent OHLCV ({LOOKBACK_DAYS} trading days buffer)...")
    data_df = fetch_recent_ohlcv(tickers, lookback_calendar_days=90)

    factor_list = load_factor_list(factor_json)
    factor_df = compute_factors(data_df, factor_list)

    # Today's factors = last available date
    latest_date = factor_df.index.get_level_values("datetime").max()
    today_factors = factor_df.xs(latest_date, level="datetime")
    logger.info(f"Signal date: {latest_date.date()}, stocks with valid factors: {len(today_factors)}")

    model_bundle = load_model()
    scores = predict(today_factors, model_bundle)

    client = get_client() if not dry_run else None
    if dry_run:
        current_holdings: set[str] = set()
    else:
        current_holdings = get_current_positions(client)

    buys, sells = topk_dropout(scores, current_holdings, topk=TOPK, n_drop=N_DROP)

    logger.info(f"Signals → BUY {len(buys)}: {buys}")
    logger.info(f"          SELL {len(sells)}: {sells}")

    if dry_run:
        print("\n=== DRY RUN — no orders submitted ===")
        print(f"Top 10 scores:\n{scores.sort_values(ascending=False).head(10).to_string()}")
        return

    execute_rebalance(buys, sells, client)

    # Update position record from live API (ground truth after execution)
    updated_holdings = get_current_positions(client)
    save_positions(updated_holdings)

    today = date.today()
    log_trades(buys, sells, scores, today)
    log_pnl(client, today)

    print(f"\n✓ Rebalance complete — {len(buys)} buys, {len(sells)} sells")
    print(f"  Portfolio equity: ${get_account_equity(client):,.2f}")


def main():
    parser = argparse.ArgumentParser(
        description="QuantaAlpha Paper Trader",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--train", action="store_true",
                      help="Fetch historical data and train LightGBM model")
    mode.add_argument("--run",   action="store_true",
                      help="Compute daily signals and rebalance via Alpaca")

    parser.add_argument("--factor-json", type=Path, default=FACTOR_JSON,
                        help=f"Path to factor library JSON (default: {FACTOR_JSON})")
    parser.add_argument("--dry-run", action="store_true",
                        help="Run mode: compute signals but skip order submission")
    parser.add_argument("--skip-hours-check", action="store_true",
                        help="Skip market hours guard (useful for testing)")

    args = parser.parse_args()

    if args.train:
        run_train(args.factor_json)
    else:
        run_daily(args.factor_json, dry_run=args.dry_run, skip_hours_check=args.skip_hours_check)


if __name__ == "__main__":
    main()
