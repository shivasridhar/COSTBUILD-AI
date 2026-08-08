import pandas as pd
import numpy as np

def audit_dataset(csv_path="final_training_dataset.csv"):
    print("==================================================")
    print("     BUILDCOST AI: DATASET AUDIT & EDA REPORT     ")
    print("==================================================\n")
    
    # 1. Load Dataset
    df = pd.read_csv(csv_path)
    
    # 2. Basic Dimensions & Timeline Coverage
    print("1. SHAPE & TIMELINE COVERAGE")
    print(f"   • Total Rows (Months): {df.shape[0]}")
    print(f"   • Total Columns (Features): {df.shape[1]}")
    if 'year_month' in df.columns:
        print(f"   • Start Month: {df['year_month'].min()}")
        print(f"   • End Month:   {df['year_month'].max()}")
    print("-" * 50)
    
    # 3. Column Data Types & Missing Value Audit
    print("\n2. MISSING VALUES & DATA TYPES AUDIT")
    null_counts = df.isnull().sum()
    null_pct = (df.isnull().sum() / len(df)) * 100
    
    audit_df = pd.DataFrame({
        'Data Type': df.dtypes,
        'Missing Values': null_counts,
        'Missing (%)': null_pct.round(2)
    })
    print(audit_df.to_string())
    print("-" * 50)
    
    # 4. Numerical Distribution & Outlier Audit
    print("\n3. STATISTICAL DISTRIBUTION AUDIT")
    num_cols = df.select_dtypes(include=[np.number]).columns
    stats = df[num_cols].describe().T[['mean', 'std', 'min', '50%', 'max']]
    stats.columns = ['Mean', 'Std Dev', 'Min', 'Median (50%)', 'Max']
    print(stats.round(2).to_string())
    print("-" * 50)
    
    # 5. Chronological Continuity & Duplicate Check
    print("\n4. TIMELINE INTEGRITY & DUPLICATE CHECK")
    if 'year_month' in df.columns:
        duplicates = df['year_month'].duplicated().sum()
        print(f"   • Duplicate Months Found: {duplicates}")
        
        # Check chronological order
        is_sorted = df['year_month'].is_monotonic_increasing
        print(f"   • Strictly Chronologically Sorted: {is_sorted}")
    print("-" * 50)

if __name__ == "__main__":
    audit_dataset()
