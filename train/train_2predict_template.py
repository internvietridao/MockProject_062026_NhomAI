# =============================================================
# 1. IMPORTS
# =============================================================
import json
import numpy as np
import pandas as pd
import warnings
import joblib

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

DATA_PATH  = "data.json"        
TARGET_COL = "Level"            
CORES_KEY  = "5_cores"          
TEST_SIZE  = 0.2                
VAL_SIZE   = 0.15              
MODEL_SAVE_PATH = "multiview_random_forest.pkl"  

# =============================================================
# 3. LOAD & PREPROCESS DATA (NO DATAFRAME FLATTENING)
# =============================================================
print("=" * 60)
print("  LOAD & PREPROCESS DATA")
print("=" * 60)

with open(DATA_PATH, "r", encoding="utf-8") as f:
    raw_data = json.load(f)

CORE_FEATURES = {
    "ADLs": ["Age", "Physical Activity"],
    "Cognitive": ["Sleep Duration", "Stress Level"],
    "Clinical": ["BMI", "Chronic Disease"],
    "Mood": ["Stress Level", "Smoking", "Alcohol"],
    "Financial": ["Age", "Gender", "Chronic Disease"]
}

X_raw = {core_name: [] for core_name in CORE_FEATURES.keys()}
y_raw = []

for record in raw_data:
    cores = record.get("5_cores", record.get("5 cores", {}))
    for core_name, feat_list in CORE_FEATURES.items():
        core_data = cores.get(core_name, {})
        row = []
        for feat in feat_list:
            val = core_data.get(feat, 0)
            row.append(val)
        X_raw[core_name].append(row)
    y_raw.append(record.get(TARGET_COL))

print(f"Total records loaded: {len(raw_data):,}")

# ---- Encode Feature độc lập cho từng feature của từng Core ----
feature_encoders = {}
X_encoded = {core_name: [] for core_name in CORE_FEATURES.keys()}

for core_name, feat_list in CORE_FEATURES.items():
    arr = np.array(X_raw[core_name], dtype=object)
    encoded_cols = []
    
    for col_idx in range(arr.shape[1]):
        col_data = arr[:, col_idx]
        
        # Nếu cột chứa dữ liệu dạng chữ (string), tiến hành Label Encoding
        is_string = any(isinstance(val, str) for val in col_data)
        if is_string:
            le = LabelEncoder()
            encoded_col = le.fit_transform(col_data.astype(str)).astype(np.float32)
            feature_encoders[(core_name, col_idx)] = le
            print(f"  Encoded feature '{feat_list[col_idx]}' in Core '{core_name}'")
        else:
            encoded_col = col_data.astype(np.float32)
            
        encoded_cols.append(encoded_col)
    
    X_encoded[core_name] = np.stack(encoded_cols, axis=1)

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

X_train_cores = {core: X_encoded[core][train_idx] for core in X_encoded}
X_val_cores   = {core: X_encoded[core][val_idx] for core in X_encoded}
X_test_cores  = {core: X_encoded[core][test_idx] for core in X_encoded}
y_train = y[train_idx]
y_val   = y[val_idx]
y_test  = y[test_idx]

# ---- Normalize độc lập từng Core (StandardScaler) ----
core_scalers = {}
from sklearn.preprocessing import StandardScaler

for core_name, feat_list in CORE_FEATURES.items():
    arr_train = X_train_cores[core_name]
    arr_val   = X_val_cores[core_name]
    arr_test  = X_test_cores[core_name]
    
    # Chỉ chuẩn hóa những cột nguyên bản là dữ liệu số (không bị mã hóa bởi LabelEncoder)
    cols_to_scale = []
    for col_idx in range(arr_train.shape[1]):
        if (core_name, col_idx) not in feature_encoders:
            cols_to_scale.append(col_idx)
            
    if cols_to_scale:
        scaler = StandardScaler()
        arr_train[:, cols_to_scale] = scaler.fit_transform(arr_train[:, cols_to_scale])
        arr_val[:, cols_to_scale]   = scaler.transform(arr_val[:, cols_to_scale])
        arr_test[:, cols_to_scale]  = scaler.transform(arr_test[:, cols_to_scale])
        core_scalers[core_name] = scaler
        print(f"  Normalized numerical features for Core '{core_name}': {[feat_list[i] for i in cols_to_scale]}")
        
    X_train_cores[core_name] = arr_train
    X_val_cores[core_name]   = arr_val
    X_test_cores[core_name]  = arr_test

# Định nghĩa số lượng chiều đầu vào cho từng nhánh
core_input_dims = {core: len(features) for core, features in CORE_FEATURES.items()}

print(f"\nTrain samples: {len(train_idx)} | Val samples: {len(val_idx)} | Test samples: {len(test_idx)}")
for core_name, dim in core_input_dims.items():
    print(f"  Branch '{core_name}' -> Input Dimension: {dim}")

# =============================================================
# 4. TRAINING & COMPARING HOMOGENEOUS STACKED PIPELINES
# =============================================================
print("\n" + "=" * 60)
print("  TRAINING & COMPARING COHESIVE PIPELINES")
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


def build_meta_features(data, current_base_models):
    meta = []
    for core_name in core_input_dims:
        prob = current_base_models[core_name].predict_proba(data[core_name])
        meta.append(prob)
    return np.hstack(meta)


pipeline_candidates = ["Random Forest", "Gradient Boosting", "XGBoost", "LightGBM"]
meta_results = []

for name in pipeline_candidates:
    print(f"\n{'-'*60}")
    print(f"  Training Stacked Pipeline: {name}")
    print(f"{'-'*60}")
    
    # 1. Huấn luyện 5 base models con tương ứng
    curr_base_models = {}
    print("  Base Models Accuracy on Test Set:")
    for core_name in core_input_dims:
        model = get_model_instance(name)
        model.fit(X_train_cores[core_name], y_train)
        curr_base_models[core_name] = model
        
        pred = model.predict(X_test_cores[core_name])
        acc = accuracy_score(y_test, pred)
        print(f"    {core_name:<15}: {acc:.4f}")
        
    # 2. Tạo tập đặc trưng Meta cho Train, Val và Test
    X_train_meta = build_meta_features(X_train_cores, curr_base_models)
    X_val_meta   = build_meta_features(X_val_cores, curr_base_models)
    X_test_meta  = build_meta_features(X_test_cores, curr_base_models)
    
    # 3. Huấn luyện mô hình Meta cùng thuật toán
    meta_model = get_model_instance(name)
    if name == "Random Forest":
        meta_model.set_params(n_estimators=300)
    meta_model.fit(X_train_meta, y_train)
    
    # 4. Dự đoán trên tập Val và Test thông qua mô hình Meta
    y_val_pred  = meta_model.predict(X_val_meta)
    y_test_pred = meta_model.predict(X_test_meta)
    
    # 5. Tính toán metrics của mô hình tổng
    val_acc     = accuracy_score(y_val, y_val_pred)
    test_acc    = accuracy_score(y_test, y_test_pred)
    weighted_f1 = f1_score(y_test, y_test_pred, average="weighted", zero_division=0)
    macro_f1    = f1_score(y_test, y_test_pred, average="macro", zero_division=0)
    
    meta_results.append({
        "pipeline_name": name,
        "base_models": curr_base_models,
        "meta_model": meta_model,
        "predictions": y_test_pred,
        "val_accuracy": val_acc,
        "test_accuracy": test_acc,
        "weighted_f1": weighted_f1,
        "macro_f1": macro_f1
    })
    
    print(f"\n  [Meta Model: {name}] -> Val Acc: {val_acc:.4f} | Test Acc: {test_acc:.4f} | Macro F1: {macro_f1:.4f}")

# =============================================================
# 5. EVALUATION & SELECTION
# =============================================================
print("\n" + "=" * 75)
print("  PIPELINES COMPARISON SUMMARY")
print("=" * 75)

comparison_df = pd.DataFrame(meta_results)[[
    "pipeline_name", "val_accuracy", "test_accuracy", "weighted_f1", "macro_f1"
]].sort_values("macro_f1", ascending=False)

print(comparison_df.to_string(index=False))

# Lựa chọn Pipeline tốt nhất dựa trên Macro F1
best_idx = next(i for i, r in enumerate(meta_results) if r["pipeline_name"] == comparison_df.iloc[0]["pipeline_name"])
best_pipeline = meta_results[best_idx]
best_name = best_pipeline["pipeline_name"]

all_preds = best_pipeline["predictions"]
all_targets = y_test

print(f"\n Best Pipeline: {best_name}")
print(f"   Validation Accuracy: {best_pipeline['val_accuracy']:.4f}")
print(f"   Test Accuracy      : {best_pipeline['test_accuracy']:.4f}")
print(f"   Weighted F1-Score  : {best_pipeline['weighted_f1']:.4f}")
print(f"   Macro F1-Score     : {best_pipeline['macro_f1']:.4f}")

print(f"\nDetailed Classification Report — {best_name}:")
print(classification_report(all_targets, all_preds, target_names=le_target.classes_))

print("\nConfusion Matrix:")
print(confusion_matrix(all_targets, all_preds))

# =============================================================
# 6. SAVE ALL TRAINED PIPELINES
# =============================================================
print("\n" + "=" * 60)
print("  SAVING ALL TRAINED PIPELINES")
print("=" * 60)

# Đóng gói toàn bộ 4 pipelines của 4 thuật toán
pipelines_to_save = {}
for r in meta_results:
    pipelines_to_save[r["pipeline_name"]] = {
        "base_models": r["base_models"],
        "meta_model": r["meta_model"]
    }

joblib.dump(
    {
        "pipelines": pipelines_to_save,
        "best_pipeline_name": best_name,
        "feature_encoders": feature_encoders,
        "core_scalers": core_scalers,
        "target_encoder": le_target,
        "core_features": CORE_FEATURES
    },
    MODEL_SAVE_PATH
)
print(f"All {len(pipelines_to_save)} pipelines successfully saved to '{MODEL_SAVE_PATH}'!")

