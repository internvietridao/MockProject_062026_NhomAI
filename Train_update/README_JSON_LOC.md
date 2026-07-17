# Báo cáo mô tả bài toán: Phân loại mức độ chăm sóc trong viện dưỡng lão (LOC)

## 1. Tổng quan dự án

Dự án này xây dựng một pipeline Machine Learning demo để phân loại **Level of Care (LOC)** trong bối cảnh viện dưỡng lão. Mục tiêu của bài toán là dự đoán cư dân có nhu cầu chăm sóc ở mức:

- **Level 1**: Nhu cầu chăm sóc thấp
- **Level 2**: Nhu cầu chăm sóc trung bình
- **Level 3**: Nhu cầu chăm sóc cao



Vì dataset gốc không có nhãn LOC, nhóm tạo nhãn `LOC_Level` bằng phương pháp **synthetic rule-based labeling**, tức là tạo nhãn nhân tạo dựa trên điểm `care_score`.

---

## 2. Nguồn dữ liệu

Dataset gốc sử dụng trong dự án:

```text
heart_disease_health_indicators_BRFSS2015.csv
```

Dataset này chứa các biến sức khỏe, hành vi, nhân khẩu học và khả năng tiếp cận chăm sóc như:

- `Age`
- `BMI`
- `HighBP`
- `HighChol`
- `Diabetes`
- `Stroke`
- `HeartDiseaseorAttack`
- `GenHlth`
- `PhysHlth`
- `MentHlth`
- `DiffWalk`
- `PhysActivity`
- `Smoker`
- `HvyAlcoholConsump`
- `AnyHealthcare`
- `NoDocbcCost`
- `Education`
- `Income`

Sau khi xử lý, dữ liệu CSV được chuyển thành file JSON có cấu trúc 5 core:

```text
train/heart_disease_loc_5core.json
```

---

## 3. Lý do chuyển từ CSV sang JSON 5 core

Ban đầu dataset là dạng CSV phẳng. Tuy nhiên, bài toán của nhóm yêu cầu tổ chức dữ liệu theo 5 nhóm thông tin chăm sóc. Vì vậy, dữ liệu được chuyển sang cấu trúc JSON để thể hiện rõ từng core.

Cấu trúc JSON giúp:

- Giữ đúng yêu cầu 5 core của bài toán.
- Dễ giải thích feature thuộc nhóm chăm sóc nào.
- Dễ mở rộng nếu sau này có thêm dữ liệu MDS, ADL, Braden, Morse, medication hoặc nursing notes.
- Tách rõ dữ liệu đầu vào, điểm `care_score`, và nhãn `LOC_Level`.

Ví dụ cấu trúc một record:

```json
{
  "source_id": 0,
  "data_source": "Kaggle Heart Disease Health Indicators BRFSS2015",
  "label_type": "synthetic_rule_based_loc",
  "5_cores": {
    "ADLs_IADLs": {},
    "Cognitive_Neurological_Status": {},
    "Clinical_Risk_Assessments": {},
    "Mood_Behavioral_Health": {},
    "Financial_Legal_General_Status": {}
  },
  "care_score": 8,
  "LOC_Level": 2
}
```

---



---

## 4. Mapping dữ liệu sang 5 core

### Core 1: ADLs & IADLs

Core này mô phỏng khả năng sinh hoạt và vận động của cư dân.

Các biến sử dụng:

| Feature | Ý nghĩa |
|---|---|
| `Age` | Nhóm tuổi |
| `DiffWalk` | Có khó khăn khi đi lại hay không |
| `PhysActivity` | Có hoạt động thể chất hay không |
| `PhysHlth` | Số ngày sức khỏe thể chất không tốt |

Các biến này được dùng như proxy cho khả năng vận động, giới hạn chức năng và nhu cầu hỗ trợ sinh hoạt.

---

### Core 2: Cognitive & Neurological Status

Core này mô phỏng tình trạng thần kinh và tinh thần.

Các biến sử dụng:

| Feature | Ý nghĩa |
|---|---|
| `Stroke` | Tiền sử đột quỵ |
| `MentHlth` | Số ngày sức khỏe tinh thần không tốt |

Dataset không có các biến nhận thức trực tiếp như BIMS, CPS hoặc dementia, nên `Stroke` và `MentHlth` chỉ được xem là proxy.

---

### Core 3: Clinical Risk Assessments

Core này thể hiện rủi ro lâm sàng và bệnh nền.

Các biến sử dụng:

| Feature | Ý nghĩa |
|---|---|
| `HeartDiseaseorAttack` | Bệnh tim hoặc nhồi máu cơ tim |
| `HighBP` | Huyết áp cao |
| `HighChol` | Cholesterol cao |
| `CholCheck` | Có kiểm tra cholesterol |
| `Diabetes` | Tình trạng tiểu đường |
| `BMI` | Chỉ số khối cơ thể |
| `GenHlth` | Tự đánh giá sức khỏe tổng quát |
| `PhysHlth` | Số ngày sức khỏe thể chất không tốt |
| `AnyHealthcare` | Có khả năng tiếp cận chăm sóc y tế |

Đây là nhóm feature quan trọng nhất để mô phỏng nguy cơ sức khỏe và nhu cầu theo dõi.

---

### Core 4: Mood & Behavioral Health

Core này mô phỏng sức khỏe tinh thần và hành vi/lối sống.

Các biến sử dụng:

| Feature | Ý nghĩa |
|---|---|
| `MentHlth` | Số ngày sức khỏe tinh thần không tốt |
| `Smoker` | Có hút thuốc hay không |
| `HvyAlcoholConsump` | Tiêu thụ rượu nặng |
| `Fruits` | Có ăn trái cây |
| `Veggies` | Có ăn rau |

Các biến này không đại diện hoàn toàn cho hành vi trong nursing home, nhưng có thể dùng làm proxy cho mood và behavioral/lifestyle risk.

---

### Core 5: Financial / Legal / General Status

Core này mô phỏng thông tin nhân khẩu học, xã hội và khả năng tiếp cận chăm sóc.

Các biến sử dụng:

| Feature | Ý nghĩa |
|---|---|
| `Age` | Nhóm tuổi |
| `Sex` | Giới tính |
| `Education` | Trình độ học vấn |
| `Income` | Thu nhập |
| `NoDocbcCost` | Không đi khám vì chi phí |
| `AnyHealthcare` | Có tiếp cận chăm sóc y tế |

Nhóm này không trực tiếp xác định LOC nhưng giúp mô tả hoàn cảnh tổng quát của người được khảo sát.

---

## 5. Tạo nhãn synthetic LOC bằng care_score

Vì dataset gốc không có nhãn LOC thật, dự án tạo `care_score` dựa trên các biến proxy. Điểm càng cao thì nhu cầu chăm sóc giả định càng cao.

### Quy tắc tính điểm

| Điều kiện | Điểm |
|---|---:|
| `Age >= 10` | +2 |
| `Age >= 8` | +1 |
| `DiffWalk = 1` | +3 |
| `PhysActivity = 0` | +1 |
| `GenHlth >= 4` | +3 |
| `GenHlth == 3` | +1 |
| `PhysHlth >= 15` | +2 |
| `PhysHlth >= 7` | +1 |
| `MentHlth >= 15` | +1 |
| `HighBP = 1` | +1 |
| `HighChol = 1` | +1 |
| `Diabetes > 0` | +2 |
| `Stroke = 1` | +2 |
| `HeartDiseaseorAttack = 1` | +2 |
| `BMI >= 35` | +1 |
| `BMI < 18.5` | +1 |
| `Smoker = 1` | +1 |
| `HvyAlcoholConsump = 1` | +1 |
| `NoDocbcCost = 1` | +1 |

### Chuyển care_score thành LOC_Level

| LOC_Level | Điều kiện |
|---|---|
| Level 1 | `care_score <= 3` |
| Level 2 | `4 <= care_score <= 8` |
| Level 3 | `care_score > 8` |

`care_score` được lưu trong JSON để giải thích và kiểm tra logic nhãn, nhưng **không được dùng làm feature đầu vào khi train model**.

---

## 6. Lọc dữ liệu theo bối cảnh nursing-home-like

Dataset gốc có 253,680 dòng. Sau khi áp dụng strict filter để chọn nhóm gần với bối cảnh người cao tuổi/có rủi ro chăm sóc, dữ liệu còn lại:

```text
44,840 records
```

Điều kiện lọc chính:

- Tuổi từ nhóm `Age >= 9`
- Có ít nhất một dấu hiệu về functional risk hoặc clinical risk

Sau khi lọc, phân phối nhãn là:

Phân phối nhãn sau cân bằng:

| Level | Số lượng |
|---|---:|
| Level 1 | 459 |
| Level 2 | 5,000 |
| Level 3 | 5,000 

Phân phối này bị lệch về Level 3, vì bộ lọc ưu tiên các trường hợp có rủi ro cao hơn.

---

## 8. Pipeline huấn luyện mô hình

Pipeline train model gồm các bước:

1. Load file JSON 5 core.
2. Flatten dữ liệu JSON thành dạng bảng.
3. Tách `LOC_Level` làm target.
4. Loại bỏ `care_score` khỏi input để tránh leakage trực tiếp.
5. Tạo thêm một số engineered features.
6. Chia train/test theo tỷ lệ 80/20.
7. Train nhiều mô hình.
8. So sánh theo Accuracy, Balanced Accuracy và Macro F1.
9. Chọn model tốt nhất theo Macro F1.
10. Lưu model tốt nhất vào thư mục `models`.

File train chính:

```text
train_model_json_loc.py
```

Model được lưu tại:

```text
models/loc_json_best_model.pkl
```

---

## 9. Kết quả thực nghiệm

Sau khi train, kết quả thu được:

| Model | Accuracy | Balanced Accuracy | Macro F1 |
|---|---:|---:|---:|
| Logistic Regression | 0.9707 | 0.9763 | 0.9083 |
| Random Forest | 0.9494 | 0.9613 | 0.9007 |

Model tốt nhất:

```text
Logistic Regression
```

Kết quả test của Logistic Regression:

| Metric | Giá trị |
|---|---:|
| Accuracy | 0.9707 |
| Balanced Accuracy | 0.9763 |
| Macro F1 | 0.9083 |

Classification report:

| Level | Precision | Recall | F1-score | Support |
|---|---:|---:|---:|---:|
| Level 1 | 0.6500 | 0.9891 | 0.7845 | 92 |
| Level 2 | 0.9518 | 0.9674 | 0.9595 | 3,224 |
| Level 3 | 0.9899 | 0.9722 | 0.9810 | 5,652 |

Confusion Matrix:

```text
[[  91    1    0]
 [  49 3119   56]
 [   0  157 5495]]
```

---

## 10. Cách diễn giải kết quả

Kết quả model khá cao, đặc biệt Logistic Regression đạt Macro F1 = 0.9083. Tuy nhiên, cần diễn giải cẩn thận.

Vì `LOC_Level` là nhãn synthetic được tạo từ chính các biến proxy trong dataset, model có thể học lại pattern của rule labeling. Do đó:

- Kết quả cao chứng minh pipeline hoạt động tốt.
- Kết quả cao cho thấy model học tốt quy luật nhãn nhân tạo.
- Kết quả này **không chứng minh model dự đoán LOC lâm sàng thật tốt**.
- Đây là demo học thuật, không phải hệ thống quyết định chăm sóc y tế.

---





```

Thứ tự chạy :

1. Chạy `convert_csv_to_5core_json.py` để tạo JSON.
2. Chạy `train_model_json_loc.py` để train model.

---
