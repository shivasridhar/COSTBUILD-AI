"""
Pruned Feature Engineering Module for BuildCost AI
Builds an optimized, low-dimensional feature matrix to prevent dimensional overfitting.
"""
import os
import sys
import numpy as np
import pandas as pd

# Path configuration
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

try:
    from config import FINAL_CSV_PATH, PROCESSED_DATA_DIR
except ImportError:
    FINAL_CSV_PATH = os.path.join(BASE_DIR, "final_training_dataset.csv")
    PROCESSED_DATA_DIR = os.path.join(BASE_DIR, "data", "processed")

OUTPUT_CSV_PATH = os.path.join(BASE_DIR, "processed_features.csv")


def run_feature_engineering_pruned(
    input_csv: str = FINAL_CSV_PATH,
    output_csv: str = OUTPUT_CSV_PATH
) -> pd.DataFrame:
    """
    Ingests final_training_dataset.csv, performs data imputation (including CPI-based diesel backcasting),
    generates lean engineered predictors, prunes redundant features, and saves the cleaned dataset.
    """
    print("==================================================")
    print("   FEATURE ENGINEERING & PRUNING PIPELINE         ")
    print("==================================================")

    if not os.path.exists(input_csv):
        raise FileNotFoundError(f"Input file not found: {input_csv}")

    df = pd.read_csv(input_csv)
    initial_shape = df.shape
    print(f"\n[Step 1] Ingested dataset with initial shape: {initial_shape}")

    # 1. Data Ingestion & Imputation
    print("[Step 2] Imputing missing values...")
    df['cpi_general_index'] = df['cpi_general_index'].ffill().bfill()
    df['wpi_cement'] = df['wpi_cement'].ffill().bfill()
    df['wpi_steel'] = df['wpi_steel'].ffill().bfill()

    # Back-cast early diesel_price_delhi missing values (pre-June 2017)
    june_2017_rows = df[df['year_month'] == '2017-06']
    if not june_2017_rows.empty:
        diesel_june_2017 = june_2017_rows['diesel_price_delhi'].values[0]
        cpi_june_2017 = june_2017_rows['cpi_general_index'].values[0]
        print(f"  -> June 2017 Baseline - Diesel: {diesel_june_2017}, CPI: {cpi_june_2017:.4f}")

        backcast_diesel = diesel_june_2017 * (df['cpi_general_index'] / cpi_june_2017)
        df['diesel_price_delhi'] = df['diesel_price_delhi'].fillna(backcast_diesel)

    df['diesel_price_delhi'] = df['diesel_price_delhi'].ffill().bfill()

    # 2. Engineered Predictors
    print("[Step 3] Generating lean engineered predictors...")
    # Binary Weather Flag
    df['is_peak_monsoon'] = (df['rainfall_mm_climatology'] > 200).astype(int)

    # Calendar Signals
    dates = pd.to_datetime(df['year_month'])
    df['month_num'] = dates.dt.month
    df['sin_month'] = np.sin(2 * np.pi * df['month_num'] / 12.0)

    # 1-Month Lags ONLY
    df['wpi_steel_lag1m'] = df['wpi_steel'].shift(1)
    df['wpi_cement_lag1m'] = df['wpi_cement'].shift(1)

    # 3. Feature Pruning Rules (Columns to REMOVE)
    print("[Step 4] Pruning redundant and collinear features...")
    cols_to_remove = [
        'wpi_cement_subgroup',
        'wpi_steel_subgroup',
        'wpi_all_commodities',
        'cpi_inflation',
        'rainfall_mm_climatology'
    ]
    df_pruned = df.drop(columns=[col for col in cols_to_remove if col in df.columns])

    # 4. Output & Verification: Drop single initial setup row created by 1-month lag
    print("[Step 5] Dropping setup row from 1-month lag...")
    df_final = df_pruned.dropna().reset_index(drop=True)

    final_shape = df_final.shape
    remaining_features = df_final.columns.tolist()

    # Log initial vs. final shape and remaining lean features
    print("\n--------------------------------------------------")
    print(f"Initial Dataset Shape  : {initial_shape}")
    print(f"Final Dataset Shape    : {final_shape}")
    num_predictors = final_shape[1] - 1  # Excluding year_month
    print(f"Sample-to-Feature Ratio: {final_shape[0]} rows / {num_predictors} features (~{final_shape[0]/num_predictors:.1f}:1)")
    print("\nRemaining Lean Features:")
    for feat in remaining_features:
        print(f"  - {feat}")
    print("--------------------------------------------------")

    # Verify model-specific subset mapping
    steel_subset = ['wpi_steel_lag1m', 'diesel_price_delhi', 'sin_month']
    cement_subset = ['wpi_cement_lag1m', 'diesel_price_delhi', 'is_peak_monsoon']
    print("\nModel-Specific Subset Mapping Verification:")
    print(f"  - Steel Subset Available : {all(col in remaining_features for col in steel_subset)} ({steel_subset})")
    print(f"  - Cement Subset Available: {all(col in remaining_features for col in cement_subset)} ({cement_subset})")

    # Export cleaned matrix
    output_dir = os.path.dirname(output_csv)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    df_final.to_csv(output_csv, index=False)
    print(f"\n[SUCCESS] Cleaned matrix exported to: {output_csv}")

    # Secondary copy to PROCESSED_DATA_DIR if directory exists
    if os.path.exists(PROCESSED_DATA_DIR):
        processed_dir_file = os.path.join(PROCESSED_DATA_DIR, "processed_features.csv")
        df_final.to_csv(processed_dir_file, index=False)
        print(f"[SUCCESS] Secondary copy exported to: {processed_dir_file}")

    return df_final


if __name__ == "__main__":
    run_feature_engineering_pruned()
