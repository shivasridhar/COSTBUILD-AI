import os
import pandas as pd
import config

def extract_cpi_old(file_path=None):
    """
    Extracts MOSPI OLD CPI (2012 Base) All-India Combined General Index from cpi_1435.csv.
    Filters where group == 'General', sector == 'Combined', state == 'All India'.
    Returns DataFrame with columns: date (year_month), cpi_index, cpi_inflation_rate.
    """
    if file_path is None:
        file_path = config.CPI_OLD_FILE

    print(f"[CPI OLD ETL] Loading OLD CPI dataset from {file_path}...")
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"OLD CPI dataset not found at {file_path}")

    df_raw = pd.read_csv(file_path)

    # Filter for group == 'General', sector == 'Combined', state == 'All India'
    mask = (
        (df_raw['group'].astype(str).str.strip() == 'General') &
        (df_raw['sector'].astype(str).str.strip() == 'Combined') &
        (df_raw['state'].astype(str).str.strip() == 'All India')
    )
    df_filtered = df_raw[mask].copy()

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
        if m_str in month_map:
            m_num = month_map[m_str]
        elif 'month_code' in row and pd.notna(row['month_code']):
            m_num = str(int(row['month_code'])).zfill(2)
        else:
            m_num = m_str.zfill(2)
        return f"{yr}-{m_num}"

    df_filtered['year_month'] = df_filtered.apply(format_ym, axis=1)
    df_filtered['date'] = df_filtered['year_month']

    # Rename index and inflation columns
    df_filtered = df_filtered.rename(columns={
        'index': 'cpi_index',
        'inflation': 'cpi_inflation_rate'
    })

    # Select target columns and deduplicate/sort
    cols = ['date', 'year_month', 'cpi_index', 'cpi_inflation_rate']
    df_cpi_old = df_filtered[cols].drop_duplicates(subset=['year_month']).sort_values('year_month').reset_index(drop=True)

    missing_count = df_cpi_old[['cpi_index', 'cpi_inflation_rate']].isna().sum().to_dict()
    print(f"[CPI OLD ETL] Extracted {len(df_cpi_old)} records from {df_cpi_old['year_month'].min()} to {df_cpi_old['year_month'].max()}")
    print(f"[CPI OLD ETL] Missing values: {missing_count}")

    return df_cpi_old

if __name__ == "__main__":
    df = extract_cpi_old()
    print(df.head())
    print(df.tail())
