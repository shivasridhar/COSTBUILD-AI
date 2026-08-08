import os
import pandas as pd
import config

def extract_wpi_old(file_path=None):
    """
    Extracts 2011-12 base WPI dataset from monthly_index_202606.csv.
    Extracts WPI All Commodities, OPC Cement, Cement Subgroup, Mild Steel Long Products, and Basic Metals Subgroup.
    Returns DataFrame with columns: year_month, wpi_all_commodities, wpi_cement, wpi_cement_subgroup, wpi_steel, wpi_steel_subgroup.
    """
    if file_path is None:
        file_path = config.WPI_OLD_FILE

    print(f"[WPI OLD ETL] Loading OLD WPI dataset from {file_path}...")
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"OLD WPI dataset not found at {file_path}")

    df_raw = pd.read_csv(file_path)

    targets = {
        'wpi_all_commodities': ['All commodities'],
        'wpi_cement': ['Ordinary Portland cement', 'Ordinary Portland Cement (OPC)'],
        'wpi_cement_subgroup': ['e. Manufacture of cement, lime and plaster', 'e.Manufacture of cement, lime and plaster'],
        'wpi_steel': ['d. Mild Steel -Long Products', 'Bars and Rods of Mild steel', 'MS Bright Bars'],
        'wpi_steel_subgroup': ['(N). MANUFACTURE OF BASIC METALS', 'a.Manufacture of basic iron and steel', 'c. Mild Steel - Semi Finished Steel']
    }

    indx_cols = [c for c in df_raw.columns if c.startswith('INDX')]
    results = {}
    for col in indx_cols:
        # INDXMMYYYY -> YYYY-MM
        m = col[4:6]
        y = col[6:10]
        ym = f"{y}-{m}"
        results[ym] = {'year_month': ym}

    comms = df_raw['COMM_NAME'].astype(str).str.strip()

    for var_name, aliases in targets.items():
        found_row = None
        for alias in aliases:
            match = df_raw[comms.str.lower() == alias.lower()]
            if match.empty:
                match = df_raw[comms.str.contains(alias, case=False, na=False, regex=False)]
            if not match.empty:
                found_row = match.iloc[0]
                break
        
        if found_row is not None:
            for col in indx_cols:
                m = col[4:6]
                y = col[6:10]
                ym = f"{y}-{m}"
                val = found_row[col]
                results[ym][var_name] = float(val) if pd.notna(val) else None
        else:
            print(f"[WPI OLD ETL WARNING] Target '{var_name}' could not be matched.")

    df_old_wpi = pd.DataFrame(list(results.values())).sort_values('year_month').reset_index(drop=True)
    missing_count = df_old_wpi.isna().sum().to_dict()
    print(f"[WPI OLD ETL] Extracted {len(df_old_wpi)} records from {df_old_wpi['year_month'].min()} to {df_old_wpi['year_month'].max()}")
    print(f"[WPI OLD ETL] Missing values: {missing_count}")

    return df_old_wpi

if __name__ == "__main__":
    df = extract_wpi_old()
    print(df.head())
    print(df.tail())
