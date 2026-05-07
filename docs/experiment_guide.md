# Quanta Alpha — Quantitative Factor Mining Experiment Guide

## Table of Contents
- [1. Project Overview](#1-project-overview)
- [2. Methodology](#2-methodology)
- [3. Main Experiment Walkthrough](#3-main-experiment-walkthrough)
- [4. Standalone Backtest Framework](#4-standalone-backtest-framework)
- [5. Evaluation Metrics](#5-evaluation-metrics)
- [6. Experiment Configuration & Hyperparameters](#6-experiment-configuration--hyperparameters)
- [7. Data & Backtest Settings](#7-data--backtest-settings)
- [8. Conclusions & Analysis](#8-conclusions--analysis)

---

## 1. Project Overview

### 1.1 Goals

**Quanta Alpha** is an LLM-driven system for automated quantitative factor discovery. Core objectives:

- **Automated factor discovery**: use LLMs to generate market hypotheses and translate them into computable factor expressions
- **Evolutionary optimization**: iteratively improve factor quality via Mutation and Crossover operations
- **End-to-end backtest validation**: evaluate factor predictive power and investment value using the Qlib framework

### 1.2 System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                   Quanta Alpha System Architecture              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   User Input (exploration direction)                             │
│         │                                                        │
│         ▼                                                        │
│   ┌──────────────┐                                               │
│   │   Planning   │ ──→ Generate N parallel exploration directions │
│   └──────────────┘                                               │
│         │                                                        │
│         ▼                                                        │
│   ┌──────────────────────────────────────────────────────────┐  │
│   │              Evolution Controller                         │  │
│   │  ┌──────────┐  ┌──────────┐  ┌──────────┐               │  │
│   │  │ Original │→│ Mutation │→│ Crossover│→ repeat...      │  │
│   │  └──────────┘  └──────────┘  └──────────┘               │  │
│   └──────────────────────────────────────────────────────────┘  │
│         │                                                        │
│         ▼                                                        │
│   ┌──────────────────────────────────────────────────────────┐  │
│   │           QuantAgentLoop (5-step cycle)                   │  │
│   │  1. factor_propose    → LLM generates market hypothesis   │  │
│   │  2. factor_construct  → LLM generates factor expressions  │  │
│   │  3. factor_calculate  → parse and compute factor values   │  │
│   │  4. factor_backtest   → Qlib backtest                     │  │
│   │  5. feedback          → LLM analysis + write to library   │  │
│   └──────────────────────────────────────────────────────────┘  │
│         │                                                        │
│         ▼                                                        │
│   ┌──────────────┐                                               │
│   │ Factor Library│ ──→ archive of all valid factors             │
│   │    JSON       │                                              │
│   └──────────────┘                                               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 1.3 Key Files

| File / Script | Purpose |
|-----------|----------|
| `run_experiment.sh` | Main entry script — activates the environment and calls `alphaagent mine` |
| `backtest_v2/run_backtest.py` | Standalone backtest tool for batch evaluation of the factor library |
| `run_config.yaml` | Main experiment config (planning, evolution, backtest parameters) |
| `backtest_v2/config.yaml` | Standalone backtest config |
| `all_factors_library_*.json` | Factor library output files |

---

## 2. Methodology

### 2.1 Core Method: LLM-Driven Evolutionary Factor Mining

Traditional factor mining relies on manual expertise and domain knowledge, which is inefficient and hard to scale. Quanta Alpha takes an innovative approach:

#### 2.1.1 Hypothesis-Driven

```
User Input (e.g., "momentum strategy")
        │
        ▼
   ┌─────────────────────────────────────────┐
   │  LLM generates a market hypothesis       │
   │  Example:                                │
   │  "The momentum effect of past-N-day      │
   │   returns is significant in A-shares;    │
   │   short-term momentum may reverse while  │
   │   medium-term momentum persists"         │
   └─────────────────────────────────────────┘
        │
        ▼
   ┌─────────────────────────────────────────┐
   │  LLM translates hypothesis into factor   │
   │  expressions, e.g.:                      │
   │  ($close - Ref($close, 5)) / Ref($close, 5)  │
   │  Rank(Mean($close/Ref($close,1)-1, 20))      │
   └─────────────────────────────────────────┘
```

#### 2.1.2 Evolutionary Optimization

Borrowing from genetic algorithms, factors are improved via **mutation** and **crossover**:

```
             ┌─────────────────────────────────────────────┐
             │            Evolution Flow                    │
             ├─────────────────────────────────────────────┤
             │                                             │
  Round 0    │   Original: N directions explored in        │
  (Original) │   parallel → generate N initial trajectories│
             │                                             │
             │              │                              │
             │              ▼                              │
             │                                             │
  Round 1    │   Mutation: "mutate" existing trajectories  │
  (Mutation) │   → generate orthogonal strategies          │
             │   → avoid re-exploring the same paths       │
             │                                             │
             │              │                              │
             │              ▼                              │
             │                                             │
  Round 2    │   Crossover: select K parent trajectories   │
  (Crossover)│   → combine advantages of different traces  │
             │   → produce new hybrid strategies           │
             │                                             │
             │              │                              │
             │              ▼                              │
             │                                             │
  Round 3+   │   Continue: Mutation → Crossover → ...      │
             │   until maximum rounds reached              │
             │                                             │
             └─────────────────────────────────────────────┘
```

### 2.2 Methodology Advantages

| Advantage | Description |
|------|------|
| **Interpretability** | LLM-generated factors come with hypothesis explanations, making factor logic transparent |
| **Diversity** | Evolutionary mechanism ensures factor diversity and avoids local optima |
| **Automation** | Fully automated pipeline with minimal manual intervention |
| **Iterative improvement** | Feedback mechanism lets the system learn from failures and continuously improve |

---

## 3. Main Experiment Walkthrough

### 3.1 Launch Commands

```bash
# Basic usage
./run_experiment.sh "your exploration direction"

# Examples
./run_experiment.sh "short-term reversal factors based on price-volume relationships"
./run_experiment.sh "market sentiment factors using volatility and trading volume"
```

### 3.2 The 5-Step Cycle

Each round of exploration consists of 5 core steps:

#### Step 1: factor_propose (Hypothesis Generation)
- **Input**: exploration direction + historical trajectory (trace)
- **Process**: call LLM to generate a market hypothesis
- **Output**: structured hypothesis description
- **Core module**: `QuantAgentHypothesisGen`

```python
# Pseudo-code
hypothesis = llm.generate(
    prompt="""
    Given the following exploration direction, generate a testable market hypothesis:
    Direction: {direction}
    Historical experience: {trace.history}
    
    Describe:
    1. Core logic of the hypothesis
    2. Expected market phenomenon
    3. Possible validation methods
    """
)
```

#### Step 2: factor_construct (Factor Construction)
- **Input**: market hypothesis
- **Process**: LLM translates hypothesis into 2–3 factor expressions
- **Output**: list of factor expressions
- **Core module**: `QuantAgentHypothesis2FactorExpression`

```
# Factor expression syntax examples
$close                          # Close price
Ref($close, 5)                  # Close price 5 days ago
Mean($volume, 20)               # 20-day average volume
Rank($close / Ref($close, 1) - 1)  # Daily return rank
Std($close / Ref($close, 1) - 1, 20)  # 20-day return std dev
```

#### Step 3: factor_calculate (Factor Computation)
- **Input**: factor expressions
- **Process**: parse expressions and compute factor values
- **Output**: factor value matrix (time × stocks)
- **Core module**: `QlibFactorParser`

##### 3.1 Computation Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     Factor Computation Pipeline                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   Factor expression input                                                │
│   e.g.: "RANK(DELTA($close, 5) / TS_STD($close, 20))"                  │
│         │                                                                │
│         ▼                                                                │
│   ┌──────────────────────────────────────────────────────────────────┐  │
│   │  1. Expression pre-processing (expr_parser.py)                    │  │
│   │     - Bracket balance check                                        │  │
│   │     - Invalid operator check                                       │  │
│   │     - Unary minus pre-processing ("* -$close" → "* (-1*$close)")  │  │
│   └──────────────────────────────────────────────────────────────────┘  │
│         │                                                                │
│         ▼                                                                │
│   ┌──────────────────────────────────────────────────────────────────┐  │
│   │  2. Expression parsing (pyparsing library)                         │  │
│   │     - Build AST (abstract syntax tree)                             │  │
│   │     - Operator precedence: * / → + - → > < >= <= == != → && → ||  │  │
│   │     - Convert infix to function-call form                          │  │
│   │       e.g.: "$close + $open" → "ADD($close, $open)"               │  │
│   └──────────────────────────────────────────────────────────────────┘  │
│         │                                                                │
│         ▼                                                                │
│   ┌──────────────────────────────────────────────────────────────────┐  │
│   │  3. Factor validation (factor_regulator.py)                        │  │
│   │     - Parseability check                                            │  │
│   │     - Duplicate subtree detection (vs existing factor library)      │  │
│   │     - Complexity constraints:                                        │  │
│   │       · Symbol Length (SL) ≤ 300                                   │  │
│   │       · Base Feature Count (ER) ≤ 6                                │  │
│   │       · Free parameter ratio < 50%                                  │  │
│   └──────────────────────────────────────────────────────────────────┘  │
│         │                                                                │
│         ▼                                                                │
│   ┌──────────────────────────────────────────────────────────────────┐  │
│   │  4. Load market data (Qlib)                                        │  │
│   │     - Data source: daily_pv.h5 (daily bar data)                    │  │
│   │     - Contains: $open, $high, $low, $close, $volume                │  │
│   │     - Index: MultiIndex (instrument, datetime)                      │  │
│   └──────────────────────────────────────────────────────────────────┘  │
│         │                                                                │
│         ▼                                                                │
│   ┌──────────────────────────────────────────────────────────────────┐  │
│   │  5. Recursive factor computation (function_lib.py)                 │  │
│   │     - Variable substitution: "$close" → "df['$close']"             │  │
│   │     - Execute parsed expression via eval()                          │  │
│   │     - All functions automatically apply groupby('instrument')       │  │
│   └──────────────────────────────────────────────────────────────────┘  │
│         │                                                                │
│         ▼                                                                │
│   ┌──────────────────────────────────────────────────────────────────┐  │
│   │  6. Result output & caching                                        │  │
│   │     - Output: result.h5 (HDF5 format)                              │  │
│   │     - Index: MultiIndex (instrument, datetime)                      │  │
│   │     - dtype: float64                                                │  │
│   └──────────────────────────────────────────────────────────────────┘  │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

##### 3.2 Expression Parser Implementation

The expression parser is built on **pyparsing** and supports arithmetic, comparison, logical, and conditional expressions:

```python
# Core parsing logic (expr_parser.py)

# 1. Define basic elements
var = Combine(Optional("$") + Word(alphas, alphanums + "_"))  # variables: $close, volume
number = Regex(r"[+-]?(\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?")   # numbers: 1.5, -3, 1e-8

# 2. Define operator precedence (low to high)
expr = infixNotation(operand, [
    (mul_div,      2, LEFT,  parse_arith_op),      # * /
    (add_minus,    2, LEFT,  parse_arith_op),      # + -
    (comparison,   2, LEFT,  parse_comparison_op),  # > < >= <= == !=
    (logical_and,  2, LEFT,  parse_logical),        # && &
    (logical_or,   2, LEFT,  parse_logical),        # || |
    (conditional,  3, RIGHT, parse_conditional)     # ? :
])

# 3. Operators converted to function calls
# e.g.: "$close + $open"  →  "ADD($close, $open)"
#       "$close > $open"  →  "GT($close, $open)"
#       "A ? B : C"       →  "WHERE(A, B, C)"
```

##### 3.3 Supported Factor Function Library

The system ships a rich set of built-in functions (`function_lib.py`):

**Time-series functions (TS_*)** — grouped by instrument, computed along the time axis

| Function | Description | Example |
|------|------|------|
| `DELTA(df, p)` | p-period difference | `DELTA($close, 5)` — 5-day close change |
| `DELAY(df, p)` | Lag by p periods | `DELAY($close, 1)` — yesterday's close |
| `TS_MEAN(df, p)` | p-period rolling mean | `TS_MEAN($volume, 20)` — 20-day avg volume |
| `TS_STD(df, p)` | p-period rolling std dev | `TS_STD($close, 20)` — 20-day volatility |
| `TS_MAX(df, p)` | p-period rolling max | `TS_MAX($high, 10)` — 10-day high |
| `TS_MIN(df, p)` | p-period rolling min | `TS_MIN($low, 10)` — 10-day low |
| `TS_RANK(df, p)` | p-period rolling rank | `TS_RANK($close, 20)` — 20-day rank |
| `TS_CORR(df1, df2, p)` | p-period rolling correlation | `TS_CORR($close, $volume, 20)` |
| `TS_SUM(df, p)` | p-period rolling sum | `TS_SUM($volume, 5)` — 5-day cumulative volume |
| `TS_ARGMAX(df, p)` | Position of max value | `TS_ARGMAX($close, 20)` — days since 20-day high |
| `TS_ARGMIN(df, p)` | Position of min value | `TS_ARGMIN($close, 20)` — days since 20-day low |
| `TS_PCTCHANGE(df, p)` | p-period return | `TS_PCTCHANGE($close, 5)` — 5-day return |

**Cross-sectional functions (CS_*)** — grouped by date, computed across stocks

| Function | Description | Example |
|------|------|------|
| `RANK(df)` | Cross-sectional rank (percentile) | `RANK($close)` |
| `ZSCORE(df)` | Cross-sectional z-score | `ZSCORE($volume)` |
| `MEAN(df)` | Cross-sectional mean | `MEAN($close)` — market-wide average price |
| `STD(df)` | Cross-sectional std dev | `STD($close)` — market-wide price dispersion |
| `SCALE(df)` | Cross-sectional scaling | `SCALE($close)` — normalization |

**Math functions**

| Function | Description | Example |
|------|------|------|
| `ABS(df)` | Absolute value | `ABS(DELTA($close, 1))` |
| `LOG(df)` | Natural log | `LOG($volume)` |
| `SQRT(df)` | Square root | `SQRT($volume)` |
| `SIGN(df)` | Sign function | `SIGN(DELTA($close, 1))` |
| `POW(df, n)` | Power | `POW($close, 2)` |
| `EXP(df)` | Exponential | `EXP($close / 100)` |

**Technical indicator functions**

| Function | Description | Example |
|------|------|------|
| `SMA(df, m)` | Simple moving average | `SMA($close, 20)` |
| `EMA(df, p)` | Exponential moving average | `EMA($close, 12)` |
| `WMA(df, p)` | Weighted moving average | `WMA($close, 10)` |
| `MACD(price, s, l)` | MACD indicator | `MACD($close, 12, 26)` |
| `RSI(price, p)` | Relative strength index | `RSI($close, 14)` |
| `BB_UPPER/MIDDLE/LOWER` | Bollinger Bands | `BB_UPPER($close, 20)` |
| `DECAYLINEAR(df, p)` | Linear decay weighting | `DECAYLINEAR($close, 10)` |

**Regression functions**

| Function | Description | Example |
|------|------|------|
| `REGBETA(y, x, p)` | Rolling regression coefficient | `REGBETA($close, $volume, 20)` |
| `REGRESI(y, x, p)` | Rolling regression residual | `REGRESI($close, MEAN($close), 20)` |

**Logic & conditional functions**

| Function | Description | Example |
|------|------|------|
| `GT(a, b)` | Greater than | `GT($close, $open)` |
| `LT(a, b)` | Less than | `LT($close, DELAY($close, 1))` |
| `AND(a, b)` | Logical AND | `AND(GT($close, $open), GT($volume, 1e8))` |
| `OR(a, b)` | Logical OR | `OR(GT($close, $open), LT($low, $open))` |
| `WHERE(cond, t, f)` | Conditional selection | `WHERE(GT($close, $open), $high, $low)` |

##### 3.4 Factor Complexity Regularization

To prevent overly complex factors or duplication with existing ones, the system implements complexity regularization (`FactorRegulator`):

```
Complexity penalty: R_g(f, h) = α₁·SL(f) + α₂·PC(f) + α₃·ER(f, h)

Where:
- SL(f): Symbol Length — character count of the expression
- PC(f): Parameter Complexity — ratio of free parameters
- ER(f, h): Expression Redundancy — number of distinct base features
```

**Validation rules**:

| Metric | Threshold | Description |
|------|------|------|
| Symbol Length (SL) | ≤ 300 | Expression must not be too long |
| Base Feature Count (ER) | ≤ 6 | At most 6 distinct raw features |
| Free parameter ratio | < 50% | Numeric constants must not dominate |
| Duplicate subtree size | ≤ 8 | Overlap with existing factors must be small |

##### 3.5 Computation Execution & Caching

Final factor computation uses Python's `eval()`:

```python
# Compute template (template.jinja2)
def calculate_factor(expr: str, name: str):
    # 1. Load data
    df = pd.read_hdf('./daily_pv.h5', key='data')
    
    # 2. Symbol substitution
    expr = parse_symbol(expr, df.columns)   # TRUE → True, $close → close
    expr = parse_expression(expr)            # parse into function-call form
    
    # 3. Variable substitution
    for col in df.columns:
        expr = expr.replace(col[1:], f"df['{col}']")  # close → df['$close']
    
    # 4. Execute
    df[name] = eval(expr)
    result = df[name].astype(np.float64)
    
    # 5. Save result
    result.to_hdf('result.h5', key='data')
```

**Caching**:
- Results are saved in HDF5 format (`result.h5`)
- Workspace path: `/mnt/DATA/quantagent/QuantaAlpha/QuantaAlpha_workspace/{UUID}/`
- The standalone backtest framework can reuse these results via cache extraction tools

#### Step 4: factor_backtest (Factor Backtest)
- **Input**: computed factor values
- **Process**: ML-based backtest using Qlib
- **Output**: backtest metrics (IC, ICIR, returns, etc.)
- **Core module**: `QlibFactorRunner`

```yaml
# Main program backtest config (conf.yaml)
Train:      2016-01-01 ~ 2020-12-31  # 5 years
Validation: 2021-01-01 ~ 2021-12-31  # 1 year
Test:       2022-01-01 ~ 2025-12-26  # ~4 years

Model:    LightGBM
Strategy: TopkDropoutStrategy (Top50, Drop5)
```

#### Step 5: feedback (Feedback & Library Write)
- **Input**: backtest results + hypothesis
- **Process**: LLM analyzes results and generates feedback
- **Output**: feedback report + factor written to library
- **Core module**: `QuantAgentQlibFactorHypothesisExperiment2Feedback`

```python
# Factor library entry structure
factor_entry = {
    "factor_name": "momentum_5d",
    "factor_expression": "($close - Ref($close, 5)) / Ref($close, 5)",
    "hypothesis": "Short-term momentum effect...",
    "direction": "momentum strategy",
    "evolution_phase": "original" | "mutation" | "crossover",
    "metrics": {
        "RankIC": 0.05,
        "RankICIR": 0.8,
        "annualized_return": 0.15,
        ...
    }
}
```

### 3.3 Evolution Controller

The `EvolutionController` manages the entire evolutionary process:

```
┌─────────────────────────────────────────────────────────────┐
│                  Evolution Controller                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  TrajectoryPool                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Trajectory 1: direction=0, phase=original, ic=0.03  │   │
│  │ Trajectory 2: direction=1, phase=original, ic=0.05  │   │
│  │ Trajectory 3: direction=0, phase=mutation, ic=0.04  │   │
│  │ Trajectory 4: parents=[1,2], phase=crossover, ic=0.06│   │
│  │ ...                                                  │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
│  Task scheduling logic                                       │
│  ├─ Original:  create initial tasks for each planning dir.  │
│  ├─ Mutation:  generate mutation tasks for each trajectory  │
│  └─ Crossover: select K parent combos, generate crossovers  │
│                                                              │
│  Parent selection strategies                                 │
│  ├─ best:     prioritize best-performing trajectories        │
│  ├─ weighted: performance-weighted sampling (worse = more    │
│  │            likely to be selected, encouraging exploration)│
│  └─ random:   random selection                               │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**Crossover evaluation mechanism**

**1. Visible metrics**

The crossover evaluator can see 7 metrics per trajectory:

| Metric | Description | Use |
|--------|-------------|-----|
| IC | Information Coefficient | Factor–return correlation |
| ICIR | IC Information Ratio | IC stability |
| RankIC | Rank IC | More robust factor correlation |
| RankICIR | Rank IC Information Ratio | RankIC stability |
| annualized_return | Annualized excess return | Strategy profitability |
| information_ratio | Information Ratio | Risk-adjusted return |
| max_drawdown | Maximum drawdown | Strategy risk |

**2. Primary evaluation metric**

`RankIC` is used as the primary metric (`get_primary_metric()` method):

```python
def get_primary_metric(self) -> Optional[float]:
    """Get the primary metric (RankIC) for comparison."""
    return self.backtest_metrics.get("RankIC")
```

**3. Where metrics drive decisions**

| Decision point | How metrics are used |
|----------------|----------------------|
| Parent selection | `get_primary_metric()` (RankIC) used for sorting / weighting |
| Pair scoring | Average RankIC used in `select_crossover_pairs` |
| Diversity preference | Combines direction diversity + phase diversity + avg performance |

**4. Trajectory information visible to the LLM**

When generating crossover prompts, the LLM sees:

```
### Parent 1: Original Round
**Direction ID**: 0
**Hypothesis**: Price-volume factor mining...
**Factors**:
  - ROC60_Factor: RANK(TS_PCTCHANGE($close, 60))...
**Metrics**:
  - IC: 0.0053
  - ICIR: 0.0418
  - RankIC: 0.0220
  - RankICIR: 0.1789
  - annualized_return: 0.068
  - information_ratio: 1.12
  - max_drawdown: -0.05
**Feedback**: The results show...
```

**5. Crossover evaluation flow**

```
┌─────────────────────────────────────────────────────────────────┐
│                    Crossover Evaluation Flow                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Candidate trajectory pool (from previous rounds)            │
│     ├── Trajectory A: RankIC=0.22, direction=0, phase=original  │
│     ├── Trajectory B: RankIC=0.18, direction=1, phase=original  │
│     ├── Trajectory C: RankIC=0.25, direction=0, phase=mutation  │
│     └── Trajectory D: RankIC=0.15, direction=1, phase=mutation  │
│                                                                  │
│  2. Filter by parent_selection_strategy                          │
│     ├── best:                    sort by RankIC desc, take Top-N │
│     ├── weighted:                higher RankIC = higher weight   │
│     ├── weighted_inverse:        lower RankIC = higher weight    │
│     └── top_percent_plus_random: top 30% guaranteed + random    │
│                                                                  │
│  3. Generate pairs and score                                     │
│     ├── Pair [A, C] → score = diversity + avg_metric            │
│     ├── Pair [A, D] → score = ...                               │
│     └── ...                                                      │
│                                                                  │
│  4. Select Top-N pairs as crossover parents                      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 4. Standalone Backtest Framework

### 4.1 Purpose

The backtest inside the main experiment (`factor_backtest`) is designed for rapid single-factor evaluation. The standalone framework (`backtest_v2`) is used for:

1. **Batch evaluation**: uniform backtest across the entire factor library
2. **Long-horizon validation**: longer test period (2022–2025) to verify factor stability
3. **Portfolio effect**: assess overall performance of multi-factor combinations
4. **Benchmarking**: compare against the official Qlib factor library (Alpha158)

### 4.2 Backtest Configuration

```yaml
# backtest_v2/config.yaml key settings

Data:
  Source:  ~/.qlib/qlib_data/cn_data
  Market:  csi300 (CSI 300 constituents)
  Range:   2016-01-01 ~ 2025-12-26

Dataset splits:
  Train:      2016-01-01 ~ 2020-12-31  # learn historical patterns
  Validation: 2021-01-01 ~ 2021-12-31  # hyperparameter tuning
  Test:       2022-01-01 ~ 2025-12-26  # out-of-sample evaluation

Model:
  Type:           LightGBM
  learning_rate:  0.1
  max_depth:      8
  num_leaves:     210
  early_stopping: 50
  max_iterations: 500

Strategy: TopkDropoutStrategy
  - topk:   50   # hold top-50 ranked stocks
  - n_drop: 5    # remove 5 lowest-ranked each rebalance

Transaction costs:
  Buy:     0.05%
  Sell:    0.15%
  Minimum: ¥5
```

### 4.3 Usage

```bash
# Single factor library backtest
python backtest_v2/run_backtest.py \
    -c backtest_v2/config.yaml \
    --factor-source custom \
    --factor-json /path/to/factors.json

# Compare against Alpha158
python backtest_v2/run_backtest.py \
    -c backtest_v2/config.yaml \
    --factor-source alpha158_20

# Batch backtest
./batch_backtest.sh
```

### 4.4 Comparison: Main vs. Standalone Backtest

| Feature | Main program backtest | Standalone framework |
|------|---------------|--------------|
| Purpose | Rapid single-factor evaluation | Batch evaluation of factor library |
| Test period | 2021 (validation set) | 2022–2025 (test set) |
| Factors per run | 2–3 per round | Entire factor library |
| Caching | Auto-cached to workspace | Separate cache directory |
| Output | Written to factor library JSON | Standalone metrics JSON |

---

## 5. Evaluation Metrics

### 5.1 Important Note: All Return Metrics Are Excess Returns

⚠️ **Note**: Return metrics output by the backtest framework (`annualized_return`, `max_drawdown`, etc.) are **all excess returns** — performance relative to the benchmark (CSI 300 Index), not absolute returns.

**Formula**:
```python
excess_return = portfolio_return - bench_return - cost
```

All risk analysis metrics (annualized return, max drawdown, information ratio, etc.) are computed from this excess return series.

### 5.2 Predictive Power Metrics

#### IC (Information Coefficient)
```
Definition: Pearson correlation between factor values and future returns
Range: [-1, 1]
Interpretation:
  IC > 0.03: factor has some predictive power
  IC > 0.05: factor has strong predictive power
  IC > 0.10: factor has very strong predictive power (rare)

Formula:
  IC_t = Corr(Factor_t, Return_{t+1})
  IC   = Mean(IC_t)  # averaged over all time periods
```

#### ICIR (IC Information Ratio)
```
Definition: ratio of IC mean to IC std dev
Formula: ICIR = Mean(IC) / Std(IC)
Interpretation:
  ICIR > 0.5: factor prediction is stable
  ICIR > 1.0: factor prediction is very stable

Note: a high but unstable IC may be inferior to a moderate but stable one
```

#### Rank IC
```
Definition: Spearman correlation between factor ranks and return ranks
Advantage: more robust to outliers; better suited for real investment contexts
```

#### Rank ICIR
```
Definition: ratio of Rank IC mean to Rank IC std dev
Formula: RankICIR = Mean(RankIC) / Std(RankIC)
```

### 5.3 Return Metrics (All Excess Returns)

#### Excess Annualized Return
```
Definition: strategy's annualized excess return relative to benchmark
Formula: Ann_Excess_Return = (1 + Total_Excess_Return)^(252/Trading_Days) - 1
Example:
  0.18 (18%) means the strategy outperforms the benchmark by 18% per year

Note: transaction costs are already deducted
```

#### Information Ratio
```
Definition: excess return divided by tracking error
Formula: IR = Mean(Excess_Return) / Std(Excess_Return) × √252
Interpretation:
  IR > 1.0: strategy significantly outperforms benchmark
  IR > 2.0: excellent strategy performance

Meaning: excess return earned per unit of tracking error risk
```

#### Excess Maximum Drawdown
```
Definition: largest peak-to-trough decline of the excess return curve
Formula: MDD = min((Excess_Cumulative_t - Excess_Peak) / Excess_Peak)
Example:
  -0.09 (-9%) means excess returns fell at most 9% from peak

Note: this is the drawdown relative to the benchmark, not the absolute portfolio drawdown
```

#### Calmar Ratio
```
Definition: excess annualized return divided by absolute max drawdown
Formula: Calmar = Ann_Excess_Return / |MDD|
Interpretation:
  Calmar > 1.0: decent risk-return ratio
  Calmar > 2.0: excellent risk-return ratio
```

### 5.4 Example Metric Interpretation

Actual backtest results (`QA_phase_mutation` factor library):

```json
{
  "IC": 0.1277,                    // Very strong predictive power
  "ICIR": 0.8738,                  // Stable prediction
  "Rank IC": 0.1242,               // Strong rank-based predictive power
  "Rank ICIR": 0.8566,             // Stable rank prediction
  "annualized_return": 0.1827,     // Excess annualized return 18.27%
  "information_ratio": 2.2588,     // Information ratio 2.26
  "max_drawdown": -0.0894,         // Excess max drawdown 8.94%
  "calmar_ratio": 2.0447           // Calmar ratio 2.04
}
```

**Summary assessment**:
- This factor library performed excellently over the 2022–2025 test period
- IC > 0.12 indicates the factor combination has very strong return predictive power
- **Excess annualized return 18.27%**: strategy outperforms CSI 300 by 18.27% per year on average (after transaction costs)
- **Information ratio 2.26**: earns 2.26% excess return per 1% of tracking error (IR > 2 is generally considered excellent)
- **Excess max drawdown 8.94%**: maximum decline relative to benchmark is kept under 9%
- **Calmar ratio 2.04**: excess return is 2× the max drawdown — a good risk-return profile

### 5.5 Benchmark Comparison Summary

| Metric type | Specific metric | How it compares to benchmark |
|----------|----------|--------------|
| Predictive power | IC, ICIR, Rank IC, Rank ICIR | Correlation between factor and returns computed directly |
| Return | annualized_return | **Excess** annualized = portfolio annualized − benchmark annualized − costs |
| Risk | max_drawdown | Max drawdown of the **excess** return curve |
| Combined | information_ratio, calmar_ratio | Computed from excess returns |

**Benchmark settings**:
```yaml
benchmark: SH000300  # CSI 300 Index
market: csi300       # CSI 300 constituents
```

---

## 6. Experiment Configuration & Hyperparameters

### 6.1 Core Hyperparameters

#### Planning Phase
```yaml
planning:
  num_directions: 10    # Number of parallel exploration directions
                        # Larger → broader initial exploration, but higher resource use
                        # Recommended: 5–15
```

#### Evolution Phase
```yaml
evolution:
  max_rounds: 5         # Maximum number of evolution rounds
                        # Larger → deeper exploration, but longer runtime
                        # Recommended: 3–7
  
  crossover_size: 2     # Number of parents per crossover
                        # 2: pairwise crossover (most common)
                        # 3: three-way crossover (more diversity)
  
  crossover_n: 10       # Crossover combinations generated per round
                        # Larger → broader crossover exploration
                        # Recommended: 5–15
  
  parent_selection_strategy: best  # Parent selection strategy
                        # best:     prioritize best trajectories
                        # weighted: weighted sampling (encourages exploration)
                        # random:   random selection
```

#### Execution Phase
```yaml
execution:
  max_loops: 7          # Maximum loop iterations per trajectory
                        # Total steps = max_loops × 5
  
  steps_per_loop: 5     # Fixed at 5 (the 5-step cycle)
```

### 6.2 Configuration Presets

**Exploration mode** (breadth-first):
```yaml
planning:
  num_directions: 15
evolution:
  max_rounds: 3
  crossover_n: 15
  parent_selection_strategy: weighted
```

**Deep mode** (depth-first):
```yaml
planning:
  num_directions: 5
evolution:
  max_rounds: 7
  crossover_n: 5
  parent_selection_strategy: best
```

**Balanced mode** (recommended):
```yaml
planning:
  num_directions: 10
evolution:
  max_rounds: 5
  crossover_n: 10
  parent_selection_strategy: best
```

---

## 7. Data & Backtest Settings

### 7.1 Data Source

```
Source: Qlib China A-share data
Path:   ~/.qlib/qlib_data/cn_data

Contains:
- Daily OHLCV: open, high, low, close, volume
- Fundamental data: market cap, valuation, etc.
- CSI 300 constituent stock list
```

### 7.2 Market Settings

```yaml
Market:    csi300   (CSI 300 constituents)
Benchmark: SH000300 (CSI 300 Index)

Rationale:
- Good liquidity, low transaction costs
- Representative; covers core blue-chip stocks
- High data quality with few outliers
```

### 7.3 Time Split

```
┌───────────────────────────────────────────────────────────────┐
│                          Timeline                             │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│  2016        2020        2021        2022        2025         │
│    │──────────┼───────────┼───────────┼───────────┤          │
│    │  Train   │  Validate │           Test        │          │
│    │  5 years │  1 year   │         4 years       │          │
│    │          │           │                       │          │
│    │  Learn   │  Tune     │  Out-of-sample eval   │          │
│    │  history │           │  (final assessment)   │          │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

**Design rationale**:
- **Train (2016–2020)**: 5 years of data is sufficient for the model to learn market patterns
- **Validation (2021)**: prevents overfitting; used for early stopping and hyperparameter tuning
- **Test (2022–2025)**: completely out-of-sample; evaluates genuine generalization

### 7.4 Trading Strategy

```yaml
Strategy: TopkDropoutStrategy
Parameters:
  topk:   50   # hold the 50 highest-ranked stocks
  n_drop: 5    # remove the 5 lowest-ranked stocks each rebalance

Logic:
1. Each trading day, compute predicted scores for all stocks
2. Build portfolio from the top-50 ranked stocks
3. At each rebalance:
   - Retain stocks that remain in the Top 50
   - Sell the 5 lowest-ranked holdings
   - Buy newly promoted Top-50 entries
4. Equal-weight positions

Advantages:
- Avoids excessive trading (only removes the worst)
- Maintains portfolio stability
- Reduces transaction costs
```

---

## 8. Conclusions & Analysis

### 8.1 Experiment Design Summary

1. **Input**: user provides an exploration direction (e.g., "momentum strategy", "value factor")
2. **Process**:
   - Planning generates 10 parallel directions
   - 5 evolution rounds (Original → Mutation → Crossover → Mutation → Crossover)
   - 7 loops per round, each generating 2–3 factors
3. **Output**: factor library JSON (hundreds of validated factors)

### 8.2 Key Findings

#### Impact of Evolution Phase on Factor Quality

| Evolution phase | Factor characteristics | Typical performance |
|----------|----------|----------|
| Original | Basic exploration | Wide IC distribution; contains many noise factors |
| Mutation | Targeted improvement | Builds on original trajectories; slight IC improvement |
| Crossover | Combination innovation | Merges advantages of multiple directions; can yield breakthrough factors |

#### Factor Screening Strategies
- **Sort by RankIC**: select factors with the strongest predictive power
- **Phase filtering**: factors from different phases may have different characteristics
- **Random sampling**: validate overall factor library quality

### 8.3 Practical Recommendations

1. **First run**: use balanced mode configuration and run the full pipeline
2. **Benchmark comparison**: always compare against Alpha158
3. **Multiple validations**: validate across different time windows and markets
4. **Factor screening**: focus on factors with RankIC > 0.03 and ICIR > 0.5

### 8.4 Limitations & Improvement Directions

| Limitation | Possible improvement |
|--------|-----------|
| LLM-generated factors may be biased | Add stronger factor regularization constraints |
| Backtest may overfit | Use more out-of-sample validation windows |
| High computational resource consumption | Optimize caching; incremental computation |
| Simplified transaction costs | Incorporate more realistic slippage models |

---

## Appendix

### A. Quick Command Reference

```bash
# Run main experiment
./run_experiment.sh "your exploration direction"

# Standalone backtest
python backtest_v2/run_backtest.py -c backtest_v2/config.yaml \
    --factor-source custom \
    --factor-json /path/to/factors.json

# Batch backtest
./batch_backtest.sh

# View factor library
python show_all_factors.py

# Clear cache
./clear_cache.sh
```

### B. Directory Structure

```
AlphaAgent/                      # Quanta Alpha main directory
├── run_experiment.sh            # Main experiment entry
├── batch_backtest.sh            # Batch backtest script
├── clear_cache.sh               # Cache cleanup script
├── all_factors_library_*.json   # Factor library output
├── factor_library/              # Factor library samples
├── backtest_v2/                 # Standalone backtest framework
│   ├── run_backtest.py          # Backtest entry point
│   ├── config.yaml              # Backtest config
│   └── ...
├── alphaagent/                  # Core code
│   ├── app/                     # Application entry
│   │   └── qlib_rd_loop/        # Main loop
│   │       ├── run_config.yaml
│   │       ├── factor_mining.py
│   │       └── ...
│   ├── components/              # Components
│   │   ├── workflow/            # Workflow
│   │   ├── coder/               # Factor coding
│   │   └── proposal/            # Proposal generation
│   └── scenarios/               # Scenario configs
│       └── qlib/                # Qlib scenario
└── /mnt/DATA/quantagent/        # Data storage
    └── AlphaAgent/
        ├── factor_cache/        # Factor cache
        ├── backtest_v2_results/ # Backtest results
        └── QuantaAlpha_workspace/  # Workspace
```

### C. Metric Quick Reference

| Metric | Full Name | Type | Good Threshold | Description |
|------|--------|------|----------|------|
| IC | Information Coefficient | Predictive power | > 0.05 | Factor–return correlation |
| ICIR | IC Information Ratio | Prediction stability | > 0.5 | IC stability |
| Rank IC | Rank Information Coefficient | Predictive power | > 0.05 | Rank correlation; more robust |
| Rank ICIR | Rank IC Information Ratio | Prediction stability | > 0.5 | Rank IC stability |
| annualized_return | **Excess** Annualized Return | Return | > 10% | Excess annualized vs benchmark |
| information_ratio | Information Ratio | Risk-adjusted return | > 1.0 | Excess return / tracking error |
| max_drawdown | **Excess** Max Drawdown | Risk | > -15% | Max decline of excess return curve |
| calmar_ratio | Calmar Ratio | Risk-adjusted return | > 1.0 | Excess annualized / |max drawdown| |

### D. References

1. Qlib: An AI-oriented Quantitative Investment Platform (Microsoft Research)
2. LightGBM: A Highly Efficient Gradient Boosting Decision Tree
3. Factor Investing: From Traditional to Alternative Risk Premia

---

*Document version: 1.1*  
*Project: Quanta Alpha*  
*Updated: 2026-01-17*
