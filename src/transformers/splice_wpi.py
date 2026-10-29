import os
import sys

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import sqlite3
import pandas as pd
import config
from src.extractors.extract_wpi_old import extract_wpi_old
from src.extractors.extract_wpi import extract_wpi_new

def splice_wpi():
    """
    Combines the OLD WPI series (2011-12 base, monthly_index_202606.csv) with the NEW WPI series (2022-23 base, wpi_monthly_index_202607.xlsx/csv)
    into a single continuous time series using overlap-based linking factor splicing.
    Stores the rescaled spliced history in SQLite table 'wpi'.
    """
    print("\n==================================================")
    print("           WPI TIME SERIES SPLICING               ")
    print("==================================================")

    # 1. Extract raw series
    df_old = extract_wpi_old()
    df_new = extract_wpi_new()

    value_cols = ['wpi_all_commodities', 'wpi_cement', 'wpi_cement_subgroup', 'wpi_steel', 'wpi_steel_subgroup', 'wpi_wiring', 'wpi_wiring_subgroup']

    # 2. Identify overlap period
    overlap_months = sorted(list(set(df_old['year_month']).intersection(set(df_new['year_month']))))
    if not overlap_months:
        raise ValueError("[WPI SPLICE ERROR] No overlapping months found between OLD and NEW WPI series.")

    df_overlap_old = df_old[df_old['year_month'].isin(overlap_months)].sort_values('year_month').reset_index(drop=True)
    df_overlap_new = df_new[df_new['year_month'].isin(overlap_months)].sort_values('year_month').reset_index(drop=True)

    # 3. Compute column-wise linking factor = mean(new_index / old_index) across overlap
    linking_factors = {}
    print("\n[WPI SPLICE METRICS]")
    overlap_start = min(overlap_months)
    overlap_end = max(overlap_months)
    num_overlap = len(overlap_months)

    print(f"  • Overlap Date Range:       {overlap_start} to {overlap_end}")
    print(f"  • Overlapping Months Count: {num_overlap}")

    for col in value_cols:
        if col in df_overlap_old.columns and col in df_overlap_new.columns:
            ratio = df_overlap_new[col] / df_overlap_old[col]
            lf = ratio.mean()
            linking_factors[col] = lf
            print(f"  • Linking Factor for {col:20s}: {lf:.8f}")

    # 4. Rescale OLD series for months BEFORE new series start date
    new_start_date = df_new['year_month'].min()
    df_old_before = df_old[df_old['year_month'] < new_start_date].copy()

    for col in value_cols:
        if col in df_old_before.columns and col in linking_factors:
            df_old_before[col] = df_old_before[col] * linking_factors[col]

    df_old_before['source_series'] = "2011-12 base (linked)"

    # 5. NEW series from start date onward (unscaled)
    df_new_series = df_new.copy()
    df_new_series['source_series'] = "2022-23 base"

    # 6. Concatenate & sort chronologically
    db_cols = ['year_month'] + value_cols + ['source_series']
    df_spliced = pd.concat([df_old_before, df_new_series], ignore_index=True)
    # Ensure all required db_cols exist
    for col in db_cols:
        if col not in df_spliced.columns:
            df_spliced[col] = None
    df_spliced = df_spliced[db_cols].sort_values('year_month').reset_index(drop=True)

    missing_count = df_spliced[value_cols].isna().sum().to_dict()
    print(f"\n[WPI SPLICE SUCCESS] Created continuous series: {df_spliced['year_month'].min()} to {df_spliced['year_month'].max()} ({len(df_spliced)} months)")
    print(f"[WPI SPLICE] Missing values: {missing_count}")

    # 7. Store into SQLite database table 'wpi'
    conn = sqlite3.connect(config.DB_PATH)
    df_spliced.to_sql('wpi', conn, if_exists='replace', index=False)
    conn.close()
    print(f"[WPI SPLICE] Saved spliced records into table 'wpi' inside {config.DB_PATH}")

    return {
        'source': 'WPI (Spliced)',
        'start_date': df_spliced['year_month'].min(),
        'end_date': df_spliced['year_month'].max(),
        'total_months': len(df_spliced),
        'missing_months': sum([v for k, v in missing_count.items() if k != 'year_month']),
        'linking_factors': linking_factors,
        'overlap_range': f"{overlap_start} to {overlap_end}",
        'warnings': []
    }

if __name__ == "__main__":
    splice_wpi()
