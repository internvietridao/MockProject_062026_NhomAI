# Module Embedding & Hybrid RAG System

Hệ thống Retrieval-Augmented Generation (RAG) sử dụng tìm kiếm kết hợp (Hybrid Search: ChromaDB Vector Cosine + BM25 Lexical) và tích hợp kết nối LLM Cloud API (Lightning AI / Hugging Face).

## Cấu trúc Thư mục

```
Embedding_RAG/
├── data_ingestion_chunking.py   # Script quét tài liệu Markdown và tạo Chunks
├── chunks/                      # Lưu trữ file JSON chứa toàn bộ chunks
│   └── all_chunks.json
└── all-MiniLM-L6-v2/            # Module Embedding với SentenceTransformers
    ├── config.py                # Cấu hình chính (Model, Database, Lightning API URL)
    ├── embedding_storage.py     # Script tính Embeddings và lưu vào ChromaDB
    ├── run.py                   # Script khởi chạy toàn bộ pipeline
    └── test_vector_db/
        ├── retrieval.py         # Engine truy xuất dữ liệu (Hybrid BM25 + Vector)
        ├── rag_pipeline.py      # RAG Pipeline tích hợp gọi API Lightning AI
        ├── query_vector_db.py   # Test truy vấn Vector DB
        └── generate_and_test_queries.py # Tạo bộ câu hỏi kiểm thử
```

## Hướng dẫn Sử dụng

1. **Tạo Chunks dữ liệu từ tài liệu Markdown:**
   ```bash
   python data_ingestion_chunking.py
   ```

2. **Cấu hình API Lightning AI trong `all-MiniLM-L6-v2/config.py`:**
   Cập nhật `LIGHTNING_API_URL` bằng URL Public từ Lightning Studio của bạn:
   ```python
   LIGHTNING_API_URL = "https://8000-xxxx.lightning-studio.net"
   LLM_PROVIDER = "lightning"
   ```

3. **Chạy Embedding & Indexing vào ChromaDB:**
   ```bash
   python all-MiniLM-L6-v2/embedding_storage.py
   ```

4. **Chạy RAG Pipeline:**
   ```bash
   python all-MiniLM-L6-v2/test_vector_db/rag_pipeline.py
   ```
