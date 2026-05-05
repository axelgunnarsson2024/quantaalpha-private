import logging
from pathlib import Path

import joblib
import lightgbm as lgb
import numpy as np
import pandas as pd

from paper_trading.config import (
    LGB_EARLY_STOPPING,
    LGB_LOG_EVAL_PERIOD,
    LGB_NUM_BOOST_ROUND,
    LGB_PARAMS,
    MODEL_PATH,
    TRAIN_END,
    VALID_END,
    VALID_START,
)

logger = logging.getLogger(__name__)


def cs_rank_norm(df: pd.DataFrame) -> pd.DataFrame:
    """Cross-sectional percentile rank per datetime — replicates Qlib CSRankNorm."""
    return df.groupby(level="datetime").rank(pct=True)


def compute_label(data_df: pd.DataFrame) -> pd.Series:
    """
    Next-day close return, cross-sectionally rank-normed.
    Label at time t = close[t+1] / close[t] - 1, then cs_rank_norm.
    """
    raw = (
        data_df["$close"]
        .groupby(level="instrument")
        .transform(lambda x: x.shift(-1) / x - 1)
    )
    raw.name = "label"
    normed = raw.groupby(level="datetime").rank(pct=True)
    return normed


def train(data_df: pd.DataFrame, factor_df: pd.DataFrame, model_path: Path = MODEL_PATH):
    """
    Train LightGBM on historical data and save model to model_path.

    Steps:
    1. Compute label (next-day return, cs_rank_normed)
    2. Apply cs_rank_norm to features
    3. Align features + label, drop NaN rows
    4. Split train / valid by date
    5. Train with early stopping on valid set
    6. Save {booster, feature_names} via joblib
    """
    logger.info("Computing label...")
    label = compute_label(data_df)

    logger.info("Normalising features...")
    features = cs_rank_norm(factor_df)

    # Align on common index and drop rows with any NaN
    combined = features.join(label, how="inner").dropna()

    feature_names = list(features.columns)
    X = combined[feature_names]
    y = combined["label"]

    train_mask = combined.index.get_level_values("datetime") <= TRAIN_END
    valid_mask = (
        (combined.index.get_level_values("datetime") >= VALID_START)
        & (combined.index.get_level_values("datetime") <= VALID_END)
    )

    X_train, y_train = X[train_mask], y[train_mask]
    X_valid, y_valid = X[valid_mask], y[valid_mask]

    logger.info(f"Train: {len(X_train)} rows, Valid: {len(X_valid)} rows")

    train_data = lgb.Dataset(X_train, label=y_train, feature_name=feature_names)
    valid_data = lgb.Dataset(X_valid, label=y_valid, feature_name=feature_names, reference=train_data)

    callbacks = [
        lgb.early_stopping(LGB_EARLY_STOPPING, verbose=False),
        lgb.log_evaluation(LGB_LOG_EVAL_PERIOD),
    ]

    logger.info("Training LightGBM...")
    booster = lgb.train(
        LGB_PARAMS,
        train_data,
        num_boost_round=LGB_NUM_BOOST_ROUND,
        valid_sets=[train_data, valid_data],
        valid_names=["train", "valid"],
        callbacks=callbacks,
    )

    # Compute validation IC as sanity check
    valid_pred = pd.Series(booster.predict(X_valid), index=X_valid.index)
    ic = _compute_ic(valid_pred, y_valid)
    logger.info(f"Validation IC: {ic:.4f}")

    bundle = {"booster": booster, "feature_names": feature_names}
    joblib.dump(bundle, model_path)
    logger.info(f"Model saved to {model_path}")
    return ic


def load_model(path: Path = MODEL_PATH) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Model not found at {path}. Run --train first.")
    return joblib.load(path)


def predict(today_factors: pd.DataFrame, model_bundle: dict) -> pd.Series:
    """
    Predict scores for today's stocks.

    today_factors: DataFrame indexed by instrument (or MultiIndex with single date).
    Returns pd.Series(ticker → score).
    """
    booster = model_bundle["booster"]
    feature_names = model_bundle["feature_names"]

    # Handle both single-level (instrument) and multi-level index
    if isinstance(today_factors.index, pd.MultiIndex):
        today_factors = today_factors.droplevel("datetime")

    # Reindex to trained feature set; fill missing with NaN (handled by LightGBM)
    X = today_factors.reindex(columns=feature_names)

    # Apply cross-sectional rank norm within today's cross-section
    X = X.rank(pct=True)

    scores = booster.predict(X)
    return pd.Series(scores, index=today_factors.index, name="score")


def _compute_ic(pred: pd.Series, label: pd.Series) -> float:
    """Cross-sectional mean IC across all dates."""
    combined = pd.DataFrame({"pred": pred, "label": label})
    daily_ic = combined.groupby(level="datetime").apply(
        lambda g: g["pred"].corr(g["label"])
    )
    return float(daily_ic.mean())
