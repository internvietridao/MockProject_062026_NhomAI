import pandas as pd

def run_global_eda(df):
    print("=== SUMMARY OF THE DATASET ===")
    print(df.info())
    print("\n=== DESCRIPTIVE STATISTICS ===")
    print(df.describe())
    print("\n=== MISSING VALUES RATIO (%) ===")
    missing_ratio = df.isnull().mean() * 100
    print(missing_ratio)
    return missing_ratio