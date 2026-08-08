import os

# Base Directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DATA_DIR = os.path.join(BASE_DIR, "data", "raw")
PROCESSED_DATA_DIR = os.path.join(BASE_DIR, "data", "processed")
MODELS_DIR = os.path.join(BASE_DIR, "models_artifacts")
DOWNLOADS_DIR = r"C:\Users\Asus\Downloads"

# Database & Output Paths
DB_PATH = os.path.join(BASE_DIR, "buildcost.db")
FINAL_CSV_PATH = os.path.join(BASE_DIR, "final_training_dataset.csv")

# Input File Candidate Paths (Checks data/raw/ first, then root, then Downloads)
def get_file_path(local_name, download_name):
    raw_path = os.path.join(RAW_DATA_DIR, local_name)
    if os.path.exists(raw_path):
        return raw_path
    local_path = os.path.join(BASE_DIR, local_name)
    if os.path.exists(local_path):
        return local_path
    download_path = os.path.join(DOWNLOADS_DIR, download_name)
    if os.path.exists(download_path):
        return download_path
    return raw_path

WPI_FILE = get_file_path("wpi_monthly_index_202607.csv", "wpi_monthly_index_202607.xlsx")
WPI_XLSX_FILE = get_file_path("wpi_monthly_index_202607.xlsx", "wpi_monthly_index_202607.xlsx")
WPI_OLD_FILE = get_file_path("monthly_index_202606.csv", "monthly_index_202606.csv")

CPI_FILE = get_file_path("cpi_1590.csv", "cpi_1590.csv")
CPI_OLD_FILE = get_file_path("cpi_1435.csv", "cpi_1435.csv")

RAINFALL_FILE = get_file_path("rainfall_1901_2015.csv", "rainfall_area-wt_India_1901-2015.csv")

DIESEL_PDF = get_file_path(
    "diesel_prices.pdf", 
    "1785738928_PP_9_a_DailyPriceMSHSD_Metro_03.08.2026.pdf"
)

PWD_PDF_2024_25 = get_file_path("tn_pwd_rates_2024_25.pdf", "SOR_2024_25.pdf")
PWD_PDF_2025_26 = get_file_path("tn_pwd_rates_2025_26.pdf", "tn_pwd_rates_2025_26.pdf")
