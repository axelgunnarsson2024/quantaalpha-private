import pandas as pd


def topk_dropout(
    scores: pd.Series,
    current_holdings: set[str],
    topk: int = 50,
    n_drop: int = 5,
) -> tuple[list[str], list[str]]:
    """
    Pure TopkDropout logic. Returns (tickers_to_buy, tickers_to_sell).

    1. Rank all stocks by score descending → top_k_set
    2. Find held stocks that fell out of top_k → sell candidates
    3. Sell up to n_drop of those (lowest-scoring first)
    4. Buy top n_drop from top_k that are not already held
    """
    scores = scores.dropna().sort_values(ascending=False)
    top_k_set = set(scores.iloc[:topk].index.tolist())

    # Stocks to potentially sell: held but no longer in top-k
    sell_candidates = current_holdings - top_k_set
    if sell_candidates:
        # Sort sell candidates by score ascending (drop worst performers first)
        candidate_scores = scores.reindex(list(sell_candidates)).sort_values()
        sells = candidate_scores.index[:n_drop].tolist()
    else:
        sells = []

    # Stocks to buy: top of top-k not yet held
    buy_candidates = [t for t in scores.iloc[:topk].index if t not in current_holdings]
    buys = buy_candidates[:n_drop]

    return buys, sells
