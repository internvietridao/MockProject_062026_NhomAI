import os
import json
import logging
import sys
import re
import math
from collections import Counter
from pathlib import Path
from typing import List, Dict
import chromadb
from chromadb.utils import embedding_functions

# Setup python path to import config.py from parent directory
sys.path.append(str(Path(__file__).resolve().parent.parent))
import config

VECTOR_DB_DIR = config.VECTOR_DB_DIR
COLLECTION_NAME = config.COLLECTION_NAME
EMBEDDING_MODEL_NAME = config.EMBEDDING_MODEL_NAME
TOP_K = config.TOP_K
RETRIEVAL_MODE = config.RETRIEVAL_MODE

# 1. BM25 RETRIEVAL CLASS & INITIALIZATION
class BM25Retriever:
    def __init__(self, chunks_json_path: str, k1=1.5, b=0.75):
        self.k1 = k1
        self.b = b
        self.chunks_data = []
        if os.path.exists(chunks_json_path):
            try:
                with open(chunks_json_path, 'r', encoding='utf-8') as f:
                    self.chunks_data = json.load(f)
            except Exception as e:
                logging.error(f"Failed to load chunks for BM25: {str(e)}")
        else:
            logging.warning(f"Chunks JSON not found at: {chunks_json_path}. BM25 will be empty.")
            
        self.corpus_size = len(self.chunks_data)
        self.avg_doc_len = 0
        self.doc_lengths = []
        self.doc_freqs = {}
        self.term_freqs = []
        
        tokenized_corpus = []
        for chunk in self.chunks_data:
            tokens = self._tokenize(chunk["text_content"])
            tokenized_corpus.append(tokens)
            
        total_len = 0
        for doc in tokenized_corpus:
            doc_len = len(doc)
            self.doc_lengths.append(doc_len)
            total_len += doc_len
            
            tf = Counter(doc)
            self.term_freqs.append(tf)
            
            for term in tf.keys():
                self.doc_freqs[term] = self.doc_freqs.get(term, 0) + 1
                
        self.avg_doc_len = total_len / self.corpus_size if self.corpus_size > 0 else 0
        
        self.idf = {}
        for term, df in self.doc_freqs.items():
            self.idf[term] = math.log((self.corpus_size - df + 0.5) / (df + 0.5) + 1.0)
            
    def _tokenize(self, text):
        return re.findall(r'\w+', text.lower())
        
    def query(self, query_text: str, top_k: int = 3) -> List[Dict]:
        if self.corpus_size == 0:
            return []
            
        query_tokens = self._tokenize(query_text)
        scores = [0.0] * self.corpus_size
        
        for term in query_tokens:
            if term not in self.idf:
                continue
            idf_val = self.idf[term]
            for idx in range(self.corpus_size):
                tf = self.term_freqs[idx].get(term, 0)
                doc_len = self.doc_lengths[idx]
                numerator = tf * (self.k1 + 1)
                denominator = tf + self.k1 * (1 - self.b + self.b * doc_len / self.avg_doc_len)
                scores[idx] += idf_val * (numerator / denominator)
                
        ranked_indices = sorted(range(self.corpus_size), key=lambda i: scores[i], reverse=True)[:top_k]
        
        results = []
        for idx in ranked_indices:
            chunk = self.chunks_data[idx]
            
            headings_str = chunk.get("metadata", {}).get("headings", "{}")
            if isinstance(headings_str, dict):
                headings_dict = headings_str
            else:
                try:
                    headings_dict = json.loads(headings_str)
                except Exception:
                    headings_dict = {}
                    
            results.append({
                "chunk_id": chunk["chunk_id"],
                "score": float(scores[idx]),
                "text_content": chunk["text_content"],
                "metadata": {
                    "source": chunk.get("metadata", {}).get("source_file", ""),
                    "category": chunk.get("metadata", {}).get("category", ""),
                    "headings": headings_dict,
                    "chunk_index": chunk.get("metadata", {}).get("chunk_index", 0)
                }
            })
        return sorted(results, key=lambda x: x["score"], reverse=True)

logging.info("Initializing BM25 index over all document chunks...")
bm25_retriever = BM25Retriever(config.CHUNKS_JSON_PATH)
logging.info(f"BM25 index initialized with {bm25_retriever.corpus_size} documents.")

# 2. RETRIEVAL LOGIC
def retrieve_context(
    query_text: str, 
    top_k: int = TOP_K, 
    vector_db_dir: str = VECTOR_DB_DIR, 
    collection_name: str = COLLECTION_NAME, 
    embedding_model_name: str = EMBEDDING_MODEL_NAME
) -> List[Dict]:
    if RETRIEVAL_MODE == "bm25":
        return bm25_retriever.query(query_text, top_k=top_k)
        
    if not os.path.exists(vector_db_dir):
        logging.error(f"ChromaDB persistent directory not found at: {vector_db_dir}")
        raise FileNotFoundError(f"Database directory missing: {vector_db_dir}")
        
    try:
        client = chromadb.PersistentClient(path=vector_db_dir)
        
        embedding_func = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=embedding_model_name
        )
        
        collection = client.get_collection(
            name=collection_name,
            embedding_function=embedding_func
        )
        
        chroma_k = top_k * 3 if RETRIEVAL_MODE == "hybrid" else top_k
        results = collection.query(
            query_texts=[query_text],
            n_results=chroma_k
        )
        
        dense_results = []
        
        ids = results.get("ids", [[]])[0]
        distances = results.get("distances", [[]])[0]
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        
        for idx in range(len(ids)):
            meta = metadatas[idx] if idx < len(metadatas) else {}
            
            headings_str = meta.get("headings", "{}")
            try:
                headings_dict = json.loads(headings_str)
            except Exception:
                headings_dict = {}
                
            chunk_data = {
                "chunk_id": ids[idx],
                "score": distances[idx],
                "text_content": documents[idx],
                "metadata": {
                    "source": meta.get("source", ""),
                    "category": meta.get("category", ""),
                    "headings": headings_dict,
                    "chunk_index": meta.get("chunk_index", 0)
                }
            }
            dense_results.append(chunk_data)
            
        if RETRIEVAL_MODE == "cosine":
            return dense_results
            
        sparse_results = bm25_retriever.query(query_text, top_k=top_k * 3)
        
        scores = {}
        docs = {}
        rrf_constant = 60
        
        for rank, doc in enumerate(dense_results, 1):
            doc_id = doc["chunk_id"]
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (rrf_constant + rank)
            docs[doc_id] = doc
            
        for rank, doc in enumerate(sparse_results, 1):
            doc_id = doc["chunk_id"]
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (rrf_constant + rank)
            if doc_id not in docs:
                docs[doc_id] = doc
                
        sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)[:top_k]
        
        merged_results = []
        for doc_id in sorted_ids:
            doc = docs[doc_id]
            doc["score"] = scores[doc_id]
            merged_results.append(doc)
            
        return merged_results
        
    except Exception as e:
        logging.error(f"Failed to query database for text '{query_text}': {str(e)}")
        raise e
