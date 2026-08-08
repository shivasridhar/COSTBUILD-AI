import os
import sys

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import sqlite3
import pandas as pd
import config
from src.extractors.extract_cpi_old import extract_cpi_old
from src.extractors.extract_cpi import extract_cpi_new

def splice_cpi():
    """
    Combines the OLD CPI series (2012 base, cpi_1435.csv) with the NEW CPI series (2024 base, cpi_1590.csv/xlsx)
    into a single continuous time series using overlap-based linking factor splicing.
    Stores the rescaled spliced history in SQLite table 'cpi'.
    """
    print("\n==================================================")
    print("           CPI TIME SERIES SPLICING               ")
    print("==================================================")

    # 1. Extract raw series
    df_old = extract_cpi_old()
    df_new = extract_cpi_new()

    # Ensure consistent column naming for index & inflation
    df_old_clean = df_old[['year_month', 'cpi_index', 'cpi_inflation_rate']].copy()
    df_old_clean = df_old_clean.rename(columns={
        'cpi_index': 'cpi_general_index',
        'cpi_inflation_rate': 'cpi_inflation'
    })

    df_new_clean = df_new[['year_month', 'cpi_general_index', 'cpi_inflation']].copy()

    # 2. Identify overlap period
    overlap_months = sorted(list(set(df_old_clean['year_month']).intersection(set(df_new_clean['year_month']))))
    if not overlap_months:
        raise ValueError("[CPI SPLICE ERROR] No overlapping months found between OLD and NEW CPI series.")

    df_overlap_old = df_old_clean[df_old_clean['year_month'].isin(overlap_months)].sort_values('year_month').reset_index(drop=True)
    df_overlap_new = df_new_clean[df_new_clean['year_month'].isin(overlap_months)].sort_values('year_month').reset_index(drop=True)

    # 3. Compute linking factor = mean(new_index / old_index) across overlap
    merged_overlap = pd.merge(df_overlap_old, df_overlap_new, on='year_month', suffixes=('_old', '_new'))
    merged_overlap['ratio'] = merged_overlap['cpi_general_index_new'] / merged_overlap['cpi_general_index_old']
    linking_factor = merged_overlap['ratio'].mean()

    overlap_start = min(overlap_months)
    overlap_end = max(overlap_months)
    num_overlap = len(overlap_months)

    print("\n[CPI SPLICE METRICS]")
    print(f"  • Overlap Date Range:      {overlap_start} to {overlap_end}")
    print(f"  • Overlapping Months Count: {num_overlap}")
    print(f"  • Computed Linking Factor:  {linking_factor:.8f}")

    # 4. Rescale OLD series for months BEFORE new series start date
    new_start_date = df_new_clean['year_month'].min()
    df_old_before = df_old_clean[df_old_clean['year_month'] < new_start_date].copy()
    
    # Rescale index, leave inflation rate unscaled
    df_old_before['cpi_general_index'] = df_old_before['cpi_general_index'] * linking_factor
    df_old_before['source_series'] = "2012 base (linked)"

    # 5. NEW series from start date onward (unscaled)
    df_new_series = df_new_clean.copy()
    df_new_series['source_series'] = "2024 base"

    # 6. Concatenate & sort chronologically
    df_spliced = pd.concat([df_old_before, df_new_series], ignore_index=True)
    df_spliced = df_spliced.sort_values('year_month').reset_index(drop=True)

    # Provide alias columns if needed
    df_spliced['date'] = df_spliced['year_month']
    df_spliced['cpi_index'] = df_spliced['cpi_general_index']
    df_spliced['cpi_inflation_rate'] = df_spliced['cpi_inflation']

    # Standard column ordering for DB storage
    db_cols = ['year_month', 'cpi_general_index', 'cpi_inflation', 'source_series']
    df_db = df_spliced[db_cols]

    missing_count = df_db[['cpi_general_index', 'cpi_inflation']].isna().sum().to_dict()
    print(f"\n[CPI SPLICE SUCCESS] Created continuous series: {df_db['year_month'].min()} to {df_db['year_month'].max()} ({len(df_db)} months)")
    print(f"[CPI SPLICE] Missing values: {missing_count}")

    # 7. Store into SQLite database table 'cpi'
    conn = sqlite3.connect(config.DB_PATH)
    df_db.to_sql('cpi', conn, if_exists='replace', index=False)
    conn.close()
    print(f"[CPI SPLICE] Saved spliced records into table 'cpi' inside {config.DB_PATH}")

    return {
        'source': 'CPI (Spliced)',
        'start_date': df_db['year_month'].min(),
        'end_date': df_db['year_month'].max(),
        'total_months': len(df_db),
        'missing_months': sum([v for k, v in missing_count.items() if k != 'year_month']),
        'linking_factor': linking_factor,
        'overlap_range': f"{overlap_start} to {overlap_end}",
        'warnings': []
    }

if __name__ == "__main__":
    splice_cpi()
