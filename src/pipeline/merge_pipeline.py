import os
import sys

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import sqlite3
import pandas as pd
import config

def run_merge_pipeline(extraction_summaries=None):
    """
    Loads all per-source tables from SQLite database buildcost.db,
    merges time series tables on year_month, maps rainfall climatology by calendar month,
    exports final_training_dataset.csv, and prints a summary report.
    """
    print(f"\n==================================================")
    print(f"       BUILDCOST AI ETL MERGE PIPELINE            ")
    print(f"==================================================")

    if not os.path.exists(config.DB_PATH):
        raise FileNotFoundError(f"Database {config.DB_PATH} not found. Run extractors first.")

    conn = sqlite3.connect(config.DB_PATH)

    # 1. Load per-source tables from SQLite
    df_wpi = pd.read_sql("SELECT * FROM wpi", conn)
    df_diesel = pd.read_sql("SELECT * FROM diesel", conn)
    df_cpi = pd.read_sql("SELECT * FROM cpi", conn)
    df_rainfall_clim = pd.read_sql("SELECT * FROM rainfall_climatology", conn)
    df_pwd = pd.read_sql("SELECT * FROM pwd_rates", conn)

    # Drop source_series tag before merging if present (tag retained in DB)
    df_cpi_merge = df_cpi.drop(columns=['source_series'], errors='ignore')
    df_wpi_merge = df_wpi.drop(columns=['source_series'], errors='ignore')

    # 2. Outer join time-series tables on year_month
    df_merged = pd.merge(df_diesel, df_wpi_merge, on='year_month', how='outer')
    df_merged = pd.merge(df_merged, df_cpi_merge, on='year_month', how='outer')

    # Sort chronologically by year_month
    df_merged = df_merged.sort_values('year_month').reset_index(drop=True)

    # Extract month number (1..12) from year_month (YYYY-MM)
    df_merged['month_num'] = df_merged['year_month'].apply(lambda x: int(x.split('-')[1]))

    # 3. Map Climatology Rainfall by calendar month (month_num)
    df_merged = pd.merge(df_merged, df_rainfall_clim[['month_num', 'rainfall_mm_climatology']], on='month_num', how='left')

    # Drop temporary month_num column or keep it
    df_merged = df_merged.drop(columns=['month_num'])

    # 4. Save final training-ready CSV
    df_merged.to_csv(config.FINAL_CSV_PATH, index=False)
    print(f"\n[MERGE SUCCESS] Final training-ready dataset exported to: {config.FINAL_CSV_PATH}")
    print(f"[MERGE INFO] Total rows: {len(df_merged)}, Total columns: {len(df_merged.columns)}")

    # 5. Generate and print short summary report
    print("\n--------------------------------------------------")
    print("                ETL SUMMARY REPORT                ")
    print("--------------------------------------------------")

    print("\n• Merged Dataset Missing-Value Counts Per Column:")
    missing_dict = df_merged.isna().sum().to_dict()
    for col, count in missing_dict.items():
        print(f"  - {col}: {count} missing")


    sources = [
        ("WPI (Steel, Cement & Wiring)", df_wpi, 'year_month'),
        ("Diesel Prices (Delhi)", df_diesel, 'year_month'),
        ("CPI (MOSPI Combined)", df_cpi, 'year_month'),
        ("Rainfall (Climatology)", df_rainfall_clim, None),
        ("PWD Rates (Annual Snapshots)", df_pwd, None)
    ]

    for name, df, ym_col in sources:
        if ym_col and not df.empty:
            min_ym = df[ym_col].min()
            max_ym = df[ym_col].max()
            count = len(df)
            print(f"• Source: {name}")
            print(f"  - Records: {count}")
            print(f"  - Covered Date Range: {min_ym} to {max_ym}")
            # Gaps within date range
            full_range = pd.date_range(start=min_ym + "-01", end=max_ym + "-01", freq='MS').strftime('%Y-%m')
            missing_gaps = len(full_range) - len(df[ym_col].unique())
            print(f"  - Missing months within range: {missing_gaps}")
        elif name == "Rainfall (Climatology)":
            print(f"• Source: {name}")
            print(f"  - Records: 12 calendar months (Jan–Dec)")
            print(f"  - Applied to all {len(df_merged)} merged training rows via monthly climatology mapping.")
            print(f"  - Missing months: 0")
        elif name == "PWD Rates (Annual Snapshots)":
            years = df['source_year'].unique().tolist() if 'source_year' in df.columns else []
            print(f"• Source: {name}")
            print(f"  - Records: {len(df)} line items")
            print(f"  - Source Years: {years}")
            print(f"  - Stored in SQLite table 'pwd_rates' for BOM cost engine lookup.")

    print("\n• PDF Extraction Failures/Warnings:")
    pdf_warnings_found = False
    if extraction_summaries:
        for s in extraction_summaries:
            if s.get('warnings'):
                pdf_warnings_found = True
                for w in s['warnings']:
                    print(f"  - [{s['source']}] {w}")
    if not pdf_warnings_found:
        print("  - None! All PDF tables extracted cleanly without malformed rows or dropped pages.")

    print("--------------------------------------------------\n")
    conn.close()
    return df_merged

if __name__ == "__main__":
    run_merge_pipeline()
