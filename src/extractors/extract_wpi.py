import os
import sqlite3
import pandas as pd
import config

def extract_wpi_new(file_path=None):
    """
    Extracts 2022-23 base WPI dataset from wpi_monthly_index_202607.xlsx / csv.
    Returns DataFrame with columns: year_month, wpi_all_commodities, wpi_cement, wpi_cement_subgroup, wpi_steel, wpi_steel_subgroup.
    """
    if file_path is None:
        file_path = config.WPI_XLSX_FILE if os.path.exists(config.WPI_XLSX_FILE) else config.WPI_FILE

    print(f"[WPI NEW ETL] Loading WPI dataset from {file_path}...")

    if file_path.endswith('.xlsx'):
        df_raw = pd.read_excel(file_path)
    else:
        df_raw = pd.read_csv(file_path)

    meta_cols = ['Level', 'Commodity Name', 'Commodity Code', 'Commodity Weight']
    date_cols = [c for c in df_raw.columns if c not in meta_cols]

    target_commodities = {
        'wpi_all_commodities': 'All Commodities',
        'wpi_cement': 'Ordinary Portland Cement (OPC)',
        'wpi_cement_subgroup': 'e.Manufacture of cement, lime and plaster',
        'wpi_steel': 'Bars and Rods of Mild steel',
        'wpi_steel_subgroup': 'a.Manufacture of basic iron and steel'
    }

    results_by_month = {}

    for col in date_cols:
        try:
            ym_str = pd.to_datetime(col).strftime('%Y-%m')
        except Exception:
            ym_str = str(col)[:7]

        if ym_str not in results_by_month:
            results_by_month[ym_str] = {'year_month': ym_str}

    for var_name, comm_name in target_commodities.items():
        match_rows = df_raw[df_raw['Commodity Name'].astype(str).str.strip().str.lower() == comm_name.lower()]
        if match_rows.empty:
            match_rows = df_raw[df_raw['Commodity Name'].astype(str).str.contains(comm_name, case=False, na=False)]
        
        if not match_rows.empty:
            row_data = match_rows.iloc[0]
            for col in date_cols:
                try:
                    ym_str = pd.to_datetime(col).strftime('%Y-%m')
                except Exception:
                    ym_str = str(col)[:7]
                val = row_data[col]
                results_by_month[ym_str][var_name] = float(val) if pd.notna(val) else None
        else:
            print(f"[WPI NEW ETL ERROR] Commodity '{comm_name}' could not be extracted.")

    df_wpi = pd.DataFrame(list(results_by_month.values())).sort_values('year_month').reset_index(drop=True)
    return df_wpi

def extract_transform_wpi():
    """
    Extracts WPI data for Steel and Cement (base 2011-12),
    normalizes dates to YYYY-MM, checks missing values, and stores in SQLite table 'wpi'.
    """
    df_wpi = extract_wpi_new()


    # Check for missing values
    missing_count = df_wpi.isna().sum().to_dict()
    print(f"[WPI ETL] Data range: {df_wpi['year_month'].min()} to {df_wpi['year_month'].max()} ({len(df_wpi)} months)")
    print(f"[WPI ETL] Missing values report: {missing_count}")

    # Load into SQLite database
    conn = sqlite3.connect(config.DB_PATH)
    df_wpi.to_sql('wpi', conn, if_exists='replace', index=False)
    conn.close()
    print(f"[WPI ETL SUCCESS] Stored {len(df_wpi)} records in table 'wpi' inside {config.DB_PATH}")

    return {
        'source': 'WPI',
        'start_date': df_wpi['year_month'].min(),
        'end_date': df_wpi['year_month'].max(),
        'total_months': len(df_wpi),
        'missing_months': sum([v for k, v in missing_count.items() if k != 'year_month']),
        'warnings': []
    }

if __name__ == "__main__":
    extract_transform_wpi()
