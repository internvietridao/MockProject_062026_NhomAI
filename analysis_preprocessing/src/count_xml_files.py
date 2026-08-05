import os

def count_xml_in_folders(repo_path):
    if not os.path.exists(repo_path):
        print(f"Đường dẫn không tồn tại: {os.path.abspath(repo_path)}")
        return

    print(f"ĐANG THỐNG KÊ SỐ LƯỢNG FILE XML TRONG REPO: {repo_path}\n")
    print(f"{'Tên thư mục con':<50} | {'Số lượng file XML':<20}")
    print("-" * 75)

    total_xml_files = 0
    
    try:
        subitems = sorted(os.listdir(repo_path))
    except Exception as e:
        print(f"Không thể đọc thư mục: {str(e)}")
        return

    for item in subitems:
        item_path = os.path.join(repo_path, item)
        
        if os.path.isdir(item_path):
            xml_count = len([f for f in os.listdir(item_path) if f.endswith('.xml') and os.path.isfile(os.path.join(item_path, f))])
            print(f"{item:<50} | {xml_count:<20,}")
            total_xml_files += xml_count

    print("-" * 75)
    print(f"{'TỔNG CỘNG TẤT CẢ THƯ MỤC:':<50} | {total_xml_files:<20,}\n")

if __name__ == "__main__":
    REPO_DIRECTORY = "./data_raw/MedQuAD" 
    
    count_xml_in_folders(REPO_DIRECTORY)