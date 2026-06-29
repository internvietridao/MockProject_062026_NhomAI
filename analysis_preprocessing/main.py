import pandas as pd
from src.eda import run_global_eda
from src.preprocessing import handle_missing_data, transform_features

def main():
    data_path = "data/nursing_home.csv"
    raw_data = pd.read_csv(data_path)    
    run_global_eda(raw_data)
    clean_data = handle_missing_data(raw_data)
    final_dataset = transform_features(clean_data)
    print("\n=== FINAL PREPROCESSED DATASET FOR MODEL TRAINING ===")
    print(final_dataset.head())

if __name__ == "__main__":
    main()