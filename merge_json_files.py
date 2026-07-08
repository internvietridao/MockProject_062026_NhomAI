import json
import os

def merge_json_files(folder_path, output_file):
    """Gộp tất cả các file JSON trong folder thành một file"""
    all_data = []
    
    # Lấy danh sách file JSON và sắp xếp theo tên
    json_files = sorted([f for f in os.listdir(folder_path) if f.endswith('.json')])
    
    for filename in json_files:
        file_path = os.path.join(folder_path, filename)
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            all_data.extend(data)
    
    # Ghi dữ liệu đã gộp vào file output
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)
    
    print(f"Đã gộp {len(json_files)} files từ {folder_path} vào {output_file}")
    print(f"Tổng số câu hỏi: {len(all_data)}")
    return len(all_data)

# Gộp 3 folder
folders = [
    ('7_SeniorHealth_QA_json', '7_SeniorHealth_QA_merged.json'),
    ('8_NHLBI_QA_XML_json', '8_NHLBI_QA_XML_merged.json'),
    ('9_CDC_QA_json', '9_CDC_QA_merged.json')
]

total_questions = 0
for folder, output in folders:
    count = merge_json_files(folder, output)
    total_questions += count

print(f"\nTổng số câu hỏi sau khi gộp: {total_questions}")
