import os
import json
from sentence_transformers import SentenceTransformer
from typing import List, Dict
import numpy as np

def load_markdown_files(folder_path: str) -> List[Dict]:
    """Đọc tất cả các file markdown trong folder"""
    documents = []
    
    for filename in sorted(os.listdir(folder_path)):
        if filename.endswith('.md'):
            file_path = os.path.join(folder_path, filename)
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            documents.append({
                'filename': filename,
                'content': content,
                'file_path': file_path
            })
            print(f"Đã đọc: {filename} ({len(content)} ký tự)")
    
    return documents

def create_embeddings(documents: List[Dict], model_name: str = 'all-MiniLM-L6-v2') -> Dict:
    """Tạo embeddings cho các tài liệu"""
    print(f"\nĐang tải model: {model_name}")
    model = SentenceTransformer(model_name)
    
    embeddings = {}
    
    for doc in documents:
        # Tạo embedding cho toàn bộ nội dung
        embedding = model.encode(doc['content'], show_progress_bar=True)
        
        embeddings[doc['filename']] = {
            'embedding': embedding.tolist(),
            'filename': doc['filename'],
            'file_path': doc['file_path'],
            'content_length': len(doc['content'])
        }
        print(f"Đã tạo embedding cho: {doc['filename']}")
    
    return embeddings

def save_embeddings(embeddings: Dict, output_file: str):
    """Lưu embeddings vào file JSON"""
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(embeddings, f, ensure_ascii=False, indent=2)
    
    print(f"\nĐã lưu embeddings vào: {output_file}")
    print(f"Tổng số tài liệu: {len(embeddings)}")

def main():
    # Đường dẫn
    rag_folder = 'data_clean/RAG'
    output_file = 'data_clean/RAG_embeddings.json'
    
    # Đọc các file markdown
    print("Đang đọc các file markdown...")
    documents = load_markdown_files(rag_folder)
    
    if not documents:
        print("Không tìm thấy file markdown nào!")
        return
    
    # Tạo embeddings
    print(f"\nĐang tạo embeddings cho {len(documents)} tài liệu...")
    embeddings = create_embeddings(documents)
    
    # Lưu embeddings
    save_embeddings(embeddings, output_file)
    
    print("\nHoàn thành!")

if __name__ == '__main__':
    main()
