import json
import warnings
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import (
    ExtraTreesClassifier,
    GradientBoostingClassifier,
    HistGradientBoostingClassifier,
    RandomForestClassifier,
)
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression, RidgeClassifier
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
)
from sklearn.model_selection import StratifiedKFold, cross_val_predict, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder, OneHotEncoder, StandardScaler
from sklearn.feature_selection import mutual_info_classif

warnings.filterwarnings("ignore")

RANDOM_STATE = 42
np.random.seed(RANDOM_STATE)

DATA_PATH = "train/healthcare_5cores.json"

MODEL_SAVE_PATH = "final_5core_best_model.pkl"
MODEL_COMPARISON_PATH = "final_model_comparison.csv"
FEATURE_IMPORTANCE_PATH = "feature_importance_by_feature.csv"
CORE_IMPORTANCE_PATH = "feature_importance_by_core.csv"


# =============================================================
# 1. Helpers
# =============================================================

def safe_get(dct, *keys, default=np.nan):
    current = dct
    for key in keys:
        if not isinstance(current, dict):
            return default
        current = current.get(key, default)
    return current


def has_chronic(series):
    s = series.astype(str).str.lower().str.strip()
    return (
        series.notna()
        & ~s.isin(["nan", "none", "null", "", "no", "missing"])
    ).astype("int8")


def flatten_record(record):
    """
    Flatten one 5-core JSON record into a row.
    Prefixes preserve the source core of each feature.
    """
    cores = record.get("5_cores", record.get("5 cores", {}))

    return {
        "Level": record.get("Level"),

        # Core 1: ADLs & IADLs
        "ADL_Age": safe_get(cores, "ADLs & IADLs", "Age"),
        "ADL_PhysicalActivity": safe_get(cores, "ADLs & IADLs", "Physical Activity"),

        # Core 2: Cognitive & Neurological Status
        "Cog_SleepDuration": safe_get(cores, "Cognitive & Neurological Status", "Sleep Duration"),
        "Cog_StressLevel": safe_get(cores, "Cognitive & Neurological Status", "Stress Level"),

        # Core 3: Clinical Risk Assessments
        "Clinical_BMI": safe_get(cores, "Clinical Risk Assessments", "BMI"),
        "Clinical_ChronicDisease": safe_get(cores, "Clinical Risk Assessments", "Chronic Disease"),

        # Core 4: Mood & Behavioral Health
        "Mood_StressLevel": safe_get(cores, "Mood & Behavioral Health", "Stress Level"),
        "Mood_SmokingStatus": safe_get(cores, "Mood & Behavioral Health", "Smoking Status"),
        "Mood_AlcoholConsumption": safe_get(cores, "Mood & Behavioral Health", "Alcohol Consumption"),

        # Core 5: Financial & Legal
        "General_Age": safe_get(cores, "Financial & Legal", "Age"),
        "General_Gender": safe_get(cores, "Financial & Legal", "Gender"),
        "General_ChronicDisease": safe_get(cores, "Financial & Legal", "Chronic Disease"),
    }


def add_features(df):
    """
    Feature engineering using only fields from the 5 cores.
    """
    df = df.copy()

    numeric_cols = [
        "ADL_Age",
        "ADL_PhysicalActivity",
        "Cog_SleepDuration",
        "Cog_StressLevel",
        "Clinical_BMI",
        "Mood_StressLevel",
        "Mood_AlcoholConsumption",
        "General_Age",
    ]

    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Unified fields
    df["Age_Final"] = df["ADL_Age"].fillna(df["General_Age"])
    df["Stress_Final"] = df["Mood_StressLevel"].fillna(df["Cog_StressLevel"])
    df["Chronic_Final"] = df["Clinical_ChronicDisease"].fillna(df["General_ChronicDisease"])

    # Core 1: ADLs & IADLs
    df["LowActivity"] = (df["ADL_PhysicalActivity"] < 2.5).astype("int8")
    df["HighActivity"] = (df["ADL_PhysicalActivity"] > 7).astype("int8")
    df["ActivityBin"] = pd.cut(
        df["ADL_PhysicalActivity"],
        bins=[-1, 2.5, 5, 7, 99],
        labels=["Low", "Medium", "Good", "High"],
    )
    df["ADL_Age_x_Activity"] = df["ADL_Age"] * df["ADL_PhysicalActivity"]

    # Core 2: Cognitive & Neurological Status
    df["SleepDeprived"] = (df["Cog_SleepDuration"] < 7).astype("int8")
    df["ExcessiveSleep"] = (df["Cog_SleepDuration"] > 9).astype("int8")
    df["HighStress"] = (df["Stress_Final"] >= 7).astype("int8")
    df["ModerateStress"] = (
        (df["Stress_Final"] >= 4) & (df["Stress_Final"] < 7)
    ).astype("int8")
    df["StressBin"] = pd.cut(
        df["Stress_Final"],
        bins=[0, 3, 6, 10],
        labels=["Low", "Moderate", "High"],
    )
    df["Sleep_Stress_Ratio"] = df["Cog_SleepDuration"] / (df["Stress_Final"] + 1e-6)

    # Core 3: Clinical Risk Assessments
    df["BMI_Category"] = pd.cut(
        df["Clinical_BMI"],
        bins=[0, 18.5, 25, 30, 100],
        labels=["Underweight", "Normal", "Overweight", "Obese"],
    )
    df["IsObese"] = (df["Clinical_BMI"] >= 30).astype("int8")
    df["IsUnderweight"] = (df["Clinical_BMI"] < 18.5).astype("int8")
    df["HasChronicDisease"] = has_chronic(df["Chronic_Final"])

    # Core 4: Mood & Behavioral Health
    smoking_map = {
        "Never": 0,
        "Former": 1,
        "Current": 2,
        "No": 0,
        "Yes": 2,
        "None": 0,
    }
    df["SmokingRisk"] = df["Mood_SmokingStatus"].astype(str).map(smoking_map).fillna(1)
    df["AlcoholRisk"] = (df["Mood_AlcoholConsumption"] > 14).astype("int8")
    df["LifestyleRisk"] = df["SmokingRisk"] + df["AlcoholRisk"]
    df["MoodCompositeRisk"] = df["LifestyleRisk"] + df["HighStress"]

    # Core 5: Financial & Legal
    df["AgeBin"] = pd.cut(
        df["Age_Final"],
        bins=[0, 30, 45, 60, 75, 120],
        labels=["Young", "Adult", "MiddleAge", "Older", "Elderly"],
    )
    df["IsElderly"] = (df["Age_Final"] >= 65).astype("int8")
    df["IsSenior"] = (df["Age_Final"] >= 75).astype("int8")

    # Cross-core interaction features
    df["Age_x_BMI"] = df["Age_Final"] * df["Clinical_BMI"]
    df["Age_x_Stress"] = df["Age_Final"] * df["Stress_Final"]
    df["BMI_Activity_Ratio"] = df["Clinical_BMI"] / (df["ADL_PhysicalActivity"] + 1e-6)

    risk_cols = [
        "IsObese",
        "HighStress",
        "LowActivity",
        "SleepDeprived",
        "AlcoholRisk",
        "HasChronicDisease",
    ]
    df["CompositeRiskScore"] = df[risk_cols].sum(axis=1).astype("int8")

    return df


def build_preprocessor(X_data):
    numeric_features = X_data.select_dtypes(include=[np.number]).columns.tolist()
    categorical_features = X_data.select_dtypes(exclude=[np.number]).columns.tolist()

    numeric_transformer = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )

    categorical_transformer = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="constant", fill_value="Missing")),
            ("onehot", OneHotEncoder(handle_unknown="ignore")),
        ]
    )

    preprocessor = ColumnTransformer(
        [
            ("num", numeric_transformer, numeric_features),
            ("cat", categorical_transformer, categorical_features),
        ]
    )

    return preprocessor, numeric_features, categorical_features


def get_models():
    """
    Conservative settings reduce overfitting on small dataset.
    """
    models = {
        "Dummy Baseline": DummyClassifier(strategy="most_frequent"),

        "Logistic Regression": LogisticRegression(
            max_iter=4000,
            class_weight="balanced",
            C=0.5,
            random_state=RANDOM_STATE,
        ),

        "Ridge Classifier": RidgeClassifier(
            class_weight="balanced",
            alpha=2.0,
            random_state=RANDOM_STATE,
        ),

        "Random Forest Conservative": RandomForestClassifier(
            n_estimators=800,
            max_depth=4,
            min_samples_leaf=8,
            class_weight="balanced",
            random_state=RANDOM_STATE,
            n_jobs=-1,
        ),

        "Extra Trees Conservative": ExtraTreesClassifier(
            n_estimators=900,
            max_depth=4,
            min_samples_leaf=8,
            class_weight="balanced",
            random_state=RANDOM_STATE,
            n_jobs=-1,
        ),

        "Gradient Boosting Conservative": GradientBoostingClassifier(
            n_estimators=120,
            learning_rate=0.03,
            max_depth=1,
            min_samples_leaf=10,
            random_state=RANDOM_STATE,
        ),

        "Hist Gradient Boosting Conservative": HistGradientBoostingClassifier(
            max_iter=150,
            learning_rate=0.03,
            max_leaf_nodes=6,
            min_samples_leaf=15,
            l2_regularization=0.2,
            random_state=RANDOM_STATE,
        ),
    }

    try:
        import xgboost as xgb
        models["XGBoost Conservative"] = xgb.XGBClassifier(
            n_estimators=150,
            learning_rate=0.03,
            max_depth=1,
            min_child_weight=8,
            subsample=0.85,
            colsample_bytree=0.85,
            random_state=RANDOM_STATE,
            n_jobs=-1,
            eval_metric="mlogloss",
            verbosity=0,
        )
    except Exception as e:
        print("XGBoost skipped:", e)

    try:
        import lightgbm as lgb
        models["LightGBM Conservative"] = lgb.LGBMClassifier(
            n_estimators=150,
            learning_rate=0.03,
            max_depth=2,
            num_leaves=4,
            min_child_samples=25,
            class_weight="balanced",
            random_state=RANDOM_STATE,
            n_jobs=-1,
            verbose=-1,
        )
    except Exception as e:
        print("LightGBM skipped:", e)

    return models


def get_feature_names(preprocessor):
    try:
        return preprocessor.get_feature_names_out()
    except Exception:
        return np.array([])


def remove_onehot_suffix(clean_name):
    """
    Convert names like BMI_Category_Overweight back to BMI_Category
    for core mapping.
    """
    known_prefixes = [
        "BMI_Category",
        "ActivityBin",
        "StressBin",
        "AgeBin",
        "Clinical_ChronicDisease",
        "Mood_SmokingStatus",
        "General_Gender",
        "General_ChronicDisease",
        "Chronic_Final",
    ]

    for prefix in known_prefixes:
        if clean_name.startswith(prefix):
            return prefix

    return clean_name


def map_feature_to_core(feature_name):
    """
    Map transformed feature names back to 5 cores.
    """
    clean_name = feature_name
    if "__" in clean_name:
        clean_name = clean_name.split("__", 1)[1]

    base_name = remove_onehot_suffix(clean_name)

    # Cross-core first
    if base_name in [
        "Age_x_BMI",
        "Age_x_Stress",
        "BMI_Activity_Ratio",
        "CompositeRiskScore",
        "Age_Final",
        "Stress_Final",
        "Chronic_Final",
    ]:
        return "Cross-core / Derived"

    if (
        base_name.startswith("ADL_")
        or base_name in [
            "LowActivity",
            "HighActivity",
            "ActivityBin",
        ]
    ):
        return "ADLs & IADLs"

    if (
        base_name.startswith("Cog_")
        or base_name in [
            "SleepDeprived",
            "ExcessiveSleep",
            "HighStress",
            "ModerateStress",
            "StressBin",
            "Sleep_Stress_Ratio",
        ]
    ):
        return "Cognitive & Neurological Status"

    if (
        base_name.startswith("Clinical_")
        or base_name in [
            "BMI_Category",
            "IsObese",
            "IsUnderweight",
            "HasChronicDisease",
        ]
    ):
        return "Clinical Risk Assessments"

    if (
        base_name.startswith("Mood_")
        or base_name in [
            "SmokingRisk",
            "AlcoholRisk",
            "LifestyleRisk",
            "MoodCompositeRisk",
        ]
    ):
        return "Mood & Behavioral Health"

    if (
        base_name.startswith("General_")
        or base_name in [
            "AgeBin",
            "IsElderly",
            "IsSenior",
        ]
    ):
        return "Financial & Legal"

    return "Other"


def export_importance(best_pipeline):
    """
    Export feature-level and core-level importance if the selected model supports it.
    """
    model = best_pipeline.named_steps["model"]
    preprocessor = best_pipeline.named_steps["preprocess"]

    if not hasattr(model, "feature_importances_"):
        print("\nSelected model has no feature_importances_. Skipping importance export.")
        return None, None

    feature_names = get_feature_names(preprocessor)
    importances = model.feature_importances_

    if len(feature_names) != len(importances):
        print("\nFeature name count does not match importance count. Skipping importance export.")
        return None, None

    feature_df = pd.DataFrame(
        {
            "feature": feature_names,
            "importance": importances,
        }
    )
    feature_df["core"] = feature_df["feature"].apply(map_feature_to_core)
    feature_df = feature_df.sort_values(by="importance", ascending=False).reset_index(drop=True)

    core_df = (
        feature_df
        .groupby("core", as_index=False)["importance"]
        .sum()
        .sort_values(by="importance", ascending=False)
        .reset_index(drop=True)
    )
    core_df["importance_percent"] = core_df["importance"] / core_df["importance"].sum() * 100

    feature_df.to_csv(FEATURE_IMPORTANCE_PATH, index=False, encoding="utf-8-sig")
    core_df.to_csv(CORE_IMPORTANCE_PATH, index=False, encoding="utf-8-sig")

    return feature_df, core_df


# =============================================================
# 2. Load data
# =============================================================

print("=" * 100)
print("1. LOAD 5-CORE JSON DATA")
print("=" * 100)

data_path = Path(DATA_PATH)

if not data_path.exists():
    raise FileNotFoundError(
        f"Cannot find {DATA_PATH}. Please run this script from project root."
    )

with open(data_path, "r", encoding="utf-8") as f:
    raw_data = json.load(f)

print(f"Loaded: {DATA_PATH}")
print(f"Total records: {len(raw_data)}")


# =============================================================
# 3. Flatten + Feature Engineering
# =============================================================

print("\n" + "=" * 100)
print("2. FLATTEN 5 CORES AND CREATE FEATURES")
print("=" * 100)

df_raw = pd.DataFrame([flatten_record(record) for record in raw_data])
df_raw = df_raw.dropna(subset=["Level"]).reset_index(drop=True)
df_feat = add_features(df_raw)

print("Raw flattened shape:", df_raw.shape)
print("Feature-engineered shape:", df_feat.shape)

print("\nTarget distribution:")
print(df_feat["Level"].value_counts().sort_index())

target_encoder = LabelEncoder()
y = target_encoder.fit_transform(df_feat["Level"])
X = df_feat.drop(columns=["Level"])

# Same stable split as advanced version
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    stratify=y,
    random_state=RANDOM_STATE,
)

print("\nSplit:")
print(f"Train/CV samples: {len(y_train)}")
print(f"Final test samples: {len(y_test)}")


# =============================================================
# 4. Feature signal check
# =============================================================

print("\n" + "=" * 100)
print("3. FEATURE SIGNAL CHECK")
print("=" * 100)

X_mi = X.copy()
for col in X_mi.select_dtypes(exclude=[np.number]).columns:
    X_mi[col] = LabelEncoder().fit_transform(X_mi[col].astype(str).fillna("Missing"))

X_mi = X_mi.fillna(X_mi.median(numeric_only=True))
mi_scores = mutual_info_classif(X_mi, y, random_state=RANDOM_STATE)

mi_df = pd.DataFrame(
    {
        "feature": X_mi.columns,
        "mi_score": mi_scores,
    }
).sort_values(by="mi_score", ascending=False)

print("\nTop 20 features by Mutual Information:")
print(mi_df.head(20).to_string(index=False))


# =============================================================
# 5. Model search with CV
# =============================================================

print("\n" + "=" * 100)
print("4. CROSS-VALIDATION MODEL SEARCH")
print("=" * 100)

preprocessor, numeric_features, categorical_features = build_preprocessor(X_train)
models = get_models()
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)

rows = []
trained_pipelines = {}

for model_name, model in models.items():
    print(f"\nEvaluating: {model_name}")

    pipeline = Pipeline(
        [
            ("preprocess", preprocessor),
            ("model", model),
        ]
    )

    try:
        cv_pred = cross_val_predict(
            pipeline,
            X_train,
            y_train,
            cv=cv,
            n_jobs=None,
        )

        cv_accuracy = accuracy_score(y_train, cv_pred)
        cv_macro_f1 = f1_score(y_train, cv_pred, average="macro", zero_division=0)
        cv_balanced_accuracy = balanced_accuracy_score(y_train, cv_pred)

        pipeline.fit(X_train, y_train)
        test_pred = pipeline.predict(X_test)

        test_accuracy = accuracy_score(y_test, test_pred)
        test_macro_f1 = f1_score(y_test, test_pred, average="macro", zero_division=0)
        test_balanced_accuracy = balanced_accuracy_score(y_test, test_pred)

        rows.append(
            {
                "model": model_name,
                "cv_accuracy": cv_accuracy,
                "cv_macro_f1": cv_macro_f1,
                "cv_balanced_accuracy": cv_balanced_accuracy,
                "test_accuracy": test_accuracy,
                "test_macro_f1": test_macro_f1,
                "test_balanced_accuracy": test_balanced_accuracy,
            }
        )

        trained_pipelines[model_name] = pipeline

        print(f"  CV Macro F1: {cv_macro_f1:.4f} | Test Macro F1: {test_macro_f1:.4f}")

    except Exception as e:
        print(f"  Skipped due to error: {e}")

if not rows:
    raise RuntimeError("No model was successfully evaluated.")


# =============================================================
# 6. Select best model
# =============================================================

comparison_df = pd.DataFrame(rows).sort_values(
    by=["cv_macro_f1", "test_macro_f1"],
    ascending=False,
).reset_index(drop=True)

comparison_df.to_csv(MODEL_COMPARISON_PATH, index=False, encoding="utf-8-sig")

print("\n" + "=" * 100)
print("5. MODEL COMPARISON")
print("=" * 100)
print(comparison_df.to_string(index=False))

best_model_name = comparison_df.iloc[0]["model"]
best_pipeline = trained_pipelines[best_model_name]

final_pred = best_pipeline.predict(X_test)
target_names = [str(cls) for cls in target_encoder.classes_]

print("\n" + "=" * 100)
print(f"6. FINAL TEST REPORT — {best_model_name}")
print("=" * 100)
print("Accuracy:", accuracy_score(y_test, final_pred))
print("Balanced Accuracy:", balanced_accuracy_score(y_test, final_pred))
print("Macro F1:", f1_score(y_test, final_pred, average="macro", zero_division=0))

print("\nClassification Report:")
print(
    classification_report(
        y_test,
        final_pred,
        target_names=target_names,
        zero_division=0,
    )
)

print("Confusion Matrix:")
print(confusion_matrix(y_test, final_pred))


# =============================================================
# 7. Importance export
# =============================================================

print("\n" + "=" * 100)
print("7. FEATURE IMPORTANCE AND CORE-LEVEL EXPLAINABILITY")
print("=" * 100)

feature_importance_df, core_importance_df = export_importance(best_pipeline)

if feature_importance_df is not None:
    print("\nTop 20 features:")
    print(feature_importance_df.head(20).to_string(index=False))

if core_importance_df is not None:
    print("\nCore-level importance:")
    print(core_importance_df.to_string(index=False))


# =============================================================
# 8. Save everything
# =============================================================

joblib.dump(
    {
        "best_model_name": best_model_name,
        "pipeline": best_pipeline,
        "target_encoder": target_encoder,
        "model_comparison": comparison_df,
        "feature_importance": feature_importance_df,
        "core_importance": core_importance_df,
        "mutual_information": mi_df,
        "feature_columns": X.columns.tolist(),
        "numeric_features": numeric_features,
        "categorical_features": categorical_features,
        "data_path": DATA_PATH,
        "method": "5-Core Flattened Feature Modeling with Core-level Explainability",
    },
    MODEL_SAVE_PATH,
)

print("\n" + "=" * 100)
print("8. SAVE OUTPUTS")
print("=" * 100)
print(f"Saved model: {MODEL_SAVE_PATH}")
print(f"Saved model comparison: {MODEL_COMPARISON_PATH}")

if feature_importance_df is not None:
    print(f"Saved feature importance: {FEATURE_IMPORTANCE_PATH}")

if core_importance_df is not None:
    print(f"Saved core importance: {CORE_IMPORTANCE_PATH}")

print("\nDone.")