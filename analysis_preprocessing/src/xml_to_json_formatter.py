import os
import xml.etree.ElementTree as ET
import json
import re

def clean_text(text):
    if text is None:
        return ""
    text = re.sub(re.compile(r'\s+'), ' ', text)
    return text.strip()

def parse_selective_medquad(base_path, target_folders, output_json_path):
    dataset = []
    
    print(f"Bắt đầu quét dữ liệu tại: {base_path}")
    
    for folder_name in target_folders:
        folder_path = os.path.join(base_path, folder_name)
        
        if not os.path.exists(folder_path):
            print(f"Cảnh báo: Thư mục {folder_name} không tồn tại tại đường dẫn chỉ định. Bỏ qua.")
            continue
            
        print(f"Đang xử lý thư mục: {folder_name}")
        
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                if file.endswith('.xml'):
                    file_path = os.path.join(root, file)
                    folder_source = f"{os.path.basename(base_path)}/{folder_name}".replace("\\", "/")
                    try:
                        tree = ET.parse(file_path)
                        xml_root = tree.getroot()
                        qa_pairs = xml_root.findall('.//QAPair')
                        
                        for qa in qa_pairs:
                            question_elem = qa.find('Question')
                            answer_elem = qa.find('Answer')
                            
                            if question_elem is not None and answer_elem is not None:
                                question_text = clean_text(question_elem.text)
                                answer_text = clean_text(answer_elem.text)
                                
                                data_entry = {
                                    "question": question_text,
                                    "answer": answer_text,
                                    "source": folder_source
                                }
                                dataset.append(data_entry)
                                
                    except ET.ParseError:
                        print(f"Lỗi cú pháp XML tại file: {file_path}")
                    except Exception as e:
                        print(f"Lỗi hệ thống khi xử lý file {file_path}: {str(e)}")

    with open(output_json_path, 'w', encoding='utf-8') as f:
        json.dump(dataset, f, ensure_ascii=False, indent=4)
        
    print(f"\n Hoàn thành! Đã lọc và chuyển đổi thành công {len(dataset)} cặp câu hỏi-đáp.")
    print(f" Ghi file JSON bốc dữ liệu sạch tại: {output_json_path}")

if __name__ == "__main__":
    BASE_DIRECTORY = "./data_raw/MedQuAD" 
    
    TARGET_FOLDERS = [
        "4_MPlus_Health_Topics_QA",
        "5_NIDDK_QA",
        "6_NINDS_QA"
    ]
    
    OUTPUT_FILE = "./analysis_preprocessing/data/medquad_data_train.json"
    
    selective_dataset = parse_selective_medquad(BASE_DIRECTORY, TARGET_FOLDERS, OUTPUT_FILE)