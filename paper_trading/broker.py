import json
import logging
import time
from pathlib import Path

from paper_trading.config import (
    ALPACA_API_KEY,
    ALPACA_API_SECRET,
    ALPACA_PAPER_URL,
    POSITIONS_PATH,
    TOPK,
)

logger = logging.getLogger(__name__)


def get_client():
    """Return an authenticated Alpaca paper trading client."""
    from alpaca.trading.client import TradingClient

    if not ALPACA_API_KEY or not ALPACA_API_SECRET:
        raise EnvironmentError(
            "Set ALPACA_API_KEY and ALPACA_API_SECRET environment variables"
        )
    return TradingClient(
        api_key=ALPACA_API_KEY,
        secret_key=ALPACA_API_SECRET,
        paper=True,
    )


def get_current_positions(client) -> set[str]:
    """Return set of tickers currently held (ground truth from Alpaca API)."""
    positions = client.get_all_positions()
    return {p.symbol for p in positions}


def get_account_equity(client) -> float:
    account = client.get_account()
    return float(account.equity)


def execute_rebalance(buys: list[str], sells: list[str], client, topk: int = TOPK):
    """
    Submit sell orders first, wait for fills, then submit buys as notional orders.
    Each position targets equity / topk dollars.
    """
    from alpaca.trading.enums import OrderSide, TimeInForce
    from alpaca.trading.requests import MarketOrderRequest

    if not sells and not buys:
        logger.info("No rebalance needed")
        return

    # Step 1: sells
    for ticker in sells:
        try:
            client.submit_order(
                MarketOrderRequest(
                    symbol=ticker,
                    qty=None,
                    notional=None,
                    side=OrderSide.SELL,
                    time_in_force=TimeInForce.DAY,
                )
            )
            logger.info(f"  SELL submitted: {ticker}")
        except Exception as e:
            logger.warning(f"  SELL failed for {ticker}: {e}")

    if sells:
        logger.info("Waiting 30s for sell fills...")
        time.sleep(30)

    # Step 2: buys (equal notional per position)
    equity = get_account_equity(client)
    per_position = round(equity / topk, 2)

    for ticker in buys:
        try:
            client.submit_order(
                MarketOrderRequest(
                    symbol=ticker,
                    notional=per_position,
                    side=OrderSide.BUY,
                    time_in_force=TimeInForce.DAY,
                )
            )
            logger.info(f"  BUY  submitted: {ticker} (${per_position})")
        except Exception as e:
            logger.warning(f"  BUY failed for {ticker}: {e}")


def save_positions(holdings: set[str], path: Path = POSITIONS_PATH):
    with open(path, "w") as f:
        json.dump(sorted(holdings), f, indent=2)
    logger.debug(f"Saved {len(holdings)} positions to {path}")


def load_positions(path: Path = POSITIONS_PATH) -> set[str]:
    if not path.exists():
        return set()
    with open(path) as f:
        return set(json.load(f))
