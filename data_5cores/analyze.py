import json
import os
import pandas as pd

json_file_path = "./data/healthcare_cores.json"

if not os.path.exists(json_file_path):
    print(
        f"Lỗi: Không tìm thấy file '{json_file_path}'. Hãy chạy file chuyển đổi trước!"
    )
    exit()

with open(json_file_path, "r", encoding="utf-8") as f:
    data = json.load(f)

flattened_data = []
for item in data:
    cores = item.get("5 cores", {})
    row = {
        "Level": item.get("Level"),
        "Age": cores.get("ADLs & IADLs", {}).get("Age"),
        "Physical_Activity": cores.get("ADLs & IADLs", {}).get(
            "Physical Activity"
        ),
        "Sleep_Duration": cores.get("Cognitive & Neurological Status", {}).get(
            "Sleep Duration"
        ),
        "Stress_Level": cores.get("Cognitive & Neurological Status", {}).get(
            "Stress Level"
        ),
        "BMI": cores.get("Clinical Risk Assessments", {}).get("BMI"),
        "Chronic_Disease": cores.get("Clinical Risk Assessments", {}).get(
            "Chronic Disease"
        ),
        "Alcohol_Consumption": cores.get("Mood & Behavioral Health", {}).get(
            "Alcohol Consumption"
        ),
    }
    flattened_data.append(row)

df = pd.DataFrame(flattened_data)

total_records = len(df) 
level_counts = df["Level"].value_counts().sort_index()

numeric_cols = [
    "Age",
    "BMI",
    "Physical_Activity",
    "Sleep_Duration",
    "Stress_Level",
    "Alcohol_Consumption",
]
grouped_means = df.groupby("Level")[numeric_cols].mean()

high_risk_disease = (
    df[df["Level"] == 3]["Chronic_Disease"].value_counts(normalize=True) * 100
)

md_content = f"""# Báo cáo Phân tích & Thống kê Dữ liệu Chăm sóc Sức khỏe

## 1. Phân bổ số lượng mẫu theo từng Mức độ Rủi ro (Level)
- **Tổng số dữ liệu mẫu**: {total_records} mẫu
- **Level 1 (Thấp)**: {level_counts.get(1, 0)} mẫu
- **Level 2 (Trung bình)**: {level_counts.get(2, 0)} mẫu
- **Level 3 (Cao)**: {level_counts.get(3, 0)} mẫu

## 2. Các chỉ số sức khỏe trung bình theo từng Nhóm Nguy cơ

| Level | Tuổi (Age) | Chỉ số BMI | Giờ tập thể dục/tuần | Giờ ngủ/ngày | Mức độ Stress | Đơn vị cồn/tuần |
| :---: | :--------: | :--------: | :------------------: | :----------: | :-----------: | :-------------: |
| **1** | {grouped_means.loc[1, 'Age']:.2f} | {grouped_means.loc[1, 'BMI']:.2f} | {grouped_means.loc[1, 'Physical_Activity']:.2f} | {grouped_means.loc[1, 'Sleep_Duration']:.2f} | {grouped_means.loc[1, 'Stress_Level']:.2f} | {grouped_means.loc[1, 'Alcohol_Consumption']:.2f} |
| **2** | {grouped_means.loc[2, 'Age']:.2f} | {grouped_means.loc[2, 'BMI']:.2f} | {grouped_means.loc[2, 'Physical_Activity']:.2f} | {grouped_means.loc[2, 'Sleep_Duration']:.2f} | {grouped_means.loc[2, 'Stress_Level']:.2f} | {grouped_means.loc[2, 'Alcohol_Consumption']:.2f} |
| **3** | {grouped_means.loc[3, 'Age']:.2f} | {grouped_means.loc[3, 'BMI']:.2f} | {grouped_means.loc[3, 'Physical_Activity']:.2f} | {grouped_means.loc[3, 'Sleep_Duration']:.2f} | {grouped_means.loc[3, 'Stress_Level']:.2f} | {grouped_means.loc[3, 'Alcohol_Consumption']:.2f} |

## 3. Thống kê tỷ lệ Tiền sử Bệnh lý ở Nhóm Nguy cơ Cao (Level 3)
"""

for disease, percentage in high_risk_disease.items():
    md_content += f"- **Bệnh {disease}**: {percentage:.1f}%\n"

with open("healthcare_analysis_report.md", "w", encoding="utf-8") as f:
    f.write(md_content)

print(
    "Đã phân tích lại và xuất thành công file báo cáo mới tại 'healthcare_analysis_report.md'!"
)