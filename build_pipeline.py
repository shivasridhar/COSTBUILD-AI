import os
import sys

# Ensure root workspace directory is in sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.transformers.splice_wpi import splice_wpi
from src.transformers.splice_cpi import splice_cpi
from src.extractors.extract_rainfall import extract_transform_rainfall
from src.extractors.extract_diesel import extract_transform_diesel
from src.extractors.extract_pwd import extract_transform_pwd
from src.pipeline.merge_pipeline import run_merge_pipeline

def run_all():
    print("==================================================")
    print("      BUILDCOST AI ETL PIPELINE EXECUTION         ")
    print("==================================================")

    summaries = []

    # Run extraction scripts independently
    print("\n--- [Step 1/5] Extracting & Splicing WPI Data ---")
    summaries.append(splice_wpi())

    print("\n--- [Step 2/5] Extracting & Splicing CPI Data ---")
    summaries.append(splice_cpi())

    print("\n--- [Step 3/5] Extracting Rainfall Data ---")
    summaries.append(extract_transform_rainfall())

    print("\n--- [Step 4/5] Extracting Diesel PDF Data ---")
    summaries.append(extract_transform_diesel())

    print("\n--- [Step 5/5] Extracting PWD Rates PDF Data ---")
    summaries.append(extract_transform_pwd())

    # Run merge pipeline
    print("\n--- [Step 6] Merging Datasets & Exporting Final CSV ---")
    df_final = run_merge_pipeline(summaries)

    # Initialize projects and vendor_quotes tables in buildcost.db
    from migrate_add_projects import run_migration
    run_migration()
    from src.optimization.bom_optimizer import init_vendor_quotes_table
    init_vendor_quotes_table()

    print("\n--- [Step 7] Running Walk-Forward Forecast Backtest & Error Matrix ---")
    from src.analysis.backtest import run_walk_forward_backtest
    run_walk_forward_backtest()

    print("\n[SUCCESS] BuildCost AI ETL Pipeline execution finished cleanly!")


if __name__ == "__main__":
    run_all()
