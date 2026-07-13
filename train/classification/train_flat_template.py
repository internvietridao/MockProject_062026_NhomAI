# =============================================================
# 1. IMPORTS
# =============================================================
import json
import numpy as np
import pandas as pd
import warnings
import joblib
import os

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
import xgboost as xgb
import lightgbm as lgb
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    classification_report, confusion_matrix,
)

warnings.filterwarnings("ignore")

# =============================================================
# 2. CONFIGURATION
# =============================================================
RANDOM_STATE = 42
np.random.seed(RANDOM_STATE)

DATA_PATH  = r"D:\2026\MockProject_062026_NhomAI\data\healthcare_flat.json"        
TARGET_COL = "Level"            
TEST_SIZE  = 0.2                
VAL_SIZE   = 0.15              
MODEL_SAVE_DIR = r"D:\2026\MockProject_062026_NhomAI\model"  

# =============================================================
# 3. LOAD & PREPROCESS DATA
# =============================================================
print("=" * 60)
print("  LOAD & PREPROCESS FLAT DATA")
print("=" * 60)

with open(DATA_PATH, "r", encoding="utf-8") as f:
    raw_data = json.load(f)

FEATURES = [
    "Physical Activity", "Age", "Sleep Duration", "Stress Level", 
    "BMI", "Chronic Disease", "Smoking Status", "Alcohol Consumption", "Gender"
]

X_raw = []
y_raw = []

for record in raw_data:
    data = record.get("Data", {})
    row = []
    for feat in FEATURES:
        val = data.get(feat)
        if val is None:
            # Gán giá trị mặc định cho dữ liệu bị thiếu
            if feat in ["Chronic Disease", "Smoking Status", "Gender"]:
                val = "Unknown"
            else:
                val = 0.0
        row.append(val)
    X_raw.append(row)
    y_raw.append(record.get(TARGET_COL))

print(f"Total records loaded: {len(raw_data):,}")

# ---- Encode Categorical Features ----
feature_encoders = {}
X_raw = np.array(X_raw, dtype=object)
X_encoded = np.zeros((X_raw.shape[0], X_raw.shape[1]), dtype=np.float32)

for col_idx, feat in enumerate(FEATURES):
    col_data = X_raw[:, col_idx]
    is_string = any(isinstance(val, str) for val in col_data)
    if is_string:
        le = LabelEncoder()
        X_encoded[:, col_idx] = le.fit_transform(col_data.astype(str)).astype(np.float32)
        feature_encoders[col_idx] = le
        print(f"  Encoded categorical feature '{feat}'")
    else:
        X_encoded[:, col_idx] = col_data.astype(np.float32)

# ---- Encode Target ----
y_raw = np.array(y_raw)
le_target = LabelEncoder()
y = le_target.fit_transform(y_raw)
num_classes = len(le_target.classes_)
print(f"Target classes encoded: {dict(zip(le_target.classes_, le_target.transform(le_target.classes_)))}")
print(f"Class distribution: {dict(zip(le_target.classes_, np.bincount(y)))}")

# ---- Train / Test / Val Split (Stratified) ----
indices = np.arange(len(y))

# 1. Tách tập test
train_val_idx, test_idx = train_test_split(
    indices, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=y
)

# 2. Tách tập train và validation từ tập còn lại
val_ratio = VAL_SIZE / (1 - TEST_SIZE)
train_idx, val_idx = train_test_split(
    train_val_idx, test_size=val_ratio, random_state=RANDOM_STATE, stratify=y[train_val_idx]
)

X_train = X_encoded[train_idx]
X_val   = X_encoded[val_idx]
X_test  = X_encoded[test_idx]
y_train = y[train_idx]
y_val   = y[val_idx]
y_test  = y[test_idx]

# ---- Normalize numerical features (StandardScaler) ----
cols_to_scale = [col_idx for col_idx in range(len(FEATURES)) if col_idx not in feature_encoders]
scaler = None

if cols_to_scale:
    scaler = StandardScaler()
    X_train[:, cols_to_scale] = scaler.fit_transform(X_train[:, cols_to_scale])
    X_val[:, cols_to_scale]   = scaler.transform(X_val[:, cols_to_scale])
    X_test[:, cols_to_scale]  = scaler.transform(X_test[:, cols_to_scale])
    print(f"  Normalized numerical features: {[FEATURES[i] for i in cols_to_scale]}")

print(f"\nTrain samples: {len(train_idx)} | Val samples: {len(val_idx)} | Test samples: {len(test_idx)}")
print(f"Features shape: {X_train.shape}")

# =============================================================
# 4. TRAINING & COMPARING ML MODELS ON FLAT DATA
# =============================================================
print("\n" + "=" * 60)
print("  TRAINING & COMPARING ML MODELS")
print("=" * 60)

def get_model_instance(name):
    if name == "Random Forest":
        return RandomForestClassifier(n_estimators=200, random_state=RANDOM_STATE, n_jobs=-1)
    elif name == "Gradient Boosting":
        return GradientBoostingClassifier(n_estimators=150, learning_rate=0.1, max_depth=5, random_state=RANDOM_STATE)
    elif name == "XGBoost":
        return xgb.XGBClassifier(n_estimators=150, learning_rate=0.1, max_depth=6, random_state=RANDOM_STATE, n_jobs=-1, eval_metric="mlogloss", verbosity=0)
    elif name == "LightGBM":
        return lgb.LGBMClassifier(n_estimators=150, learning_rate=0.1, max_depth=6, random_state=RANDOM_STATE, n_jobs=-1, verbose=-1)
    return None

model_candidates = ["Random Forest", "Gradient Boosting", "XGBoost", "LightGBM"]
results = []

for name in model_candidates:
    print(f"\n{'-'*60}")
    print(f"  Training Model: {name}")
    print(f"{'-'*60}")
    
    model = get_model_instance(name)
    model.fit(X_train, y_train)
    
    y_val_pred  = model.predict(X_val)
    y_test_pred = model.predict(X_test)
    
    val_acc     = accuracy_score(y_val, y_val_pred)
    test_acc    = accuracy_score(y_test, y_test_pred)
    weighted_f1 = f1_score(y_test, y_test_pred, average="weighted", zero_division=0)
    macro_f1    = f1_score(y_test, y_test_pred, average="macro", zero_division=0)
    
    results.append({
        "model_name": name,
        "model_object": model,
        "predictions": y_test_pred,
        "val_accuracy": val_acc,
        "test_accuracy": test_acc,
        "weighted_f1": weighted_f1,
        "macro_f1": macro_f1
    })
    
    print(f"  [Model: {name}] -> Val Acc: {val_acc:.4f} | Test Acc: {test_acc:.4f} | Macro F1: {macro_f1:.4f}")

# =============================================================
# 5. EVALUATION & SELECTION
# =============================================================
print("\n" + "=" * 75)
print("  MODELS COMPARISON SUMMARY")
print("=" * 75)

comparison_df = pd.DataFrame(results)[[
    "model_name", "val_accuracy", "test_accuracy", "weighted_f1", "macro_f1"
]].sort_values("macro_f1", ascending=False)

print(comparison_df.to_string(index=False))

best_idx = next(i for i, r in enumerate(results) if r["model_name"] == comparison_df.iloc[0]["model_name"])
best_model_info = results[best_idx]
best_name = best_model_info["model_name"]

all_preds = best_model_info["predictions"]
all_targets = y_test

print(f"\n Best Model: {best_name}")
print(f"   Validation Accuracy: {best_model_info['val_accuracy']:.4f}")
print(f"   Test Accuracy      : {best_model_info['test_accuracy']:.4f}")
print(f"   Weighted F1-Score  : {best_model_info['weighted_f1']:.4f}")
print(f"   Macro F1-Score     : {best_model_info['macro_f1']:.4f}")

print(f"\nDetailed Classification Report — {best_name}:")
print(classification_report(all_targets, all_preds, target_names=[str(c) for c in le_target.classes_]))

print("\nConfusion Matrix:")
print(confusion_matrix(all_targets, all_preds))

# =============================================================
# 6. SAVE ALL TRAINED MODELS INDIVIDUALLY
# =============================================================
print("\n" + "=" * 60)
print("  SAVING ALL TRAINED MODELS")
print("=" * 60)

for r in results:
    model_name = r["model_name"]
    file_name = f"{model_name.lower().replace(' ', '_')}_flat_pipeline.pkl"
    file_path = os.path.join(MODEL_SAVE_DIR, file_name)
    
    pipeline_data = {
        "model_name": model_name,
        "model": r["model_object"],
        "feature_encoders": feature_encoders,
        "scaler": scaler,
        "cols_to_scale": cols_to_scale,
        "target_encoder": le_target,
        "features": FEATURES
    }
    
    joblib.dump(pipeline_data, file_path)
    print(f"Saved model '{model_name}' to '{file_path}'")
