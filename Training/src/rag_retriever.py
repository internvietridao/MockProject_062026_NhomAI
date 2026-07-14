"""
rag_retriever.py
---------------
Module để load embeddings và thực hiện similarity search cho RAG
"""

import json
import numpy as np
from pathlib import Path
from typing import List, Tuple
from sentence_transformers import SentenceTransformer
import os

class RAGRetriever:
    def __init__(self, embeddings_dir: str = None, embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """
        Args:
            embeddings_dir: Đường dẫn đến thư mục chứa file embeddings JSON
            embedding_model: Model embedding để encode query
        """
        if embeddings_dir is None:
            # Mặc định dùng thư mục chunk_embeddings từ project chính
            project_root = Path(__file__).resolve().parent.parent.parent
            embeddings_dir = project_root / "data_clean" / "chunk_embeddings"
        
        self.embeddings_dir = Path(embeddings_dir)
        self.embedding_model = embedding_model
        self.chunks = []
        self.embeddings = None
        self.model = None
        
    def load_embeddings(self):
        """Load embeddings từ thư mục chứa các file JSON"""
        print(f"Đang load embeddings từ {self.embeddings_dir}...")
        
        if not self.embeddings_dir.exists():
            raise FileNotFoundError(f"Không tìm thấy thư mục embeddings: {self.embeddings_dir}")
        
        # Load tất cả các file embeddings trong thư mục
        all_chunks = []
        for file_path in sorted(self.embeddings_dir.glob("*_embeddings.json")):
            with open(file_path, 'r', encoding='utf-8') as f:
                chunks = json.load(f)
                all_chunks.extend(chunks)
                print(f"  - Đã load {len(chunks)} chunks từ {file_path.name}")
        
        self.chunks = all_chunks
        
        # Extract embeddings
        self.embeddings = np.array([chunk['embedding'] for chunk in self.chunks])
        
        print(f"Đã load tổng cộng {len(self.chunks)} chunks")
        
    def load_model(self):
        """Load model embedding để encode query"""
        if self.model is None:
            print(f"Đang load embedding model: {self.embedding_model}...")
            self.model = SentenceTransformer(self.embedding_model)
            print("Load embedding model xong.")
    
    def search(self, query: str, top_k: int = 5) -> List[str]:
        """
        Tìm kiếm chunks tương tự với query
        
        Args:
            query: Câu hỏi của user
            top_k: Số chunks trả về
            
        Returns:
            Danh sách nội dung chunks
        """
        if self.embeddings is None:
            self.load_embeddings()
        if self.model is None:
            self.load_model()
        
        # Encode query
        query_embedding = self.model.encode(query, show_progress_bar=False)
        
        # Tính cosine similarity
        similarities = np.dot(self.embeddings, query_embedding) / (
            np.linalg.norm(self.embeddings, axis=1) * np.linalg.norm(query_embedding)
        )
        
        # Get top-k indices
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        
        # Return chunks content
        results = []
        for idx in top_indices:
            chunk = self.chunks[idx]
            results.append(chunk['content'])
            print(f"  - Similarity: {similarities[idx]:.4f} | Source: {chunk['filename']}")
        
        return results
