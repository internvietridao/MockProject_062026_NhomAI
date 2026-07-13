import os
import json
import logging
from pathlib import Path
from typing import List, Dict
import chromadb
from chromadb.utils import embedding_functions

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

# =====================================================================
# 1. CONFIGURATION BLOCK
# =====================================================================
CHUNKS_JSON_PATH = str(Path(__file__).parent / "chucks" / "all_chunks.json")
VECTOR_DB_DIR = str(Path(__file__).parent / "chroma_db")
COLLECTION_NAME = "rag_documents"
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
BATCH_SIZE = 32

# =====================================================================
# 2. READ DATA INPUT
# =====================================================================
def load_chunks_from_json(json_path: str) -> List[Dict]:
    path = Path(json_path)
    if not path.exists():
        logging.error(f"Chunks JSON file does not exist at: {json_path}")
        raise FileNotFoundError(f"Required chunks file not found: {json_path}")
        
    logging.info(f"Loading data chunks from: {path.resolve()}")
    try:
        with open(path, 'r', encoding='utf-8') as f:
            chunks = json.load(f)
        logging.info(f"Successfully loaded {len(chunks)} chunks.")
        return chunks
    except Exception as e:
        logging.error(f"Failed to read or parse JSON file: {str(e)}")
        raise e

# =====================================================================
# 3. EMBEDDING AND STORAGE INTO VECTOR DB
# =====================================================================
def store_chunks_in_chroma(chunks: List[Dict], collection, batch_size: int = 32):
    total_chunks = len(chunks)
    total_batches = (total_chunks + batch_size - 1) // batch_size
    logging.info(f"Storing {total_chunks} chunks into ChromaDB in {total_batches} batches...")
    
    for idx, i in enumerate(range(0, total_chunks, batch_size)):
        batch = chunks[i:i + batch_size]
        
        ids = []
        documents = []
        metadatas = []
        
        for item in batch:
            ids.append(item["chunk_id"])
            documents.append(item["text_content"])
            
            orig_meta = item.get("metadata", {})
            
            headings_dict = orig_meta.get("headings", {})
            headings_json_str = json.dumps(headings_dict, ensure_ascii=False)
            
            db_meta = {
                "source": orig_meta.get("source_file", ""),
                "category": orig_meta.get("category", ""),
                "headings": headings_json_str,
                "chunk_index": int(orig_meta.get("chunk_index", 0))
            }
            metadatas.append(db_meta)
            
        try:
            collection.upsert(
                ids=ids,
                documents=documents,
                metadatas=metadatas
            )
            logging.info(f"Progress: Processed batch {idx + 1}/{total_batches} (Chunks {i + 1} to {min(i + batch_size, total_chunks)})")
        except Exception as e:
            logging.error(f"Failed to load batch starting at index {i}: {str(e)}")
            raise e

# =====================================================================
# 4. MAIN PIPELINE EXECUTION
# =====================================================================
if __name__ == "__main__":
    logging.info("Starting ChromaDB Embedding & Storage pipeline...")
    
    try:
        chunks_data = load_chunks_from_json(CHUNKS_JSON_PATH)
        
        os.makedirs(VECTOR_DB_DIR, exist_ok=True)
        
        logging.info(f"Connecting to persistent ChromaDB at: {VECTOR_DB_DIR}")
        client = chromadb.PersistentClient(path=VECTOR_DB_DIR)
        
        logging.info(f"Loading embedding model: {EMBEDDING_MODEL_NAME}")
        embedding_func = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=EMBEDDING_MODEL_NAME
        )
        
        logging.info(f"Accessing collection: '{COLLECTION_NAME}'")
        collection = client.get_or_create_collection(
            name=COLLECTION_NAME,
            embedding_function=embedding_func
        )
        
        store_chunks_in_data = store_chunks_in_chroma(chunks_data, collection, BATCH_SIZE)
        
        total_records = collection.count()
        logging.info("=" * 60)
        logging.info("SUCCESS: Data embedding and storage completed!")
        logging.info(f"Total documents inside collection '{COLLECTION_NAME}': {total_records}")
        logging.info("=" * 60)
        
    except Exception as ex:
        logging.critical(f"Pipeline crashed with an unexpected error: {str(ex)}")
