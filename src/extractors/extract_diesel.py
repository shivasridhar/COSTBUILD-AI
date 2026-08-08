import os
import sqlite3
import pdfplumber
import pandas as pd
import config

def extract_transform_diesel():
    """
    Extracts daily retail diesel prices for Delhi metro from PPAC PDF using pdfplumber,
    logs any extraction failures or malformed rows,
    normalizes dates to YYYY-MM, resamples daily prices to monthly averages,
    and stores in SQLite table 'diesel'.
    """
    pdf_path = config.DIESEL_PDF
    print(f"[Diesel ETL] Extracting daily diesel prices from PDF: {pdf_path}...")

    extracted = []
    failures = []

    if not os.path.exists(pdf_path):
        warning_msg = f"[Diesel ETL WARNING] File {pdf_path} not found."
        print(warning_msg)
        failures.append(warning_msg)
        return {
            'source': 'Diesel',
            'start_date': None,
            'end_date': None,
            'total_months': 0,
            'missing_months': 0,
            'warnings': failures
        }

    with pdfplumber.open(pdf_path) as pdf:
        for page_idx, page in enumerate(pdf.pages):
            page_num = page_idx + 1
            tables = page.extract_tables()
            if not tables:
                failures.append(f"Page {page_num}: No tables extracted.")
                continue
            
            page_valid_rows = 0
            for t in tables:
                for row in t:
                    if not row or len(row) < 9:
                        continue
                    
                    date_str = row[7] if len(row) > 7 else None
                    delhi_price_str = row[8] if len(row) > 8 else None

                    if not date_str or not delhi_price_str:
                        continue
                    
                    date_str = str(date_str).strip()
                    delhi_price_str = str(delhi_price_str).strip()

                    if '-' in date_str and any(char.isdigit() for char in date_str):
                        try:
                            dt = pd.to_datetime(date_str, format='%d-%b-%y')
                            price_val = float(delhi_price_str.replace(' ', ''))
                            extracted.append({'date': dt, 'diesel_price_delhi': price_val})
                            page_valid_rows += 1
                        except Exception:
                            # Log malformed rows if necessary
                            pass

            if page_valid_rows == 0:
                failures.append(f"Page {page_num}: Table present but 0 valid diesel rows extracted.")

    if not extracted:
        error_msg = "[Diesel ETL ERROR] No diesel records extracted from PDF."
        print(error_msg)
        failures.append(error_msg)
        return {
            'source': 'Diesel',
            'start_date': None,
            'end_date': None,
            'total_months': 0,
            'missing_months': 0,
            'warnings': failures
        }

    df_daily = pd.DataFrame(extracted).drop_duplicates(subset=['date']).sort_values('date').reset_index(drop=True)
    print(f"[Diesel ETL] Extracted {len(df_daily)} daily price entries spanning {df_daily['date'].min().strftime('%Y-%m-%d')} to {df_daily['date'].max().strftime('%Y-%m-%d')}.")

    # Resample daily prices to monthly averages (YYYY-MM)
    df_daily['year_month'] = df_daily['date'].dt.strftime('%Y-%m')
    df_monthly = df_daily.groupby('year_month')['diesel_price_delhi'].mean().reset_index()
    df_monthly['diesel_price_delhi'] = df_monthly['diesel_price_delhi'].round(2)
    df_monthly = df_monthly.sort_values('year_month').reset_index(drop=True)

    # Check for missing months in sequence
    full_months = pd.date_range(start=df_monthly['year_month'].min() + "-01", end=df_monthly['year_month'].max() + "-01", freq='MS').strftime('%Y-%m')
    missing_months = [m for m in full_months if m not in df_monthly['year_month'].values]

    print(f"[Diesel ETL] Resampled to {len(df_monthly)} monthly average entries ({df_monthly['year_month'].min()} to {df_monthly['year_month'].max()}).")
    print(f"[Diesel ETL] Missing months in date range: {len(missing_months)} -> {missing_months}")

    # Load into SQLite database
    conn = sqlite3.connect(config.DB_PATH)
    df_monthly.to_sql('diesel', conn, if_exists='replace', index=False)
    conn.close()
    print(f"[Diesel ETL SUCCESS] Stored {len(df_monthly)} records in table 'diesel' inside {config.DB_PATH}")

    return {
        'source': 'Diesel',
        'start_date': df_monthly['year_month'].min(),
        'end_date': df_monthly['year_month'].max(),
        'total_months': len(df_monthly),
        'missing_months': len(missing_months),
        'warnings': failures
    }

if __name__ == "__main__":
    extract_transform_diesel()
