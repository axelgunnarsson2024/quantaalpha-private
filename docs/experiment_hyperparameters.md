# AlphaAgent Experiment Hyperparameter Configuration

> This document details all hyperparameter settings in `run_experiment.sh` and its related configuration files.

---

## Table of Contents

1. [Model Configuration](#1-model-configuration)
2. [Planning Configuration](#2-planning-configuration)
3. [Execution Configuration](#3-execution-configuration)
4. [Evolution Configuration](#4-evolution-configuration)
5. [Factor Generation Configuration](#5-factor-generation-configuration)
6. [Backtest Configuration](#6-backtest-configuration)
7. [Data Configuration](#7-data-configuration)
8. [Model Training Configuration](#8-model-training-configuration)
9. [Trading Strategy Configuration](#9-trading-strategy-configuration)
10. [LLM Configuration](#10-llm-configuration)
11. [Logging Configuration](#11-logging-configuration)
12. [Path Configuration](#12-path-configuration)

---

## 1. Model Configuration

### 1.1 LLM Model Presets

Switch models quickly via the `MODEL_PRESET` environment variable:

| Preset name | Reasoning model | Chat model | API endpoint |
| --- | --- | --- | --- |
| `gemini` | `google/gemini-3-pro-preview` | `google/gemini-3-pro-preview` | OpenRouter |
| `deepseek` | `deepseek/deepseek-v3.2` | `deepseek/deepseek-v3.2` | OpenRouter |
| `deepseek_aliyun` | `deepseek-v3.2` | `deepseek-v3.2` | Alibaba Cloud DashScope |
| `claude` | `anthropic/claude-sonnet-4.5` | `anthropic/claude-sonnet-4.5` | OpenRouter |
| `gpt` | `openai/gpt-5.2` | `openai/gpt-5.2` | OpenRouter |
| `qwen` | `qwen3-235b-a22b-instruct-2507` | `qwen3-235b-a22b-instruct-2507` | Alibaba Cloud DashScope |

### 1.2 Environment Variable Overrides

```bash
REASONING_MODEL=<model_name>   # Reasoning model
CHAT_MODEL=<model_name>        # Chat model
OPENAI_API_KEY=<api_key>       # API key
OPENAI_BASE_URL=<base_url>     # API endpoint
```

---

## 2. Planning Configuration

> Config file: `alphaagent/app/qlib_rd_loop/run_config.yaml`

| Parameter | Default | Type | Description |
| --- | --- | --- | --- |
| `enabled` | `true` | bool | Enable parallel planning |
| `num_directions` | **10** | int | 🔥 **Hyperparameter** — number of parallel exploration directions |
| `max_attempts` | `5` | int | Maximum planning retry attempts |
| `use_llm` | `true` | bool | Use LLM to generate directions |
| `allow_fallback` | `true` | bool | Fall back to built-in templates if LLM fails |
| `prompt_file` | `planning_prompts.yaml` | str | Planning prompt file path |

---

## 3. Execution Configuration

| Parameter | Default | Type | Description |
| --- | --- | --- | --- |
| `max_loops` | `11` | int | Maximum loop iterations |
| `steps_per_loop` | `5` | int | Steps per loop (fixed: propose / construct / calculate / backtest / feedback) |
| `step_n` | `null` | int | Total steps (highest priority — overrides `max_loops × steps_per_loop`) |
| `use_local` | `true` | bool | Use local environment for backtest (vs Docker) |
| `parallel_execution` | `false` | bool | Run branches in parallel using multiprocessing |
| `branch_log_root` | `/mnt/DATA/quantagent/AlphaAgent/log` | str | Branch log root directory |
| `branch_log_prefix` | `branch` | str | Branch log file prefix |

---

## 4. Evolution Configuration

> 🔥 Core hyperparameter section

| Parameter | Default | Type | Description |
| --- | --- | --- | --- |
| `enabled` | `true` | bool | Enable evolution mode |
| `mutation_enabled` | `true` | bool | Enable mutation phase |
| `crossover_enabled` | `true` | bool | Enable crossover phase |
| `max_rounds` | **11** | int | 🔥 **Hyperparameter** — max evolution rounds (including the original round) |
| `crossover_size` | **2** | int | 🔥 **Hyperparameter** — number of parents per crossover (2 or 3) |
| `crossover_n` | **10** | int | 🔥 **Hyperparameter** — crossover combinations generated per round |
| `parallel_enabled` | `false` | bool | Parallel execution within an evolution phase |
| `prefer_diverse_crossover` | `true` | bool | Prefer diverse crossover combinations |
| `parent_selection_strategy` | `best` | str | Parent selection strategy |
| `top_percent_threshold` | `0.3` | float | Top-percent threshold (used with `top_percent_plus_random`) |
| `fresh_start` | `true` | bool | Start from an empty trajectory pool |
| `cleanup_on_finish` | `false` | bool | Clean up trajectory pool after experiment |
| `prompt_file` | `evolution_prompts.yaml` | str | Evolution prompt file path |

### 4.1 Parent Selection Strategies

| Strategy | Description |
| --- | --- |
| `best` | Prioritize best-performing trajectories |
| `random` | Random selection |
| `weighted` | Performance-weighted sampling (higher performance = higher weight) |
| `weighted_inverse` | Inverse performance-weighted sampling (encourages exploring poor trajectories) |
| `top_percent_plus_random` | Top 30% guaranteed + remaining filled randomly |

### 4.2 Evolution Flow

```
Round 0: Original  → generate initial factors
Round 1: Mutation  → mutate existing factors
Round 2: Crossover → combine different factors
Round 3: Mutation
Round 4: Crossover
...
```

---

## 5. Factor Generation Configuration

| Parameter | Default | Type | Description |
| --- | --- | --- | --- |
| `factors_per_hypothesis` | **3** | int | 🔥 Factors generated per hypothesis |

### 5.1 Complexity Constraints

| Parameter | Default | Description |
| --- | --- | --- |
| `symbol_length_threshold` | **250** | 🔥 Max character length of a factor expression (key anti-overfitting parameter) |
| `base_features_threshold` | `6` | Max number of distinct base features ($close, $open, etc.) |
| `free_args_ratio_threshold` | `0.5` | Max ratio of free parameters (numeric constants / total nodes) |

### 5.2 Duplication Check

| Parameter | Default | Description |
| --- | --- | --- |
| `duplication.enabled` | `true` | Enable duplication check |
| `duplication.threshold` | `5` | Duplicate subtree size threshold |
| `duplication.factor_zoo_path` | `null` | Path to reference factor library |

---

## 6. Backtest Configuration

| Parameter | Default | Type | Description |
| --- | --- | --- | --- |
| `use_docker` | `false` | bool | Run backtest inside Docker |
| `timeout` | **800** | int | 🔥 Timeout per backtest run (seconds) |
| `qlib.config_name` | `conf.yaml` | str | Qlib config file name |

---

## 7. Data Configuration

> Config file: `alphaagent/scenarios/qlib/experiment/factor_template/conf.yaml`

### 7.1 Qlib Initialization

| Parameter | Value | Description |
| --- | --- | --- |
| `provider_uri` | `~/.qlib/qlib_data/cn_data` | Qlib data path |
| `region` | `cn` | Market region (cn / us) |

### 7.2 Market Configuration

| Parameter | Value | Description |
| --- | --- | --- |
| `market` | **csi300** | 🔥 Stock universe (CSI 300) |
| `benchmark` | **SH000300** | 🔥 Benchmark index (CSI 300 Index) |

### 7.3 Time Ranges

| Dataset | Range | Description |
| --- | --- | --- |
| **Full data** | 2016-01-01 ~ 2025-12-26 | Entire data range |
| **Train** | 2016-01-01 ~ 2020-12-31 | Model training (5 years) |
| **Validation** | 2021-01-01 ~ 2021-12-31 | Model validation (1 year) |
| **Test** | 2022-01-01 ~ 2025-12-26 | Backtest evaluation (~4 years) |

### 7.4 Data Processors

```yaml
learn_processors:
  - Fillna (feature)      # fill missing values
  - ProcessInf            # handle infinite values
  - DropnaLabel           # drop null labels
  - CSRankNorm (feature)  # cross-sectional rank normalization (features)
  - CSRankNorm (label)    # cross-sectional rank normalization (labels)

infer_processors:
  - Fillna (feature)
  - ProcessInf
  - CSRankNorm (feature)
  - CSRankNorm (label)
```

### 7.5 Label Definition

```python
label = "Ref($close, -2) / Ref($close, -1) - 1"  # T+2 daily return
```

---

## 8. Model Training Configuration (LGBModel)

> LightGBM hyperparameters

| Parameter | Default | Description |
| --- | --- | --- |
| `loss` | `mse` | Loss function |
| `learning_rate` | **0.05** | 🔥 Learning rate |
| `max_depth` | **8** | 🔥 Maximum tree depth |
| `num_leaves` | **210** | 🔥 Number of leaf nodes |
| `colsample_bytree` | `0.8879` | Column subsampling ratio |
| `subsample` | `0.8789` | Row subsampling ratio |
| `lambda_l1` | `205.6999` | L1 regularization |
| `lambda_l2` | `580.9768` | L2 regularization |
| `num_threads` | `20` | Parallel threads |
| `early_stopping_round` | **50** | 🔥 Early stopping rounds |
| `num_boost_round` | **500** | 🔥 Maximum boosting iterations |

---

## 9. Trading Strategy Configuration

### 9.1 TopkDropout Strategy

| Parameter | Default | Description |
| --- | --- | --- |
| `topk` | **50** | 🔥 Number of stocks to hold |
| `n_drop` | **5** | 🔥 Stocks eliminated per rebalance |

### 9.2 Transaction Costs

| Parameter | Default | Description |
| --- | --- | --- |
| `account` | `100000000` | Initial capital (¥100M) |
| `limit_threshold` | `0.095` | Price limit threshold (9.5%) |
| `deal_price` | `open` | Execution price (open) |
| `open_cost` | **0.0005** | 🔥 Buy cost (0.05%) |
| `close_cost` | **0.0015** | 🔥 Sell cost (0.15%) |
| `min_cost` | `5` | Minimum transaction cost (¥5) |

---

## 10. LLM Configuration

| Parameter | Default | Description |
| --- | --- | --- |
| `factor_mining_timeout` | `999999` | Total factor mining timeout (seconds) |
| `max_retries` | `3` | Maximum API call retries |
| `retry_delay` | `1.0` | Retry interval (seconds) |
| `json_mode_strict` | `true` | Strict JSON mode |

---

## 11. Logging Configuration

| Parameter | Default | Description |
| --- | --- | --- |
| `level` | `INFO` | Log level (DEBUG / INFO / WARNING / ERROR) |
| `save_snapshots` | `true` | Save intermediate session snapshots |
| `save_trajectory_pool` | `true` | Save trajectory pool to JSON |

---

## 12. Path Configuration

### 12.1 Workspace Paths

```bash
# Auto-generated (default)
WORKSPACE_PATH=/mnt/DATA/quantagent/QuantaAlpha/QuantaAlpha_workspace_exp_YYYYMMDD_HHMMSS
PICKLE_CACHE_FOLDER_PATH=/mnt/DATA/quantagent/AlphaAgent/pickle_cache_exp_YYYYMMDD_HHMMSS

# Manually specified
EXPERIMENT_ID=my_exp bash run_experiment.sh "direction"

# Shared directory mode
EXPERIMENT_ID=shared bash run_experiment.sh "direction"
```

### 12.2 Output Files

| File | Path | Description |
| --- | --- | --- |
| Factor library | `all_factors_library.json` | Default output |
| Factor library (suffixed) | `all_factors_library_{suffix}.json` | Output with custom suffix |
| Main config | `alphaagent/app/qlib_rd_loop/run_config.yaml` | Main config file |
| Backtest config | `alphaagent/scenarios/qlib/experiment/factor_template/conf.yaml` | Qlib config |

---

## Appendix: Key Hyperparameter Summary

| Category | Parameter | Default | Impact |
| --- | --- | --- | --- |
| **Planning** | `num_directions` | 10 | Number of initial exploration directions |
| **Evolution** | `max_rounds` | 11 | Total evolution rounds |
| **Evolution** | `crossover_size` | 2 | Parents per crossover |
| **Evolution** | `crossover_n` | 10 | Crossover combinations per round |
| **Factor** | `factors_per_hypothesis` | 3 | Factors per hypothesis |
| **Factor** | `symbol_length_threshold` | 250 | Max expression length |
| **Model** | `learning_rate` | 0.05 | LightGBM learning rate |
| **Model** | `num_boost_round` | 500 | LightGBM max iterations |
| **Strategy** | `topk` | 50 | Stocks held |
| **Strategy** | `n_drop` | 5 | Stocks rotated per rebalance |
| **Data** | `market` | csi300 | Stock universe |
| **Data** | `train` | 2016–2020 | Training set range |
| **Data** | `test` | 2022–2025 | Test set range |

---

*Generated: 2026-01-24*
