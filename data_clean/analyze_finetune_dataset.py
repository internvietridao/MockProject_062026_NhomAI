import os
import json
from collections import Counter

def analyze_dataset_by_source(json_file_path, output_md_path="report_source.md"):
    if not os.path.exists(json_file_path):
        print(f"Không tìm thấy file JSON tổng hợp tại: {os.path.abspath(json_file_path)}")
        return

    print(f"Đang đọc dữ liệu từ file: {os.path.basename(json_file_path)}...")
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            dataset = json.load(f)
    except json.JSONDecodeError:
        print("Lỗi: File JSON bị sai cấu trúc cú pháp.")
        return
    except Exception as e:
        print(f"Lỗi hệ thống khi mở file: {str(e)}")
        return

    total_questions = len(dataset)
    
    source_counts = Counter()
    missing_source_count = 0

    for item in dataset:
        source = item.get('source')
        if source:
            source_counts[source] += 1
        else:
            missing_source_count += 1

    print(f"Đang tiến hành xuất bảng thống kê ra file: {output_md_path}...")
    
    with open(output_md_path, 'w', encoding='utf-8') as md:
        md.write("### BẢNG THỐNG KÊ SỐ LƯỢNG CÂU HỎI THEO LỚP (SOURCE)\n\n")
        md.write(f"- **Tổng số lượng bộ câu hỏi trong file:** {total_questions:,}\n\n")
        md.write("| Tên Nguồn Dữ Liệu (Source) | Số Lượng (QA) | Tỷ Lệ (%) |\n")
        md.write("| :--- | :---: | :---: |\n")
        
        for source, count in source_counts.most_common():
            percentage = (count / total_questions) * 100
            md.write(f"| {source} | {count:,} | {percentage:.2f}% |\n")

        if missing_source_count > 0:
            missing_percentage = (missing_source_count / total_questions) * 100
            md.write(f"| **THIẾU TRƯỜNG SOURCE** | {missing_source_count:,} | {missing_percentage:.2f}% |\n")
            
    print(" Thao tác hoàn tất! Bạn có thể mở file .md để xem kết quả.")

if __name__ == "__main__":
    FINAL_JSON_PATH = "./data_clean/fine_tune/final_train_dataset.json"
    
    analyze_dataset_by_source(FINAL_JSON_PATH, output_md_path="STATISTICS.md")
