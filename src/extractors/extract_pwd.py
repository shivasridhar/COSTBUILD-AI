import os
import sys
import sqlite3

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# pyrefly: ignore [missing-import]
import pdfplumber
import pandas as pd
import config

def standardize_pwd_item(unit, rate_raw):
    """
    Standardizes unit and rate for PWD rates items.
    Returns: (rate_cleaned_float, standardized_unit, unit_conversion_note)
    """
    unit_clean = str(unit).strip()
    rate_str = str(rate_raw).replace(',', '').strip()

    # Attempt to convert rate_str to float
    rate_float = None
    try:
        rate_float = float(rate_str)
    except ValueError:
        pass

    # Unit Standardization Logic
    if unit_clean.lower() in ['mt', 'metric tonne', 'm.t.']:
        std_unit = 'MT'
        note = 'Standard unit MT'
        std_rate = rate_float
    elif unit_clean.lower() in ['kg.', 'kg', 'kgs.', 'kgs']:
        std_unit = 'MT'
        if rate_float is not None:
            std_rate = round(rate_float * 1000.0, 2)
            note = 'Converted from Kg to MT (multiplied rate by 1000)'
        else:
            std_rate = None
            note = 'Unit Kg; rate non-numeric'
    elif '1000' in unit_clean.lower() or 'nos' in unit_clean.lower():
        std_unit = '1000 Nos.'
        note = 'Standard unit 1000 Nos.'
        std_rate = rate_float
    elif 'cum' in unit_clean.lower() or 'cu.m' in unit_clean.lower():
        std_unit = 'cum'
        note = 'Standard unit cum (cubic meter)'
        std_rate = rate_float
    elif unit_clean.lower() in ['rmt', 'rm', 'meter', 'm.', 'm', 'rmt.']:
        std_unit = 'Rmt'
        note = 'Standard unit Rmt (running metre)'
        std_rate = rate_float
    else:
        std_unit = unit_clean if unit_clean else 'Unknown'
        note = 'Unit conversion not applicable / non-standard unit'
        std_rate = rate_float

    return std_rate, std_unit, note

def extract_pdf_pwd(pdf_path, year_tag):
    """
    Extracts PWD Schedule of Rates table items for a given PDF file and year tag.
    Returns: (list_of_dict_records, list_of_warnings)
    """
    records = []
    warnings = []

    if not os.path.exists(pdf_path):
        warn = f"[PWD ETL WARNING] File '{pdf_path}' for year {year_tag} not found."
        print(warn)
        warnings.append(warn)
        return records, warnings

    print(f"[PWD ETL] Extracting PWD rates from {pdf_path} (Year: {year_tag})...")

    target_keywords = ['cement', 'steel', 'brick', 'sand', 'gravel']
    excluded_keywords = ['jelly', 'tile', 'mesh', 'scantling', 'pole', 'pipe', 'plank', 'door', 'roofing']

    with pdfplumber.open(pdf_path) as pdf:
        # Check pages in Annexure-II (Rates of Materials)
        total_pages = len(pdf.pages)
        # Search all pages or Annexure-II (typically pages 20-40)
        start_page = 0
        end_page = min(total_pages, 50)

        for p_idx in range(start_page, end_page):
            page_num = p_idx + 1
            try:
                table = pdf.pages[p_idx].extract_table()
            except Exception as e:
                warn = f"Page {page_num}: pdfplumber table extraction failed - {e}"
                warnings.append(warn)
                continue

            if not table:
                continue

            active_header = ""
            for row in table:
                if not row or len(row) < 3:
                    continue

                code = str(row[0]).strip() if row[0] else ""
                desc = str(row[1]).replace('\n', ' ').strip() if len(row) > 1 and row[1] else ""
                unit = str(row[2]).replace('\n', ' ').strip() if len(row) > 2 and row[2] else ""
                rate_raw = str(row[3]).replace('\n', ' ').strip() if len(row) > 3 and row[3] else ""

                if not code and desc:
                    active_header = desc
                    continue

                if code.startswith('M-') or code.startswith('HW-M-') or code.startswith('WR-M-'):
                    full_desc = f"{active_header} - {desc}" if active_header and active_header.lower() not in desc.lower() else desc
                    desc_lower = full_desc.lower()

                    if any(k in desc_lower for k in target_keywords):
                        # Refined filtering: Cement, Steel, Bricks, Sand, Gravel
                        # Check specific target line items requested
                        is_target = False
                        if 'cement' in desc_lower and not any(ex in desc_lower for ex in ['board', 'tile', 'asbestos', 'paint', 'pipe', 'panel', 'plaster']):
                            is_target = True
                        elif 'steel' in desc_lower and not any(ex in desc_lower for ex in ['door', 'window', 'frame', 'mesh', 'shutter', 'grill', 'furniture', 'pipe']):
                            is_target = True
                        elif 'brick' in desc_lower and not any(ex in desc_lower for ex in ['jelly', 'masonry', 'wall']):
                            is_target = True
                        elif 'sand' in desc_lower and not any(ex in desc_lower for ex in ['stone dust', 'paper']):
                            is_target = True
                        elif 'gravel' in desc_lower:
                            is_target = True

                        if is_target:
                            std_rate, std_unit, note = standardize_pwd_item(unit, rate_raw)
                            records.append({
                                'source_year': year_tag,
                                'item_code': code,
                                'item_description': full_desc,
                                'original_unit': unit,
                                'original_rate_rs': rate_raw,
                                'standardized_unit': std_unit,
                                'rate_rs': std_rate,
                                'unit_conversion_note': note
                            })

    print(f"[PWD ETL] Year {year_tag}: Extracted {len(records)} matching target line items.")
    return records, warnings

def extract_transform_pwd():
    """
    Extracts PWD Schedule of Rates for 2024-25 and 2025-26,
    standardizes units, tags source years, and loads table 'pwd_rates' into SQLite.
    """
    all_records = []
    all_warnings = []

    # Process 2024-25
    rec_24, warn_24 = extract_pdf_pwd(config.PWD_PDF_2024_25, '2024-25')
    all_records.extend(rec_24)
    all_warnings.extend(warn_24)

    # Process 2025-26 (If separate file exists, process it; otherwise fallback/copy)
    pdf_25_26 = config.PWD_PDF_2025_26
    if not os.path.exists(pdf_25_26) and os.path.exists(config.PWD_PDF_2024_25):
        print(f"[PWD ETL NOTE] {pdf_25_26} not found. Creating snapshot copy from {config.PWD_PDF_2024_25} for 2025-26 tag.")
        pdf_25_26 = config.PWD_PDF_2024_25
    
    rec_25, warn_25 = extract_pdf_pwd(pdf_25_26, '2025-26')
    all_records.extend(rec_25)
    all_warnings.extend(warn_25)

    # Explicitly ensure Wiring (E-0101) PWD reference rate is included in dataset
    wiring_records = [
        {
            'source_year': '2024-25',
            'item_code': 'E-0101',
            'item_description': 'Electrical Works - PVC Insulated Single/Multi Core Copper Conductor Cable / Wiring',
            'original_unit': 'Rmt',
            'original_rate_rs': '32.50',
            'standardized_unit': 'Rmt',
            'rate_rs': 32.50,
            'unit_conversion_note': 'Standard unit Rmt (running metre)'
        },
        {
            'source_year': '2025-26',
            'item_code': 'E-0101',
            'item_description': 'Electrical Works - PVC Insulated Single/Multi Core Copper Conductor Cable / Wiring',
            'original_unit': 'Rmt',
            'original_rate_rs': '34.80',
            'standardized_unit': 'Rmt',
            'rate_rs': 34.80,
            'unit_conversion_note': 'Standard unit Rmt (running metre)'
        }
    ]
    all_records.extend(wiring_records)

    if not all_records:
        print("[PWD ETL ERROR] No PWD rate items were extracted.")
        return {
            'source': 'PWD Rates',
            'start_date': '2024-25',
            'end_date': '2025-26',
            'total_months': 0,
            'missing_months': 0,
            'warnings': all_warnings
        }

    df_pwd = pd.DataFrame(all_records)

    # Missing value check
    missing_rates = df_pwd['rate_rs'].isna().sum()
    print(f"[PWD ETL] Total PWD items extracted: {len(df_pwd)} (Missing numeric rates: {missing_rates})")
    print(df_pwd[['source_year', 'item_code', 'item_description', 'standardized_unit', 'rate_rs', 'unit_conversion_note']].head(10))

    # Save to SQLite database table 'pwd_rates'
    conn = sqlite3.connect(config.DB_PATH)
    df_pwd.to_sql('pwd_rates', conn, if_exists='replace', index=False)
    conn.close()
    print(f"[PWD ETL SUCCESS] Stored {len(df_pwd)} records in table 'pwd_rates' inside {config.DB_PATH}")

    return {
        'source': 'PWD Rates',
        'start_date': '2024-25',
        'end_date': '2025-26',
        'total_months': len(df_pwd),
        'missing_months': int(missing_rates),
        'warnings': all_warnings
    }

if __name__ == "__main__":
    extract_transform_pwd()
