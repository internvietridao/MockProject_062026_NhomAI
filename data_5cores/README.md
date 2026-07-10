# Data - 5 Cores
Cấu trúc Thư mục (Directory Structure)

```text
data_5cores/
│
├── data/
│   ├── healthcare_real_time_dataset.csv  # Tập dữ liệu gốc (CSV)
│   ├── healthcare_5cores.json            # Dữ liệu cấu trúc 5 Cores
│   └── healthcare_flat.json              # Dữ liệu cấu trúc phẳng
│
├── normalization.py                      # Chuẩn hóa CSV sang JSON
├── analysis.py                           # Phân tích dữ liệu JSON
│
└── healthcare_analysis_report.md         # Báo cáo thống kê
```