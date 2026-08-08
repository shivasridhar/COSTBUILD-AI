"""
Resolve Features Module for BuildCost AI
Standalone script to resolve feature engineering defects in processed_features.csv:
1. Adds 2D cyclical calendar encoding with cos_month alongside sin_month.
2. Truncates trailing forward-filled rows (year_month <= '2026-06').
"""

import os
import sys
import numpy as np
import pandas as pd

# Path configuration to locate workspace root
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

DEFAULT_CSV_PATH = os.path.join(BASE_DIR, "processed_features.csv")


def resolve_features(file_path: str = DEFAULT_CSV_PATH) -> pd.DataFrame:
    """
    Ingests processed_features.csv, adds cos_month, truncates trailing forward-filled rows (> 2026-06),
    and saves the cleaned dataset back to file_path.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Feature dataset not found at: {file_path}")

    df = pd.read_csv(file_path)
    before_count = len(df)
    print(f"Ingested dataset from: {file_path}")
    print(f"Row count before truncation: {before_count}")

    # 1. Add cos_month feature
    # Derive month_num if missing or contains NaNs
    if 'month_num' not in df.columns or df['month_num'].isna().any():
        derived_month = pd.to_datetime(df['year_month']).dt.month
        if 'month_num' not in df.columns:
            df['month_num'] = derived_month
        else:
            df['month_num'] = df['month_num'].fillna(derived_month)

    df['month_num'] = df['month_num'].astype(int)

    # Compute sin_month and cos_month for complete 2D cyclical calendar encoding
    df['sin_month'] = np.sin(2 * np.pi * df['month_num'] / 12.0)
    df['cos_month'] = np.cos(2 * np.pi * df['month_num'] / 12.0)

    # 2. Truncate Dataset to Valid Non-Imputed Range ('2017-06' <= year_month <= '2026-06')
    df = df[(df['year_month'] >= '2017-06') & (df['year_month'] <= '2026-06')].copy().reset_index(drop=True)
    after_count = len(df)
    print(f"Row count after truncation ('2017-06' <= year_month <= '2026-06'): {after_count}")
    print(f"Removed {before_count - after_count} outer row(s).")

    # Retain required lean features and structure column order
    expected_cols = [
        'year_month',
        'diesel_price_delhi',
        'wpi_cement',
        'wpi_steel',
        'cpi_general_index',
        'is_peak_monsoon',
        'month_num',
        'sin_month',
        'cos_month',
        'wpi_steel_lag1m',
        'wpi_cement_lag1m'
    ]

    # Reorder columns while preserving any extra columns if present
    ordered_cols = [col for col in expected_cols if col in df.columns]
    remaining_cols = [col for col in df.columns if col not in ordered_cols]
    final_cols = ordered_cols + remaining_cols
    df = df[final_cols]

    # Save resolved dataframe back to CSV
    df.to_csv(file_path, index=False)
    print(f"Successfully saved resolved dataframe to: {file_path}")

    return df


if __name__ == '__main__':
    resolve_features()
