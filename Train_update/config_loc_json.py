# config_loc_json.py
# Configuration for Nursing Home LOC classification using a 5-core JSON dataset.

from pathlib import Path

RANDOM_STATE = 42
TEST_SIZE = 0.2

# Project paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent if Path(__file__).resolve().parent.name == "train" else Path.cwd()
TRAIN_DIR = PROJECT_ROOT / "train"
MODEL_DIR = PROJECT_ROOT / "models"

# Input CSV from Kaggle proxy dataset
RAW_CSV_PATH = TRAIN_DIR / "heart_disease_health_indicators_BRFSS2015.csv"
if not RAW_CSV_PATH.exists():
    RAW_CSV_PATH = PROJECT_ROOT / "heart_disease_health_indicators_BRFSS2015.csv"

# Converted 5-core JSON dataset
JSON_DATA_PATH = TRAIN_DIR / "heart_disease_loc_5core.json"

# Output model
MODEL_PATH = MODEL_DIR / "loc_json_best_model.pkl"

# Use only older adults for nursing-home-like proxy context.
# BRFSS Age is categorical: Age >= 7 is approximately 50+.
MIN_AGE_GROUP = 7

# Stricter proxy filter for data that better matches nursing-home-like cases.
# Set STRICT_FILTER = False to keep the broader age selection.
STRICT_FILTER = True
STRICT_MIN_AGE_GROUP = 9

# Keep these models only.
MODEL_NAMES = [
    "Logistic Regression",
    "Random Forest",
    "XGBoost",
    "LightGBM",
]
