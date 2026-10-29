# BuildCost AI — Forecast Accuracy & Trust Guide

This guide explains how BuildCost AI ensures transparency and honesty in its material cost forecasts and baseline pricing.

---

## 1. Walk-Forward Backtesting & Shaded Confidence Bands

### What is Walk-Forward Backtesting?
Rather than relying on speculative mathematical assumptions, BuildCost AI evaluates its forecasting method by testing it against 15+ years of historical government Wholesale Price Index (WPI) records.

The engine simulates "stepping back in time" to every historical month, generating a 12-month forward forecast as if it were standing on that past date, and comparing its predictions to what actually occurred in the market.

### What Do the Confidence Bands (±MAPE %) Mean?
### Symmetric Confidence Band Assumption
The lower and upper bounds of the confidence envelope are calculated as:
$$\text{Price}_{\text{low/high}} = \text{Price} \times \left(1 \mp \frac{\text{MAPE}}{100}\right)$$

This formula assumes that forecast error is equally likely up or down (symmetric error distribution). While real commodity market movements can occasionally exhibit asymmetric tail risk, this symmetric model provides a transparent, intuitive standard error envelope without making fragile skew assumptions.

### Sample Sizes ($N$) & Historical Coverage
To maintain absolute honesty about forecast accuracy claims, every MAPE metric is paired with its sample count ($N$), representing how many historical evaluation windows were tested:

| Horizon | Steel MAPE ($N$) | Cement MAPE ($N$) | Wiring MAPE ($N$) |
| :--- | :--- | :--- | :--- |
| **1 Month** | ±1.60% ($N=165$) | ±1.44% ($N=165$) | ±1.33% ($N=38$) |
| **3 Months** | ±3.88% ($N=163$) | ±3.44% ($N=163$) | ±3.24% ($N=36$) |
| **6 Months** | ±6.74% ($N=160$) | ±5.62% ($N=160$) | ±6.13% ($N=33$) |
| **9 Months** | ±8.95% ($N=157$) | ±6.79% ($N=157$) | ±9.32% ($N=30$) |
| **12 Months** | ±10.99% ($N=154$) | ±8.37% ($N=154$) | ±12.13% ($N=27$) |

> [!NOTE]
> **Overlapping Rolling Windows**: $N$ counts monthly-step walk-forward evaluation windows, not fully uncorrelated trials. For example, 154 monthly steps over a 12-month horizon share 11 overlapping months between consecutive tests ($\approx 154/12 \approx 13$ non-overlapping 1-year periods). Treat $N$ as the count of evaluated historical windows rather than a count of fully independent economic cycles.

> [!IMPORTANT]
> **Minimum Sample Floor ($N < 30$)**: When a material series has fewer than 30 historical evaluation windows for a given horizon (e.g., Wiring at 10–12 month horizons with $N=29 \to 27$), the engine explicitly flags the metric in the recommendation subtext: *"insufficient historical data for a confident estimate at this horizon (N < 30)"*, preventing low-sample estimates from being presented with unearned statistical confidence.

- **Steel & Cement ($N=165 \to 154$)**: Backtested over **171 historical WPI months** (`2012-04` to `2026-06`), yielding robust evaluation coverage across 13+ years of commodity price cycles.
- **Wiring ($N=38 \to 27$)**: Official WPI data for Electric Wires & Cables began under the `2022-23` base series (`2023-04` to `2026-06`, **39 months**). The backtest strictly filters out null pre-2023 periods without forward-filling, yielding sample sizes of $N=38$ (1m) down to $N=27$ (12m).

On the interactive **Forecast Chart**, the shaded region around each material price line represents this historical accuracy band. This ensures that when you evaluate an optimal purchase window at Month 4 or Month 6, you can visually inspect the range within which actual prices are expected to land.

---

## 2. Real Vendor Quote Baseline Correction

### Why Correction is Needed
Official government WPI data is published with a natural **2.5-month lag** (e.g. June WPI data is released in mid-August). During periods of rapid commodity price swings, relying solely on lagging government indices can leave baselines slightly out of date.

### How Vendor Quote Correction Works
BuildCost AI actively listens to real contractor and vendor quote submissions logged in `buildcost.db`:

1. **Threshold Requirement**: The system requires a minimum of **3 valid vendor quotes** logged within the last **45 days** for a specific material and region.
2. **Transparent 70/30 Blending**: When the threshold is met, the engine nudges the baseline toward real market prices using a weighted formula:
   $$\text{Effective Baseline Rate} = (0.70 \times \text{PWD/WPI Anchor Rate}) + (0.30 \times \text{Recent Vendor Quote Median})$$
3. **Clean Fallback**: If fewer than 3 quotes exist in the trailing 45-day window, the engine falls back cleanly to the pure PWD/WPI anchor rate without making unverified adjustments.

### Baseline Source Badges
On the **Reference Anchor Card**, each material displays a clear source indicator:
- **`WPI Anchor Only`**: Base rate is calculated directly from PWD SOR and WPI trend extrapolation.
- **`Corrected by Vendor Quotes`**: Base rate is dynamically blended with verified recent market quotes, displaying the quote count and median vendor price.

---

## 3. Drift Calculation: Two-Point vs. Regression Slope

### Experiment Background & Theoretical Rationale
In the forecasting engine, monthly drift is used to extrapolate WPI trajectories 12 months forward ($WPI_{t+m} = WPI_t + m \times \text{drift}$).

The engine was evaluated against a **least-squares linear regression slope** (`numpy.polyfit(x, y, 1)`) over the 6-month trailing window ($x = [0, 1, 2, 3, 4, 5]$). The theoretical rationale was that two-point drift ($\frac{WPI_t - WPI_{t-5}}{5}$) considers only the window's endpoints, leaving it vulnerable to single-month data glitches or temporary spikes. A regression slope uses all 6 months and naturally down-weights points that deviate from the shared trend line.

### Empirical Backtest Results
Both methods were backtested over **171 historical WPI months** (165 walk-forward testing windows) across 36 horizon/material combinations (1 to 12 months for Steel, Cement, and Wiring):

| Horizon | Material | Two-Point Drift MAPE (%) | Regression Slope MAPE (%) | Delta (% Error) | Empirical Outcome |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **1 Month** | **Steel** | **1.60%** | **1.66%** | +0.06% | Two-Point Won |
| **1 Month** | **Cement** | **1.44%** | **1.45%** | +0.01% | Identical |
| **1 Month** | **Wiring** | **1.33%** | **1.35%** | +0.02% | Two-Point Won |
| **3 Months** | **Steel** | **3.88%** | **4.03%** | +0.15% | Two-Point Won |
| **3 Months** | **Cement** | **3.44%** | **3.50%** | +0.06% | Two-Point Won |
| **3 Months** | **Wiring** | **3.24%** | **3.26%** | +0.02% | Identical |
| **6 Months** | **Steel** | **6.74%** | **6.96%** | +0.22% | Two-Point Won |
| **6 Months** | **Cement** | **5.62%** | **5.79%** | +0.17% | Two-Point Won |
| **6 Months** | **Wiring** | **6.13%** | **6.23%** | +0.10% | Two-Point Won |
| **9 Months** | **Steel** | **8.95%** | **9.28%** | +0.33% | Two-Point Won |
| **9 Months** | **Cement** | **6.79%** | **7.11%** | +0.32% | Two-Point Won |
| **9 Months** | **Wiring** | **9.32%** | **9.48%** | +0.16% | Two-Point Won |
| **12 Months** | **Steel** | **10.99%** | **11.42%** | +0.43% | Two-Point Won |
| **12 Months** | **Cement** | **8.37%** | **8.84%** | +0.47% | Two-Point Won |
| **12 Months** | **Wiring** | **12.13%** | **12.34%** | +0.21% | Two-Point Won |

*Summary across 36 Horizon-Material pairs*:
- **Two-Point Drift Won / Tied**: **36 / 36** (0 regressions, 2 ties within ±0.01%, 34 clear wins)
- **Error Gap Trend**: The accuracy gap widened as the forecast horizon extended (~+0.01% to +0.06% at 1m up to ~+0.43% to +0.47% at 12m).

### Interpretation & Working Hypothesis
- **Unverified Hypothesis**: Recency in this official WPI dataset appears to be more predictive than window-averaging. In macroeconomic commodity series, price adjustments often move in momentum-driven trends or sticky price step-functions. The two-point formula measures immediate net momentum between $t-5$ and $t$, whereas a least-squares line averages older historical months ($t-5, t-4, t-3$), causing it to slightly lag behind fresh momentum shifts.
- *Caveat*: This momentum interpretation is a working hypothesis to explain the backtest numbers, not an independently proven structural mechanism.

### Shipped Default & Architectural Consistency
- **Shipped Default (`USE_REGRESSION_DRIFT = False`)**: BuildCost AI retains the two-point drift calculation as its shipped production default. This decision aligns with the project's core philosophy: choosing methods that are **empirically proven to perform better** on historical walk-forward evaluations, rather than adopting theoretically "smarter" methods that fail to win in practice.
- **Code Preservation**: Both code paths remain fully intact in `src/optimization/bom_optimizer.py` and `src/analysis/backtest.py`. The `USE_REGRESSION_DRIFT` flag is preserved so future contributors can easily re-run the backtest comparison as additional historical WPI data accumulates.

