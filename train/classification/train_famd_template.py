# =============================================================
# 1. IMPORTS
# =============================================================
import json
import numpy as np
import pandas as pd
import warnings
import joblib
import prince

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

DATA_PATH  = r"D:\2026\MockProject_062026_NhomAI\data\healthcare_5cores.json"        
TARGET_COL = "Level"            
CORES_KEY  = "5_cores"          
TEST_SIZE  = 0.2                
VAL_SIZE   = 0.15              
MODEL_SAVE_DIR = r"D:\2026\MockProject_062026_NhomAI\model"  

# =============================================================
# 3. LOAD & PREPROCESS DATA (NO DATAFRAME FLATTENING)
# =============================================================
print("=" * 60)
print("  LOAD & PREPROCESS DATA")
print("=" * 60)

with open(DATA_PATH, "r", encoding="utf-8") as f:
    raw_data = json.load(f)

CORE_FEATURES = {
    "ADLs & IADLs": ["Age", "Physical Activity"],
    "Cognitive & Neurological Status": ["Sleep Duration", "Stress Level"],
    "Clinical Risk Assessments": ["BMI", "Chronic Disease"],
    "Mood & Behavioral Health": ["Stress Level", "Smoking Status", "Alcohol Consumption"],
    "Financial & Legal": ["Age", "Gender", "Chronic Disease"]
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
            if val is None:
                if feat in ["Chronic Disease", "Smoking Status", "Gender"]:
                    val = "Unknown"
                else:
                    val = 0.0
            row.append(val)
        X_raw[core_name].append(row)
    y_raw.append(record.get(TARGET_COL))

print(f"Total records loaded: {len(raw_data):,}")

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

y_train = y[train_idx]
y_val   = y[val_idx]
y_test  = y[test_idx]

# =============================================================
# 4. FAMD FOR MIXED DATA DIMENSIONALITY REDUCTION (PER CORE)
# =============================================================
print("\n" + "=" * 60)
print("  APPLYING FAMD DIMENSIONALITY REDUCTION")
print("=" * 60)

famd_transformers = {}
X_train_famd_list = []
X_val_famd_list   = []
X_test_famd_list  = []

for core_name, feat_list in CORE_FEATURES.items():
    # Khởi dựng DataFrame cho Core hiện tại từ dữ liệu thô (để giữ nguyên kiểu dữ liệu số/chuỗi)
    df_core = pd.DataFrame(X_raw[core_name], columns=feat_list)
    
    # Ép kiểu dữ liệu để prince.FAMD nhận diện chính xác
    for col in df_core.columns:
        if df_core[col].dtype == object or isinstance(df_core[col].iloc[0], str):
            df_core[col] = df_core[col].astype(str).astype("category")
        else:
            df_core[col] = df_core[col].astype("float64")

    df_train = df_core.iloc[train_idx].reset_index(drop=True)
    df_val   = df_core.iloc[val_idx].reset_index(drop=True)
    df_test  = df_core.iloc[test_idx].reset_index(drop=True)
    
    has_categorical = any(df_core[col].dtype.name == "category" for col in df_core.columns)
    
    if has_categorical:
        famd = prince.FAMD(
            n_components=1,
            n_iter=10,
            copy=True,
            check_input=True,
            random_state=RANDOM_STATE
        )
        famd.fit(df_train)
        famd_transformers[core_name] = famd
        explained_variance = famd.percentage_of_variance_
        print(f"  Core {core_name:<12} (FAMD) -> Explained Variance (1st Component): {explained_variance[0]:.2f}%")
        X_train_famd_list.append(famd.transform(df_train).values.astype(np.float32))
        X_val_famd_list.append(famd.transform(df_val).values.astype(np.float32))
        X_test_famd_list.append(famd.transform(df_test).values.astype(np.float32))
    else:
        pca = prince.PCA(
            n_components=1,
            n_iter=10,
            copy=True,
            check_input=True,
            random_state=RANDOM_STATE
        )
        pca.fit(df_train)
        famd_transformers[core_name] = pca
        explained_variance = pca.percentage_of_variance_
        print(f"  Core {core_name:<12} (PCA)  -> Explained Variance (1st Component): {explained_variance[0]:.2f}%")
        X_train_famd_list.append(pca.transform(df_train).values.astype(np.float32))
        X_val_famd_list.append(pca.transform(df_val).values.astype(np.float32))
        X_test_famd_list.append(pca.transform(df_test).values.astype(np.float32))


X_train_famd = np.hstack(X_train_famd_list)
X_val_famd   = np.hstack(X_val_famd_list)
X_test_famd  = np.hstack(X_test_famd_list)

print(f"\nFinal concatenated FAMD Train shape: {X_train_famd.shape}")
print(f"Final concatenated FAMD Test shape : {X_test_famd.shape}")

# =============================================================
# 5. HUẤN LUYỆN & SO SÁNH CÁC MÔ HÌNH ML
# =============================================================
print("\n" + "=" * 60)
print("  TRAINING & COMPARING ML MODELS")
print("=" * 60)

models_to_compare = {
    "Random Forest": RandomForestClassifier(
        n_estimators=300, random_state=RANDOM_STATE, n_jobs=-1
    ),
    "Gradient Boosting": GradientBoostingClassifier(
        n_estimators=200, learning_rate=0.1, max_depth=5, random_state=RANDOM_STATE
    ),
    "XGBoost": xgb.XGBClassifier(
        n_estimators=200, learning_rate=0.1, max_depth=6,
        random_state=RANDOM_STATE, n_jobs=-1, eval_metric="mlogloss", verbosity=0
    ),
    "LightGBM": lgb.LGBMClassifier(
        n_estimators=200, learning_rate=0.1, max_depth=6,
        random_state=RANDOM_STATE, n_jobs=-1, verbose=-1
    )
}

comparison_results = []

for name, model in models_to_compare.items():
    model.fit(X_train_famd, y_train)
    
    y_val_pred  = model.predict(X_val_famd)
    y_test_pred = model.predict(X_test_famd)
    
    val_acc     = accuracy_score(y_val, y_val_pred)
    test_acc    = accuracy_score(y_test, y_test_pred)
    weighted_f1 = f1_score(y_test, y_test_pred, average="weighted", zero_division=0)
    macro_f1    = f1_score(y_test, y_test_pred, average="macro", zero_division=0)
    
    comparison_results.append({
        "model_name": name,
        "model_object": model,
        "predictions": y_test_pred,
        "val_accuracy": val_acc,
        "test_accuracy": test_acc,
        "weighted_f1": weighted_f1,
        "macro_f1": macro_f1
    })
    print(f"  Model: {name:<20} | Val Acc: {val_acc:.4f} | Test Acc: {test_acc:.4f} | Macro F1: {macro_f1:.4f}")

# =============================================================
# 6. EVALUATION & SELECTION
# =============================================================
print("\n" + "=" * 75)
print("  MODELS COMPARISON SUMMARY")
print("=" * 75)

comparison_df = pd.DataFrame(comparison_results)[[
    "model_name", "val_accuracy", "test_accuracy", "weighted_f1", "macro_f1"
]].sort_values("macro_f1", ascending=False)

print(comparison_df.to_string(index=False))

best_idx = next(i for i, r in enumerate(comparison_results) if r["model_name"] == comparison_df.iloc[0]["model_name"])
best_info = comparison_results[best_idx]
best_name = best_info["model_name"]

all_preds   = best_info["predictions"]
all_targets = y_test

print(f"\n=== Best Model: {best_name} ===")
print(f"   Validation Accuracy: {best_info['val_accuracy']:.4f}")
print(f"   Test Accuracy      : {best_info['test_accuracy']:.4f}")
print(f"   Weighted F1-Score  : {best_info['weighted_f1']:.4f}")
print(f"   Macro F1-Score     : {best_info['macro_f1']:.4f}")

print(f"\nDetailed Classification Report — {best_name}:")
print(classification_report(all_targets, all_preds, target_names=[str(c) for c in le_target.classes_]))


print("\nConfusion Matrix:")
print(confusion_matrix(all_targets, all_preds))

# =============================================================
# 7. SAVE ALL TRAINED FAMD PIPELINES INDIVIDUALLY
# =============================================================
print("\n" + "=" * 60)
print("  SAVING ALL TRAINED FAMD PIPELINES")
print("=" * 60)

import os

for r in comparison_results:
    m_name = r["model_name"]
    file_name = f"{m_name.lower().replace(' ', '_')}_famd_pipeline.pkl"
    file_path = os.path.join(MODEL_SAVE_DIR, file_name)
    
    pipeline_data = {
        "model_name": m_name,
        "famd_transformers": famd_transformers,  
        "model": r["model_object"],  
        "target_encoder": le_target,
        "core_features": CORE_FEATURES
    }
    
    joblib.dump(pipeline_data, file_path)
    print(f"Saved FAMD pipeline '{m_name}' to '{file_path}'")


