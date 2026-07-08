import os
import json

def merge_all_json_files(data_dir, output_file_path):
    combined_dataset = []
    
    if not os.path.exists(data_dir):
        print(f"Không tìm thấy thư mục dữ liệu đầu vào: {os.path.abspath(data_dir)}")
        return

    print(f"Bắt đầu quét và gộp các file JSON từ: {os.path.abspath(data_dir)}")
    print("-" * 60)

    for root, dirs, files in os.walk(data_dir):
        for file in files:
            if file.endswith('.json'):
                file_path = os.path.join(root, file)
                    
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            combined_dataset.extend(data)
                        elif isinstance(data, dict):
                            combined_dataset.append(data)
                            
                except json.JSONDecodeError:
                    print(f"Lỗi cấu trúc JSON tại file: {file_path}")
                except Exception as e:
                    print(f"Lỗi khi đọc file {file_path}: {str(e)}")

    output_dir = os.path.dirname(output_file_path)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    with open(output_file_path, 'w', encoding='utf-8') as f:
        json.dump(combined_dataset, f, ensure_ascii=False, indent=4)
        
    print("-" * 60)
    print(f" File JSON tổng đã được lưu tại: {os.path.abspath(output_file_path)}")

if __name__ == "__main__":
    INPUT_DATA_DIRECTORY = "./analysis_preprocessing/data"
    OUTPUT_FINAL_FILE = "./data_clean/fine_tune/final_train_dataset.json"
    
    merge_all_json_files(INPUT_DATA_DIRECTORY, OUTPUT_FINAL_FILE)