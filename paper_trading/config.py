import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

# Paths
FACTOR_JSON     = REPO_ROOT / "data/factorlib/all_factors_library.json"
MODEL_PATH      = REPO_ROOT / "paper_trading/model.pkl"
POSITIONS_PATH  = REPO_ROOT / "paper_trading/positions.json"
TRADES_CSV      = REPO_ROOT / "paper_trading/trades.csv"
PNL_DB          = REPO_ROOT / "paper_trading/pnl.db"
SP500_TICKERS   = REPO_ROOT / "paper_trading/sp500_tickers.json"

# Data windows
TRAIN_START  = "2016-01-01"
TRAIN_END    = "2020-12-31"
VALID_START  = "2021-01-01"
VALID_END    = "2021-12-31"
LOOKBACK_DAYS = 65  # 60-day max rolling window + 5 buffer

# Portfolio (mirrors backtest.yaml TopkDropout)
TOPK   = 50
N_DROP = 5

# LightGBM — mirrored from configs/backtest.yaml
LGB_PARAMS = {
    "objective":              "mse",
    "learning_rate":          0.1,
    "max_depth":              8,
    "num_leaves":             210,
    "colsample_bytree":       0.8879,
    "subsample":              0.8789,
    "reg_alpha":              205.6999,
    "reg_lambda":             580.9768,
    "n_jobs":                 4,
    "seed":                   42,
    "min_child_samples":      100,
    "feature_fraction_bynode": 0.8,
    "verbose":                -1,
}
LGB_NUM_BOOST_ROUND     = 500
LGB_EARLY_STOPPING      = 50
LGB_LOG_EVAL_PERIOD     = 50

# Alpaca paper trading
ALPACA_API_KEY    = os.environ.get("ALPACA_API_KEY", "")
ALPACA_API_SECRET = os.environ.get("ALPACA_API_SECRET", "")
ALPACA_PAPER_URL  = "https://paper-api.alpaca.markets"

# Market hours guard (America/New_York)
MARKET_OPEN_HOUR   = 9
MARKET_OPEN_MINUTE = 30
MARKET_CLOSE_HOUR  = 16
