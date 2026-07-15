# Embedding_RAG

---

## 1. Cấu trúc thư mục

```text
Embbeding_RAG/
├── chucks/                          # Chứa dữ liệu chunks đầu vào (all_chunks.json)
├── all-MiniLM-L6-v2/                # Module RAG sử dụng mô hình all-MiniLM-L6-v2
│   ├── chroma_db/                   # Database vector ChromaDB (không gian Cosine)
│   ├── test_vector_db/              
│   │   ├── result/                  # Thư mục lưu báo cáo kết quả kiểm thử (.json, .md)
│   │   ├── generate_and_test_queries.py
│   │   ├── query_vector_db.py
│   │   ├── rag_pipeline.py
│   │   └── retrieval.py             # Thư viện tìm chung chứa BM25 và Hybrid Search (RRF)
│   ├── config.py                    # Cấu hình tập trung tham số
│   ├── embedding_storage.py         # Nhúng và lưu vector vào ChromaDB
│   └── run.py                       # Chạy tự động quy trình load DB & đánh giá
├── nomic-embed-text-v1.5/           # Module RAG sử dụng mô hình nomic-embed-text-v1.5
│   └── (Cấu trúc tương tự như all-MiniLM-L6-v2 ở trên)
├── bge-small-en-v1.5/               # Module RAG sử dụng mô hình BAAI/bge-small-en-v1.5
│   └── (Cấu trúc tương tự như all-MiniLM-L6-v2 ở trên)
├── data_ingestion_chunking.py        # Đọc dữ liệu MD thô và phân mảnh (Module 1)
└── requirements.txt                 # Dependencies của dự án
```

---

## 2. Các chế độ truy xuất (`RETRIEVAL_MODE` trong `config.py`)

* **`cosine`**: Tìm kiếm ngữ nghĩa qua vector nhúng (Dense Retrieval).
* **`bm25`**: Tìm kiếm từ khóa chính xác qua thuật toán BM25 (Sparse Retrieval).
* **`hybrid`**: Kết hợp `cosine` + `bm25` qua cơ chế trộn thứ hạng chéo RRF ($s=60$).

---

## 3. Chức năng chính các tệp tin

* **`data_ingestion_chunking.py`**: Quét, đọc và phân mảnh tài liệu markdown thô thành các block.
* **`[model]/config.py`**: Chứa toàn bộ cấu hình chung (model, DB path, prompt, LLM,...).
* **`[model]/embedding_storage.py`**: Vector hóa tài liệu và nạp vào ChromaDB (sử dụng độ đo Cosine).
* **`[model]/test_vector_db/retrieval.py`**: Đóng gói logic truy xuất ngữ cảnh (Cosine, BM25, Hybrid).
* **`[model]/test_vector_db/generate_and_test_queries.py`**: Sinh ngẫu nhiên bộ 100 câu hỏi trắc nghiệm tiếng Anh từ tài liệu gốc.
* **`[model]/test_vector_db/query_vector_db.py`**: Đánh giá độ chính xác tìm kiếm (Accuracy, Hit Rate, Precision, MRR) và xuất báo cáo.
* **`[model]/test_vector_db/rag_pipeline.py`**: Chạy pipeline RAG gửi câu hỏi và ngữ cảnh đến LLM, so sánh chất lượng kết quả.
* **`[model]/run.py`**: Chạy tuần tự quy trình nạp DB, sinh câu hỏi và đánh giá độ chính xác truy xuất.

---

## 4. Hướng dẫn thực thi

### Bước 1: Phân mảnh tài liệu (chạy tại thư mục gốc)
```bash
python data_ingestion_chunking.py
```

### Bước 2: Nạp dữ liệu và đánh giá tìm kiếm (cho từng mô hình)
Di chuyển vào thư mục mô hình mong muốn và khởi chạy:

* **Với mô hình MiniLM**:
  ```bash
  cd all-MiniLM-L6-v2
  python run.py
  ```

* **Với mô hình Nomic**:
  ```bash
  cd nomic-embed-text-v1.5
  python run.py
  ```

* **Với mô hình BGE**:
  ```bash
  cd bge-small-en-v1.5
  python run.py
  ```

### Bước 3: Đánh giá tích hợp RAG (gửi LLM)
Khởi chạy local LLM Ollama hoặc thiết lập API Key OpenAI trong `config.py` tương ứng rồi chạy:
```bash
cd test_vector_db
python rag_pipeline.py
```
