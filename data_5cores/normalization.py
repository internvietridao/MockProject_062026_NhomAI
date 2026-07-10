import json
import math
import pandas as pd

df = pd.read_csv("./data/healthcare_real_time_dataset.csv")

def clean_val(val):
    if pd.isna(val) or (isinstance(val, float) and math.isnan(val)):
        return None
    return val

level_map = {"High": 3, "Moderate": 2, "Low": 1}
json_5cores_output = []
json_flat_output = []

for _, row in df.iterrows():
    raw_age = row.get("Age")
    if pd.isna(raw_age) or raw_age < 50:
        continue  

    age = clean_val(raw_age)
    gender = clean_val(row.get("Gender"))
    bmi = clean_val(row.get("BMI"))
    smoking = clean_val(row.get("Smoking Status"))
    alcohol = clean_val(row.get("Alcohol Consumption (per week)"))
    activity = clean_val(row.get("Physical Activity (hours/week)"))
    sleep = clean_val(row.get("Sleep Duration (hours/day)"))
    disease = clean_val(row.get("Chronic Disease History"))

    raw_level = clean_val(row.get("Health Risk Level"))
    mapped_level = level_map.get(raw_level, None) if raw_level else None

    # --- ĐỊNH DẠNG 1: CẤU TRÚC 5 CORES ---
    item_5cores = {
        "5 cores": {
            "ADLs & IADLs": {"Physical Activity": activity, "Age": age},
            "Cognitive & Neurological Status": {
                "Sleep Duration": sleep,
                "Stress Level": clean_val(row.get("Stress Level (1-10)")),
            },
            "Clinical Risk Assessments": {"BMI": bmi, "Chronic Disease": disease},
            "Mood & Behavioral Health": {
                "Stress Level": clean_val(row.get("Stress Level (1-10)")),
                "Smoking Status": smoking,
                "Alcohol Consumption": alcohol,
            },
            "Financial & Legal": {
                "Age": age,
                "Gender": gender,
                "Chronic Disease": disease,
            },
        },
        "Level": mapped_level,
    }
    json_5cores_output.append(item_5cores)

    # --- ĐỊNH DẠNG 2: CẤU TRÚC PHẲNG ---
    item_flat = {
        "Data": {  
            "Physical Activity": activity,
            "Age": age,
            "Sleep Duration": sleep,
            "Stress Level": clean_val(row.get("Stress Level (1-10)")),
            "BMI": bmi,
            "Chronic Disease": disease,
            "Smoking Status": smoking,
            "Alcohol Consumption": alcohol,
            "Gender": gender,
        },
        "Level": mapped_level,
    }
    json_flat_output.append(item_flat)

with open("./data/healthcare_5cores.json", "w", encoding="utf-8") as f:
    json.dump(json_5cores_output, f, ensure_ascii=False, indent=4)

with open("./data/healthcare_flat.json", "w", encoding="utf-8") as f:
    json.dump(json_flat_output, f, ensure_ascii=False, indent=4)

print("=" * 60)
print(f"Đã lọc thành công {len(json_flat_output)}")
print("- File cấu trúc 5 Cores: './data/healthcare_5cores.json'")
print("- File cấu trúc Phẳng: './data/healthcare_flat.json'")
print("=" * 60)