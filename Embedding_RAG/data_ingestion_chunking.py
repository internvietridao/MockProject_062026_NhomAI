import os
import json
import re
import logging
from pathlib import Path
from typing import List, Dict

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

# 1. CONFIGURATION
DATA_DIR = str(Path(__file__).parent.parent / "data_clean" / "RAG")
OUTPUT_DIR = str(Path(__file__).parent / "chunks")
OUTPUT_FILE_NAME = "all_chunks.json"
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50

# 2. DATA INGESTION
def scan_and_read_md_files(data_dir: str) -> List[Dict]:
    md_files = []
    data_path = Path(data_dir)
    
    if not data_path.exists():
        logging.error(f"Data directory '{data_dir}' does not exist.")
        raise FileNotFoundError(f"Directory not found: {data_dir}")
        
    logging.info(f"Scanning directory for Markdown files: {data_path.resolve()}")
    
    for filepath in data_path.rglob("*.md"):
        if filepath.is_file():
            try:
                content = ""
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                except UnicodeDecodeError:
                    logging.warning(f"UTF-8 decoding failed for {filepath}. Trying 'windows-1252'.")
                    with open(filepath, 'r', encoding='windows-1252') as f:
                        content = f.read()
                
                category = filepath.parent.name
                
                try:
                    relative_path = str(filepath.relative_to(data_path))
                except ValueError:
                    relative_path = str(filepath)
                
                md_files.append({
                    "file_name": filepath.name,
                    "file_path": relative_path,
                    "category": category,
                    "content": content
                })
                logging.info(f"Ingested file: {relative_path} (Category: {category})")
            except Exception as e:
                logging.error(f"Failed to read file {filepath}: {str(e)}")
                
    logging.info(f"Total files ingested: {len(md_files)}")
    return md_files

# 3. MARKDOWN CHUNKING STRATEGY
def split_markdown_by_headers(text: str) -> List[Dict]:
    lines = text.splitlines()
    blocks = []
    
    current_headings = {
        "Header 1": None,
        "Header 2": None,
        "Header 3": None
    }
    
    current_block_lines = []
    header_pattern = re.compile(r"^(#{1,3})\s+(.+)$")
    
    def save_current_block():
        block_text = "\n".join(current_block_lines).strip()
        if block_text:
            active_headings = {k: v for k, v in current_headings.items() if v is not None}
            blocks.append({
                "text_content": block_text,
                "headings": active_headings
            })
            
    for line in lines:
        match = header_pattern.match(line)
        if match:
            save_current_block()
            current_block_lines = []
            
            level_str, header_title = match.groups()
            level = len(level_str)
            header_title = header_title.strip()
            
            if level == 1:
                current_headings["Header 1"] = header_title
                current_headings["Header 2"] = None
                current_headings["Header 3"] = None
            elif level == 2:
                current_headings["Header 2"] = header_title
                current_headings["Header 3"] = None
            elif level == 3:
                current_headings["Header 3"] = header_title
        else:
            current_block_lines.append(line)
            
    save_current_block()
    return blocks

def split_text_recursively(text: str, chunk_size: int, chunk_overlap: int, separators: List[str] = None) -> List[str]:
    if separators is None:
        separators = ["\n\n", "\n", " ", ""]
        
    if len(text) <= chunk_size:
        return [text]
        
    separator = separators[-1]
    for s in separators:
        if s == "":
            separator = s
            break
        if s in text:
            separator = s
            break
            
    if separator != "":
        splits = text.split(separator)
    else:
        splits = list(text)
        
    chunks = []
    current_chunk_parts = []
    current_chunk_len = 0
    
    for part in splits:
        if len(part) > chunk_size:
            if current_chunk_parts:
                chunks.append(separator.join(current_chunk_parts))
                current_chunk_parts = []
                current_chunk_len = 0
                
            next_seps = separators[separators.index(separator) + 1:] if separator in separators else []
            sub_chunks = split_text_recursively(part, chunk_size, chunk_overlap, next_seps)
            
            for sub in sub_chunks[:-1]:
                chunks.append(sub)
            current_chunk_parts = [sub_chunks[-1]]
            current_chunk_len = len(sub_chunks[-1])
        else:
            extra_len = len(separator) if current_chunk_parts and separator != "" else 0
            part_len = len(part) + extra_len
            
            if current_chunk_len + part_len <= chunk_size:
                current_chunk_parts.append(part)
                current_chunk_len += part_len
            else:
                if current_chunk_parts:
                    chunks.append(separator.join(current_chunk_parts))
                    
                overlap_parts = []
                overlap_len = 0
                for p in reversed(current_chunk_parts):
                    p_extra = len(separator) if overlap_parts and separator != "" else 0
                    p_len = len(p) + p_extra
                    if overlap_len + p_len <= chunk_overlap:
                        overlap_parts.insert(0, p)
                        overlap_len += p_len
                    else:
                        break
                        
                current_chunk_parts = overlap_parts
                current_chunk_len = overlap_len
                
                extra_len = len(separator) if current_chunk_parts and separator != "" else 0
                current_chunk_parts.append(part)
                current_chunk_len += len(part) + extra_len
                
    if current_chunk_parts:
        chunks.append(separator.join(current_chunk_parts))
        
    return chunks

# 4. PIPELINE ORCHESTRATION
def chunk_markdown_pipeline(data_dir: str, chunk_size: int, chunk_overlap: int) -> List[Dict]:
    try:
        md_files = scan_and_read_md_files(data_dir)
    except Exception as e:
        logging.critical(f"Data ingestion failed: {str(e)}")
        return []
        
    all_chunks = []
    
    for file_info in md_files:
        file_name = file_info["file_name"]
        file_path = file_info["file_path"]
        category = file_info["category"]
        content = file_info["content"]
        
        file_base_name = Path(file_name).stem
        logging.info(f"Processing chunking for: {file_name}")
        
        try:
            header_blocks = split_markdown_by_headers(content)
            chunk_idx = 1
            file_chunks_count = 0
            
            for block in header_blocks:
                block_text = block["text_content"]
                headings = block["headings"]
                
                if len(block_text) > chunk_size:
                    sub_texts = split_text_recursively(block_text, chunk_size, chunk_overlap)
                else:
                    sub_texts = [block_text]
                    
                for sub_text in sub_texts:
                    sub_text = sub_text.strip()
                    if not sub_text:
                        continue
                        
                    chunk_id = f"{file_base_name}_chunk_{chunk_idx:03d}"
                    
                    all_chunks.append({
                        "chunk_id": chunk_id,
                        "text_content": sub_text,
                        "metadata": {
                            "source_file": file_path,
                            "category": category,
                            "headings": headings,
                            "chunk_index": chunk_idx
                        }
                    })
                    chunk_idx += 1
                    file_chunks_count += 1
                    
            logging.info(f"Successfully split '{file_name}' into {file_chunks_count} chunks.")
            
        except Exception as e:
            logging.error(f"Error chunking file '{file_name}': {str(e)}")
            
    logging.info(f"Total chunks created across all files: {len(all_chunks)}")
    return all_chunks

# 5. MAIN EXECUTION
if __name__ == "__main__":
    logging.info("Starting Data Ingestion & Chunking pipeline...")
    
    try:
        chunks = chunk_markdown_pipeline(
            data_dir=DATA_DIR,
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP
        )
        
        if chunks:
            os.makedirs(OUTPUT_DIR, exist_ok=True)
            output_file_path = os.path.join(OUTPUT_DIR, OUTPUT_FILE_NAME)
            
            logging.info(f"Saving all {len(chunks)} chunks to: {output_file_path}")
            with open(output_file_path, 'w', encoding='utf-8') as out_f:
                json.dump(chunks, out_f, ensure_ascii=False, indent=4)
            logging.info("Successfully saved output file.")
        else:
            logging.warning("No chunks were generated. Please check the data directory.")
            
    except Exception as ex:
        logging.critical(f"An unexpected error occurred in the pipeline: {str(ex)}")
