import os
import sqlite3
import pandas as pd
import config

def extract_cpi_new(file_path=None):
    """
    Extracts MOSPI 2024-base CPI All-India Combined General Index dataset.
    Returns DataFrame with columns: year_month, date, cpi_general_index, cpi_index, cpi_inflation, cpi_inflation_rate.
    """
    if file_path is None:
        file_path = config.CPI_FILE

    print(f"[CPI NEW ETL] Loading CPI dataset from {file_path}...")

    if file_path.endswith('.xlsx'):
        df_raw = pd.read_excel(file_path)
    else:
        df_raw = pd.read_csv(file_path)

    # Filter for Combined sector & General Index
    if 'division' in df_raw.columns:
        df_gen = df_raw[
            (df_raw['sector'].astype(str).str.strip() == 'Combined') &
            (df_raw['state'].astype(str).str.strip() == 'All India') &
            (df_raw['division'].astype(str).str.strip() == 'CPI (General)')
        ].copy()
    elif 'code' in df_raw.columns:
        df_gen = df_raw[df_raw['code'].isna()].copy()
    elif 'item' in df_raw.columns:
        df_gen = df_raw[df_raw['item'].isna()].copy()
    else:
        df_gen = df_raw.copy()

    month_map = {
        'january': '01', 'jan': '01',
        'february': '02', 'feb': '02',
        'march': '03', 'mar': '03',
        'april': '04', 'apr': '04',
        'may': '05',
        'june': '06', 'jun': '06',
        'july': '07', 'jul': '07',
        'august': '08', 'aug': '08',
        'september': '09', 'sep': '09',
        'october': '10', 'oct': '10',
        'november': '11', 'nov': '11',
        'december': '12', 'dec': '12'
    }

    def format_ym(row):
        yr = str(int(row['year']))
        m_str = str(row['month']).strip().lower()
        m_num = month_map.get(m_str, m_str.zfill(2))
        return f"{yr}-{m_num}"

    df_gen['year_month'] = df_gen.apply(format_ym, axis=1)
    df_gen['date'] = df_gen['year_month']
    df_gen = df_gen.rename(columns={'index': 'cpi_general_index', 'inflation': 'cpi_inflation'})
    df_gen['cpi_index'] = df_gen['cpi_general_index']
    df_gen['cpi_inflation_rate'] = df_gen['cpi_inflation']

    cols = ['year_month', 'date', 'cpi_general_index', 'cpi_index', 'cpi_inflation', 'cpi_inflation_rate']
    df_cpi = df_gen[cols].drop_duplicates(subset=['year_month']).sort_values('year_month').reset_index(drop=True)
    return df_cpi

def extract_transform_cpi():
    """
    Extracts MOSPI CPI All-India Combined General Index,
    normalizes dates to YYYY-MM, checks missing values, and stores in SQLite table 'cpi'.
    """
    df_cpi = extract_cpi_new()
    missing_count = df_cpi[['cpi_general_index', 'cpi_inflation']].isna().sum().to_dict()
    print(f"[CPI ETL] Data range: {df_cpi['year_month'].min()} to {df_cpi['year_month'].max()} ({len(df_cpi)} months)")
    print(f"[CPI ETL] Missing values report: {missing_count}")


    # Load into SQLite database
    conn = sqlite3.connect(config.DB_PATH)
    df_cpi.to_sql('cpi', conn, if_exists='replace', index=False)
    conn.close()
    print(f"[CPI ETL SUCCESS] Stored {len(df_cpi)} records in table 'cpi' inside {config.DB_PATH}")

    return {
        'source': 'CPI',
        'start_date': df_cpi['year_month'].min(),
        'end_date': df_cpi['year_month'].max(),
        'total_months': len(df_cpi),
        'missing_months': sum([v for k, v in missing_count.items() if k != 'year_month']),
        'warnings': []
    }

if __name__ == "__main__":
    extract_transform_cpi()
