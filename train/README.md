## 5-Core Care Level Classification Model

### 1. Dataset

The model uses the `healthcare_5cores.json` dataset, which contains 511 records.  
Each record is structured into 5 care-related cores:

1. ADLs & IADLs  
2. Cognitive & Neurological Status  
3. Clinical Risk Assessments  
4. Mood & Behavioral Health  
5. Financial & Legal  

The target variable is `Level`, which has 3 classes:

| Level | Number of Records |
|---|---:|
| 1 | 201 |
| 2 | 151 |
| 3 | 159 |

After flattening the 5-core JSON structure and applying feature engineering, the dataset contains 41 features.

---

### 2. Methodology

The original 5-core structure is flattened into tabular features for model training.  
Feature engineering is applied to create additional risk indicators and cross-core interaction features, such as:

- `Age_x_Stress`
- `Age_x_BMI`
- `Sleep_Stress_Ratio`
- `BMI_Activity_Ratio`
- `CompositeRiskScore`
- `LowActivity`
- `HighStress`
- `HasChronicDisease`

Several classification models were trained and compared using 5-fold stratified cross-validation.

---

### 3. Models Compared

The following models were evaluated:

| Model | CV Macro F1 | Test Macro F1 |
|---|---:|---:|
| Random Forest Conservative | 0.3476 | 0.4043 |
| Extra Trees Conservative | 0.3322 | 0.3989 |
| Ridge Classifier | 0.3159 | 0.3048 |
| Logistic Regression | 0.3145 | 0.3235 |
| LightGBM Conservative | 0.3041 | 0.3357 |
| XGBoost Conservative | 0.2968 | 0.3594 |
| Hist Gradient Boosting Conservative | 0.2908 | 0.3551 |
| Gradient Boosting Conservative | 0.2855 | 0.3469 |
| Dummy Baseline | 0.1878 | 0.1898 |

The best model selected was:

```text
Random Forest Conservative