# Embbeding_RAG

---

## 1. Cấu trúc thư mục

```text
Embbeding_RAG/
├── chucks/                          # Thư mục chứa dữ liệu chunks đầu vào
│   ├── check_chunks.ipynb           # Kiểm tra số lượng và tính đầy đủ của các chunk của file
│   └── all_chunks.json              # File JSON lưu trữ toàn bộ các chunks văn bản từ Module 1
├── chroma_db/                       # Cơ sở dữ liệu vector ChromaDB cục bộ (sau khi nạp dữ liệu)
├── test_vector_db/                  # Module kiểm thử độ chính xác và tích hợp LLM
│   ├── result/                      # Kết quả sinh tự động từ quá trình chạy kiểm tra
│   │   ├── test_queries.json        # Bộ 100 câu hỏi kiểm thử tiếng Anh kèm đáp án mẫu
│   │   ├── evaluation_results.json  # Phân loại độ chính xác truy xuất (Retrieval) theo từng Rank
│   │   └── rag_pipeline_evaluation.json # Đánh giá 2x2 ma trận tích hợp RAG (Retrieval vs Generation)
│   ├── generate_and_test_queries.py # Tạo bộ câu hỏi trắc nghiệm tiếng Anh từ dữ liệu gốc
│   ├── query_vector_db.py           # Đánh giá độ chính xác truy xuất dữ liệu từ cơ sở dữ liệu
│   └── rag_pipeline.py              # Đánh giá liên kết truy xuất và sinh câu trả lời bằng LLM cục bộ (Ollama)
├── data_ingestion_chunking.py        # Cắt nhỏ tài liệu Markdown bằng thuật toán đệ quy thuần Python (Module 1)
├── embedding_storage.py             # Sinh vector nhúng lưu vào ChromaDB cục bộ (Module 2)
└── requirements.txt                 # Danh sách các thư viện cần thiết của dự án
```

---

## 2. Chi tiết chức năng từng file

### `data_ingestion_chunking.py`
* **Nhiệm vụ**: Quét đệ quy toàn bộ file `.md` trong thư mục dữ liệu thô, phân tích cấu trúc Heading (`#`, `##`, `###`) của tài liệu để cắt khối. Các khối quá lớn tiếp tục được phân tách đệ quy về ngưỡng tối đa `500` ký tự (độ chồng chéo `50` ký tự).
* **Đầu ra**: File [chucks/all_chunks.json].

### `embedding_storage.py`
* **Nhiệm vụ**: Đọc dữ liệu từ file JSON, sử dụng mô hình nhúng cục bộ `sentence-transformers/all-MiniLM-L6-v2` để sinh vector nhúng và đẩy toàn bộ dữ liệu vào ChromaDB cục bộ dưới dạng batch `32` phần tử.
* **Xử lý Metadata**: Tự động chuyển đổi các dictionary lồng nhau (headings) thành chuỗi JSON thô để tương thích với ChromaDB.

### `test_vector_db/generate_and_test_queries.py`
* **Nhiệm vụ**: Lấy mẫu ngẫu nhiên từ file chunks và biên dịch thành câu hỏi tiếng Anh tự nhiên tương ứng bằng các mẫu câu NLP động.
* **Đầu ra**: File [test_vector_db/result/test_queries.json].

### `test_vector_db/query_vector_db.py`
* **Nhiệm vụ**: Đọc câu hỏi kiểm thử từ thư mục `result/`, thực hiện tìm kiếm tương đồng trên ChromaDB và thống kê độ chính xác truy xuất ở các mốc: chính xác tuyệt đối Rank 1 và tỷ lệ bao phủ (hit rate) trong Top $K$ ($k=3$).
* **Đầu ra**: Bản in console thống kê và tệp phân loại chi tiết [test_vector_db/result/evaluation_results.json].

### `test_vector_db/rag_pipeline.py`
* **Nhiệm vụ**: Kết hợp việc tìm kiếm ngữ cảnh với mô hình ngôn ngữ lớn cục bộ **Ollama** chạy CPU (`qwen2:1.5b`) sử dụng cấu trúc prompt tiếng Anh. Đo lường chất lượng sinh câu trả lời bằng phương pháp Cosine Similarity giữa vector nhúng của câu trả lời từ LLM với câu trả lời tham chiếu (ngưỡng `0.70`).
* **Đầu ra**: Bảng ma trận hiệu năng 2x2 trên Console và file chi tiết các ca kiểm thử tương ứng tại [test_vector_db/result/rag_pipeline_evaluation.json].

---

## 3. Cài đặt dự án

### Cài đặt thư viện Python
Trong môi trường ảo của bạn (Conda hoặc virtualenv), chạy lệnh sau:
```bash
pip install -r requirements.txt
```
---

## 4. Thứ tự thực thi

### Bước 1: Ingestion & Cắt nhỏ chunk tài liệu
```bash
python data_ingestion_chunking.py
```
*Tạo ra tệp tin dữ liệu trung gian `chucks/all_chunks.json`.*

### Bước 2: Nhúng vector và nạp dữ liệu vào ChromaDB
```bash
python embedding_storage.py
```
*Tạo chỉ mục vector cục bộ bên trong thư mục `chroma_db/`.*

### Bước 3: Sinh tự động 100 câu hỏi kiểm thử tiếng Anh
```bash
python test_vector_db/generate_and_test_queries.py
```
*Sinh file câu hỏi `test_vector_db/result/test_queries.json`.*

### Bước 4: Đánh giá chất lượng của bộ máy tìm kiếm (Retrieval)
```bash
python test_vector_db/query_vector_db.py
```
*Tính tỷ lệ thành công khi truy xuất dữ liệu trong cơ sở dữ liệu.*

### Bước 5: Đánh giá toàn bộ hiệu năng RAG (Tương tác LLM)
```bash
python test_vector_db/rag_pipeline.py
```
*Đo lường độ chính xác tổng hợp của cả quá trình tìm kiếm ngữ cảnh lẫn sinh từ ngữ từ mô hình ngôn ngữ.*
