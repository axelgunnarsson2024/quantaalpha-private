import logging
from pathlib import Path

import pandas as pd

from quantaalpha.backtest.custom_factor_calculator import CustomFactorCalculator
from quantaalpha.backtest.factor_loader import FactorLoader

logger = logging.getLogger(__name__)


def load_factor_list(json_path: Path) -> list[dict]:
    """Load factor dicts from all_factors_library.json using FactorLoader."""
    config = {
        "factor_source": {
            "type": "custom",
            "custom": {
                "json_files": [str(json_path)],
                "quality_filter": None,
                "max_factors": None,
            },
        }
    }
    loader = FactorLoader(config)
    _, custom_factors = loader.load_factors()
    logger.info(f"Loaded {len(custom_factors)} factors from {json_path.name}")
    return custom_factors


def compute_factors(data_df: pd.DataFrame, factor_list: list[dict]) -> pd.DataFrame:
    """
    Compute all factor expressions against data_df.

    data_df must have MultiIndex (datetime, instrument) and columns
    [$open, $high, $low, $close, $volume] — $return is added automatically
    by CustomFactorCalculator._prepare_data().

    Returns wide DataFrame: index=(datetime, instrument), columns=factor names.
    """
    calc = CustomFactorCalculator(
        data_df=data_df,
        cache_dir=None,
        auto_extract_cache=False,
    )

    results = {}
    for f in factor_list:
        name = f["factor_name"]
        expr = f["factor_expression"]
        series = calc.calculate_factor(name, expr)
        if series is not None:
            results[name] = series
        else:
            logger.warning(f"Skipped factor (computation failed): {name}")

    if not results:
        raise RuntimeError("All factors failed to compute — check expressions and data")

    factor_df = pd.DataFrame(results)
    logger.info(f"Computed {len(results)}/{len(factor_list)} factors successfully")
    return factor_df
