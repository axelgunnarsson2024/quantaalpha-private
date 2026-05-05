# Reproducing Paper Results

**Paper**: [QuantaAlpha: An Evolutionary Framework for LLM-Driven Alpha Mining](https://arxiv.org/abs/2602.07085)

Target results (CSI 300, GPT-5.2, 4-year test period 2022–2025):

| Metric | Paper Value |
|--------|------------|
| IC | 0.1501 |
| Rank IC | 0.1465 |
| ARR | 27.75% |
| MDD | 7.98% |
| Calmar Ratio | 3.4774 |

---

## Prerequisites

- Python 3.10+
- Conda
- ~5 GB disk space (data + results)
- LLM API access (GPT-5.2 for exact results; DeepSeek-V3.2 gives IC ~0.1338)

---

## Step 1: Install

```bash
git clone https://github.com/QuantaAlpha/QuantaAlpha.git
cd QuantaAlpha
conda create -n quantaalpha python=3.10
conda activate quantaalpha
SETUPTOOLS_SCM_PRETEND_VERSION=0.1.0 pip install -e .
pip install -r requirements.txt
```

---

## Step 2: Download Data

Two datasets are required: Qlib market data (backtesting) and pre-computed HDF5 price-volume files (factor mining).

```bash
pip install huggingface_hub
huggingface-cli download QuantaAlpha/qlib_csi300 --repo-type dataset --local-dir ./hf_data
```

Extract and place files:

```bash
# Qlib market data
unzip hf_data/cn_data.zip -d ./data/qlib

# HDF5 price-volume files
mkdir -p git_ignore_folder/factor_implementation_source_data
mkdir -p git_ignore_folder/factor_implementation_source_data_debug

cp hf_data/daily_pv.h5      git_ignore_folder/factor_implementation_source_data/daily_pv.h5
cp hf_data/daily_pv_debug.h5 git_ignore_folder/factor_implementation_source_data_debug/daily_pv.h5
```

> The debug HDF5 file must be renamed to `daily_pv.h5` in its directory.

---

## Step 3: Configure Environment

```bash
cp configs/.env.example .env
```

Edit `.env`:

```bash
QLIB_DATA_DIR=./data/qlib/cn_data
QLIB_PROVIDER_URI=./data/qlib/cn_data
DATA_RESULTS_DIR=./data/results
CONDA_ENV_NAME=quantaalpha

OPENAI_API_KEY=your-api-key
OPENAI_BASE_URL=https://api.openai.com/v1
CHAT_MODEL=gpt-4o          # paper used GPT-5.2; use best available
REASONING_MODEL=gpt-4o
```

---

## Step 4: Configure Experiment

Edit `configs/experiment.yaml` to match the paper's settings:

```yaml
planning:
  enabled: true
  num_directions: 10        # paper used 10 (default is 2)

execution:
  max_loops: 3

evolution:
  enabled: true
  mutation_enabled: true
  crossover_enabled: true
  max_rounds: 5             # paper ran up to ~12 iterations; 5 is a good start

factor:
  factors_per_hypothesis: 3 # paper used 3 (default is 1)
  complexity:
    symbol_length_threshold: 200
    base_features_threshold: 5
    free_args_ratio_threshold: 0.5

quality_gate:
  consistency_enabled: true # paper enabled this (default is false)
  complexity_enabled: true
  redundancy_enabled: true
  consistency_strict_mode: false
  max_correction_attempts: 3
```

### Scale vs. Cost Tradeoff

| Config | ~Tokens | ~Time | Expected IC |
|--------|---------|-------|-------------|
| 2 directions × 3 rounds × 1 factor | ~30K | 30–60 min | Baseline |
| 3 directions × 5 rounds × 3 factors | ~500K | 2–4 hours | Moderate |
| 10 directions × 5 rounds × 3 factors | ~2M | 8–16 hours | Near-paper |
| 10 directions × 12 rounds × 3 factors | ~5M | 20–40 hours | Paper level |

> Optimal convergence in the paper was at **11–12 iterations (~350 factors total)**. Beyond that, performance plateaus and MDD worsens.

---

## Step 5: Run Factor Mining

```bash
conda activate quantaalpha
./run.sh "Price-Volume Factor Mining"
```

Factors are saved to `all_factors_library.json` as they are mined. The run can be interrupted and resumed.

---

## Step 6: Run the Backtest

After mining, run the out-of-sample backtest (test period: 2022-01-01 to 2025-12-26):

```bash
# Custom factors only
python -m quantaalpha.backtest.run_backtest \
  -c configs/backtest.yaml \
  --factor-source custom \
  --factor-json all_factors_library.json

# Combined with Alpha158(20) baseline factors
python -m quantaalpha.backtest.run_backtest \
  -c configs/backtest.yaml \
  --factor-source combined \
  --factor-json all_factors_library.json
```

Results are saved to `data/results/backtest_v2_results/backtest_metrics.json`.

---

## Step 7: Transfer to CSI 500 / S&P 500 (Optional)

To replicate the zero-shot transfer results (160% / 137% cumulative excess return), edit `configs/backtest.yaml`:

```yaml
data:
  market: "csi500"        # or "sp500" for S&P 500
  provider_uri: ...        # point to the relevant Qlib dataset

backtest:
  backtest:
    benchmark: "SH000905" # CSI 500 benchmark (use SPX for S&P 500)
```

Then re-run the backtest command with the same `all_factors_library.json` — no re-mining needed.

---

## Notes

- **LLM choice matters**: GPT-5.2 (IC 0.1501) > DeepSeek-V3.2 (IC 0.1338) > Claude-4.5-Sonnet (IC 0.1111) based on paper Table 1.
- **Mutation is the most critical component**: removing it causes the largest performance drop (-0.0292 IC, -9.81% ARR) per the ablation study.
- **Factor pool maintenance**: factors are admitted only if their absolute correlation with existing pool factors is below 0.7. Pool is capped at 50% of all mined factors ranked by Rank IC.
- **Backtesting uses Qlib's TopkDropout strategy**: top 50 stocks, drop 5 per day, execute at next-day open price, 0.05% buy / 0.15% sell costs.
- **Do not run beyond ~12–15 iterations**: the paper found diminishing returns and increasing MDD after this point.
