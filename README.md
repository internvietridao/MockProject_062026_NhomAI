# AI Chatbot - Nursing Home Management Assistant

Hệ thống AI Chatbot chuyên biệt hỗ trợ quản lý viện dưỡng lão tại Mỹ (Skilled Nursing Facility). Dự án tích hợp công nghệ Fine-tuning LLM và hệ thống Hybrid RAG (Retrieval-Augmented Generation) để trả lời các câu hỏi về y tế, quy trình chăm sóc điều dưỡng, và quy định pháp lý (California Title 22, OSHA, MDS 3.0 RAI).

---

## 📂 Tổng quan cấu trúc thư mục dự án

```
├── analysis_preprocessing/ # Thư mục xử lý và chuẩn hóa dữ liệu từ XML sang JSON
├── data_clean/             # Chứa dữ liệu sạch cuối cùng đã chuẩn hóa (Fine-tune JSON & RAG Markdown)
├── train/                  # Component cấu hình, mã nguồn huấn luyện model LLM (QLoRA 4-bit)
├── Embedding_RAG/          # Component hệ thống Hybrid RAG (ChromaDB + BM25) & Connector gọi LLM Cloud API
├── LLM-as-Judge/           # Chứa các báo cáo đánh giá chất lượng mô hình bằng LLM-as-a-judge (Qwen, Gemma, Phi-3)
├── deploy_qwen_lightning_ai.md # Tài liệu hướng dẫn deploy LLM Server từ A-Z lên Lightning AI Studio
└── README.md               # Tài liệu tổng quan dự án
```

---

## 🚀 Hướng dẫn khởi chạy nhanh

### 1. Huấn luyện mô hình LLM Fine-Tuned (Training)
Xem chi tiết hướng dẫn tại [train/README.md](file:///e:/AI_VTD/MockProject_062026_NhomAI/train/README.md).

### 2. Triển khai LLM API Server lên Cloud
Xem chi tiết hướng dẫn deploy model Qwen-0.5B / Gemma-2B lên Lightning AI Studio tại [deploy_qwen_lightning_ai.md](file:///e:/AI_VTD/MockProject_062026_NhomAI/deploy_qwen_lightning_ai.md).

### 3. Khởi chạy Chatbot RAG (Kiểm thử tương tác)
- **Tạo Vector DB & Embeddings (nếu lần đầu chạy):**
  ```bash
  python Embedding_RAG/data_ingestion_chunking.py
  python Embedding_RAG/all-MiniLM-L6-v2/embedding_storage.py
  ```
- **Khởi chạy Chatbot CLI:**
  ```bash
  python Embedding_RAG/all-MiniLM-L6-v2/chat_cli.py
  ```

---

*Lưu ý: Bên trong mỗi thư mục con ở trên đều có file `README.md` riêng biệt mô tả chi tiết cấu trúc file, script vận hành và hướng dẫn chạy cho module đó.*
