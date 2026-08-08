import os
import sqlite3
import pandas as pd
import config

def extract_transform_rainfall():
    """
    Reads wide rainfall CSV (1901-2015), reshapes to long format (year_month, rainfall_mm),
    computes 1901-2015 monthly climatology (average rainfall per calendar month),
    and stores 'rainfall_historical' and 'rainfall_climatology' into SQLite.
    """
    file_path = config.RAINFALL_FILE
    print(f"[Rainfall ETL] Loading rainfall dataset from {file_path}...")

    df_raw = pd.read_csv(file_path)

    month_cols = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
    month_num_map = {
        'JAN': '01', 'FEB': '02', 'MAR': '03', 'APR': '04',
        'MAY': '05', 'JUN': '06', 'JUL': '07', 'AUG': '08',
        'SEP': '09', 'OCT': '10', 'NOV': '11', 'DEC': '12'
    }

    # Reshape from wide to long format
    long_rows = []
    for _, row in df_raw.iterrows():
        year = int(row['YEAR'])
        for m in month_cols:
            m_num = month_num_map[m]
            ym_str = f"{year}-{m_num}"
            val = float(row[m]) if pd.notna(row[m]) else None
            long_rows.append({
                'year_month': ym_str,
                'year': year,
                'month_num': int(m_num),
                'month_name': m,
                'rainfall_mm': val
            })

    df_long = pd.DataFrame(long_rows).sort_values('year_month').reset_index(drop=True)

    # Compute Climatology (Historical average per calendar month across 1901-2015)
    df_climatology = df_long.groupby(['month_num', 'month_name'])['rainfall_mm'].mean().reset_index()
    df_climatology = df_climatology.rename(columns={'rainfall_mm': 'rainfall_mm_climatology'})
    df_climatology = df_climatology.sort_values('month_num').reset_index(drop=True)

    # Check for missing values
    missing_count = df_long['rainfall_mm'].isna().sum()
    print(f"[Rainfall ETL] Historical range: {df_long['year_month'].min()} to {df_long['year_month'].max()} ({len(df_long)} months)")
    print(f"[Rainfall ETL] Missing historical values: {missing_count}")
    print(f"[Rainfall ETL] Monthly Climatology (mm):\n{df_climatology[['month_num', 'month_name', 'rainfall_mm_climatology']]}")

    # Load into SQLite database
    conn = sqlite3.connect(config.DB_PATH)
    df_long.to_sql('rainfall_historical', conn, if_exists='replace', index=False)
    df_climatology.to_sql('rainfall_climatology', conn, if_exists='replace', index=False)
    # Also save df_long as 'rainfall' for table naming consistency requirement
    df_long.to_sql('rainfall', conn, if_exists='replace', index=False)
    conn.close()

    print(f"[Rainfall ETL SUCCESS] Stored {len(df_long)} records in table 'rainfall'/'rainfall_historical' and 12 records in 'rainfall_climatology' inside {config.DB_PATH}")

    return {
        'source': 'Rainfall',
        'start_date': df_long['year_month'].min(),
        'end_date': df_long['year_month'].max(),
        'total_months': len(df_long),
        'missing_months': int(missing_count),
        'warnings': []
    }

if __name__ == "__main__":
    extract_transform_rainfall()
