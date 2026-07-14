import os
import json
from sentence_transformers import SentenceTransformer
from typing import List, Dict
import re

def split_into_chunks(text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> List[str]:
    """Chia văn bản thành các chunks với overlap"""
    chunks = []
    start = 0
    text_length = len(text)
    
    while start < text_length:
        end = start + chunk_size
        
        if end < text_length:
            for separator in ['\n\n', '\n', '. ', '! ', '? ', '; ']:
                last_sep = text.rfind(separator, start, end)
                if last_sep != -1:
                    end = last_sep + len(separator)
                    break
        
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        
        start = end - chunk_overlap
        
        if len(chunks) > 0 and start <= 0:
            start = end
    
    return chunks

def split_markdown_by_structure(text: str) -> List[str]:
    """Chia markdown theo cấu trúc (headers, paragraphs)"""
    chunks = []
    lines = text.split('\n')
    current_chunk = []
    
    for line in lines:
        if line.startswith('#'):
            if current_chunk:
                chunk_text = '\n'.join(current_chunk).strip()
                if chunk_text:
                    chunks.append(chunk_text)
                current_chunk = []
            current_chunk.append(line)
        else:
            current_chunk.append(line)
    
    if current_chunk:
        chunk_text = '\n'.join(current_chunk).strip()
        if chunk_text:
            chunks.append(chunk_text)
    
    final_chunks = []
    for chunk in chunks:
        if len(chunk) > 3000:
            sub_chunks = split_into_chunks(chunk, chunk_size=2500, chunk_overlap=300)
            final_chunks.extend(sub_chunks)
        else:
            final_chunks.append(chunk)
    
    return final_chunks

def process_single_file(file_path: str, filename: str, output_file: str, model_name: str = 'all-MiniLM-L6-v2', batch_size: int = 8):
    """Xử lý một file duy nhất với batch size nhỏ"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    chunks = split_markdown_by_structure(content)
    
    chunk_data = []
    for idx, chunk in enumerate(chunks):
        chunk_data.append({
            'filename': filename,
            'chunk_id': idx,
            'content': chunk,
            'file_path': file_path,
            'chunk_length': len(chunk)
        })
    
    print(f"Đã chia {filename} thành {len(chunks)} chunks")
    
    print(f"Đang tạo embeddings cho {len(chunks)} chunks (batch_size={batch_size})...")
    model = SentenceTransformer(model_name)
    
    for i in range(0, len(chunk_data), batch_size):
        batch_chunks = chunk_data[i:i + batch_size]
        batch_texts = [chunk['content'] for chunk in batch_chunks]
        
        batch_embeddings = model.encode(batch_texts, show_progress_bar=False, batch_size=len(batch_texts))
        
        for j, chunk in enumerate(batch_chunks):
            chunk['embedding'] = batch_embeddings[j].tolist()
        
        print(f"Đã xử lý {min(i + batch_size, len(chunk_data))}/{len(chunk_data)} chunks")
        
        import gc
        gc.collect()
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(chunk_data, f, ensure_ascii=False, indent=2)
    
    print(f"Đã lưu embeddings vào: {output_file}")
    return chunk_data

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python3 embed_rag_chunks.py <filename>")
        sys.exit(1)
    
    filename = sys.argv[1]
    rag_folder = 'data_clean/RAG'
    output_folder = 'data_clean/chunk_embeddings'
    
    os.makedirs(output_folder, exist_ok=True)
    
    file_path = os.path.join(rag_folder, filename)
    output_file = os.path.join(output_folder, f"{filename}_embeddings.json")
    
    print(f"Đang xử lý: {filename}")
    process_single_file(file_path, filename, output_file, batch_size=8)
    print("Hoàn thành!")
