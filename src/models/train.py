"""
Model Training & Evaluation Module for BuildCost AI
Evaluates predictive models on the truncated 109-row dataset (2017-06 to 2026-06).
Runs two comparison benchmarks:
1. Predicting raw Price LEVEL (wpi_cement, wpi_steel)
2. Predicting Month-over-Month CHANGE/DELTA (wpi_target - wpi_target_lag1m)
"""

import os
import sys
import numpy as np
import pandas as pd
from sklearn.model_selection import TimeSeriesSplit
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.metrics import root_mean_squared_error, r2_score
import xgboost as xgb
import lightgbm as lgb
import warnings

warnings.filterwarnings('ignore')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROCESSED_CSV = os.path.join(BASE_DIR, "processed_features.csv")

AFTER_FEATURES = [
    'diesel_price_delhi',
    'cpi_general_index',
    'is_peak_monsoon',
    'month_num',
    'sin_month',
    'cos_month',
    'wpi_steel_lag1m',
    'wpi_cement_lag1m'
]


def load_dataset(csv_path: str = PROCESSED_CSV) -> pd.DataFrame:
    """Loads dataset and ensures strict 109-row truncation (2017-06 to 2026-06)."""
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Processed dataset not found: {csv_path}")

    df = pd.read_csv(csv_path)
    # Strict truncation to 2017-06 <= year_month <= 2026-06
    df = df[(df['year_month'] >= '2017-06') & (df['year_month'] <= '2026-06')].reset_index(drop=True)
    return df


def evaluate_models():
    print("==================================================")
    print("  1. DATA LOAD & MISSING VALUE AUDIT              ")
    print("==================================================")
    df = load_dataset()
    print(f"Dataset loaded from: {PROCESSED_CSV}")
    print(f"Total Rows: {len(df)} (Timeline: {df['year_month'].min()} to {df['year_month'].max()})")
    print(f"Features Used ({len(AFTER_FEATURES)}): {AFTER_FEATURES}")
    print(f"Rows-to-Features Ratio: {len(df)} / {len(AFTER_FEATURES)} = {len(df)/len(AFTER_FEATURES):.2f}:1\n")

    print("--- RIGHT BEFORE MODEL FITTING: df.isna().sum() ---")
    print(df[AFTER_FEATURES + ['wpi_cement', 'wpi_steel']].isna().sum())
    print("--------------------------------------------------\n")

    tscv = TimeSeriesSplit(n_splits=5)
    targets = ['wpi_cement', 'wpi_steel']

    models = {
        'Naive Baseline': 'naive',
        'Linear Regression': LinearRegression(),
        'Ridge (alpha=1.0)': Ridge(alpha=1.0),
        'Ridge (alpha=10.0)': Ridge(alpha=10.0),
        'Ridge (alpha=100.0)': Ridge(alpha=100.0),
        'XGBoost': xgb.XGBRegressor(n_estimators=50, max_depth=3, learning_rate=0.05, random_state=42, verbosity=0),
        'LightGBM': lgb.LGBMRegressor(n_estimators=50, max_depth=3, learning_rate=0.05, random_state=42, verbose=-1)
    }

    # =========================================================================
    # PART 1: RAW PRICE LEVEL BENCHMARK (109-Row Truncated Data)
    # =========================================================================
    print("=" * 80)
    print("   PART 1: RAW PRICE LEVEL COMPARISON (109-ROW TRUNCATED DATASET)")
    print("=" * 80)

    level_summaries = {}

    for target in targets:
        print("\n" + "=" * 80)
        print(f"          LEVEL TARGET EVALUATION: {target.upper()}")
        print("=" * 80)

        lag_col = f"{target}_lag1m"
        X = df[AFTER_FEATURES].values
        y = df[target].values
        naive_preds_series = df[lag_col].values

        summary = []

        for model_name, model in models.items():
            print(f"\n--- Model: {model_name} ---")
            fold_rmses = []
            fold_r2s = []

            for fold, (train_idx, test_idx) in enumerate(tscv.split(X), 1):
                X_train, X_test = X[train_idx], X[test_idx]
                y_train, y_test = y[train_idx], y[test_idx]

                if model_name == 'Naive Baseline':
                    preds = naive_preds_series[test_idx]
                else:
                    model.fit(X_train, y_train)
                    preds = model.predict(X_test)

                rmse = root_mean_squared_error(y_test, preds)
                r2 = r2_score(y_test, preds) if len(np.unique(y_test)) > 1 else np.nan

                fold_rmses.append(rmse)
                fold_r2s.append(r2)

                print(f"  Fold {fold}: RMSE = {rmse:.4f}, R² = {r2:.4f} (Train n={len(train_idx)}, Test n={len(test_idx)})")

            mean_rmse = np.mean(fold_rmses)
            mean_r2 = np.mean(fold_r2s)
            print(f"  --> MEAN: RMSE = {mean_rmse:.4f}, R² = {mean_r2:.4f}")
            summary.append((model_name, mean_rmse, mean_r2))

        level_summaries[target] = summary

    # =========================================================================
    # PART 2: MONTH-OVER-MONTH CHANGE / DELTA BENCHMARK
    # Target: delta = y_t - y_{t-1}
    # Naive Baseline: predict delta = 0
    # =========================================================================
    print("\n" + "=" * 80)
    print("   PART 2: MONTH-OVER-MONTH DELTA/CHANGE COMPARISON (109-ROW DATASET)")
    print("   Target: Delta (Index_t - Index_{t-1}), Naive Baseline: Delta = 0")
    print("=" * 80)

    delta_summaries = {}

    for target in targets:
        print("\n" + "=" * 80)
        print(f"          DELTA TARGET EVALUATION: DELTA_{target.upper()}")
        print("=" * 80)

        lag_col = f"{target}_lag1m"
        X = df[AFTER_FEATURES].values
        y_delta = df[target].values - df[lag_col].values  # Delta target

        summary = []

        for model_name, model in models.items():
            print(f"\n--- Model: {model_name} (Predicting Delta) ---")
            fold_rmses = []
            fold_r2s = []

            for fold, (train_idx, test_idx) in enumerate(tscv.split(X), 1):
                X_train, X_test = X[train_idx], X[test_idx]
                y_train, y_test = y_delta[train_idx], y_delta[test_idx]

                if model_name == 'Naive Baseline':
                    preds = np.zeros(len(test_idx))  # Naive baseline predicts delta = 0
                else:
                    model.fit(X_train, y_train)
                    preds = model.predict(X_test)

                rmse = root_mean_squared_error(y_test, preds)
                r2 = r2_score(y_test, preds) if len(np.unique(y_test)) > 1 else np.nan

                fold_rmses.append(rmse)
                fold_r2s.append(r2)

                print(f"  Fold {fold}: RMSE = {rmse:.4f}, R² = {r2:.4f} (Train n={len(train_idx)}, Test n={len(test_idx)})")

            mean_rmse = np.mean(fold_rmses)
            mean_r2 = np.mean(fold_r2s)
            print(f"  --> MEAN: RMSE = {mean_rmse:.4f}, R² = {mean_r2:.4f}")
            summary.append((model_name, mean_rmse, mean_r2))

        delta_summaries[target] = summary

    # Print Side-by-Side Summary Tables
    print("\n" + "=" * 80)
    print("                   FINAL COMPARISON SUMMARY TABLES")
    print("=" * 80)
    for target in targets:
        print(f"\n=== TARGET: {target.upper()} (LEVEL vs DELTA) ===")
        print(f"{'Model':<22} | {'Level RMSE':<10} | {'Level R²':<10} | {'Delta RMSE':<10} | {'Delta R²':<10}")
        print("-" * 72)
        lev_map = {name: (rmse, r2) for name, rmse, r2 in level_summaries[target]}
        del_map = {name: (rmse, r2) for name, rmse, r2 in delta_summaries[target]}

        for name in models.keys():
            l_rmse, l_r2 = lev_map[name]
            d_rmse, d_r2 = del_map[name]
            print(f"{name:<22} | {l_rmse:<10.4f} | {l_r2:<10.4f} | {d_rmse:<10.4f} | {d_r2:<10.4f}")


if __name__ == "__main__":
    evaluate_models()
