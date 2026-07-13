# RAG Evaluation Report

---

## 1. Đánh giá tầng truy xuất (Retrieval Accuracy Report)

Mục tiêu kiểm tra khả năng tìm kiếm và xếp hạng đúng chunk chứa thông tin đáp án trong Top $K$ ($K=3$) kết quả trả về từ ChromaDB.

* **Tổng số câu truy vấn đánh giá**: 100
* **Chỉ mục tìm kiếm (Top-K Hit Rate / Recall)**: **61.00%** (61/100 câu hỏi tìm thấy đúng tài liệu trong Top 3)
* **Độ chính xác Top 1 (Precision@1)**: **54.00%** (54/100 câu hỏi tìm thấy đúng tài liệu ở vị trí đầu tiên)

### Phân phối kết quả truy xuất
| Vị trí khớp (Rank) | Số lượng câu hỏi | Tỷ lệ (%) | Trạng thái |
| :--- | :---: | :---: | :--- |
| **Rank 1** (Khớp vị trí đầu tiên) | 54 | 54.00% | Rất tốt |
| **Rank 2** (Khớp vị trí thứ hai) | 4 | 4.00% | Chấp nhận được |
| **Rank 3** (Khớp vị trí thứ ba) | 3 | 3.00% | Chấp nhận được |
| **Not Found** (Không nằm trong Top 3) | 39 | 39.00% | Thất bại |

---

## 2. Đánh giá tích hợp RAG (Joint RAG Pipeline Report)

Mục tiêu đánh giá khả năng sinh câu trả lời của LLM (`qwen2:1.5b`) dựa trên ngữ cảnh được cung cấp. So sánh ngữ nghĩa giữa câu trả lời của LLM với câu trả lời mẫu (`reference_answer`) bằng độ tương đồng Cosine (ngưỡng chấp nhận $\ge 0.70$).

* **Tổng số câu hỏi đánh giá**: 100
* **Tổng số câu trả lời Đúng (Correct)**: **12 / 100 (12.00%)**
* **Tổng số câu trả lời Sai (Incorrect)**: **88 / 100 (88.00%)**

### Ma trận hiệu năng 2x2 (Retrieval vs Generation)

| Trạng thái truy xuất (Retrieval) | Số lượng truy vấn | Trạng thái sinh (Generation) | Số lượng | Tỷ lệ trong nhóm |
| :--- | :---: | :--- | :---: | :---: |
| **Truy xuất Đúng** (Tìm thấy trong Top 3) | 61 | Trả lời Đúng (Cosine $\ge 0.7$) | 12 | 19.67% |
| | | Trả lời Sai (Cosine $< 0.7$) | 49 | 80.33% |
| **Truy xuất Sai** (Không có trong Top 3) | 39 | Trả lời Đúng (Cosine $\ge 0.7$) | 0 | 0.00% |
| | | Trả lời Sai (Cosine $< 0.7$) | 39 | 100.00% |

### Chi tiết tỷ lệ trả lời đúng theo thứ tự Rank của ngữ cảnh

* **Khớp ở vị trí Rank 1** (54 câu truy vấn):
  * Trả lời Đúng: **12 câu (22.22%)**
  * Trả lời Sai: **42 câu (77.78%)**
* **Khớp ở vị trí Rank 2** (4 câu truy vấn):
  * Trả lời Đúng: **0 câu (0.00%)**
  * Trả lời Sai: **4 câu (100.00%)**
* **Khớp ở vị trí Rank 3** (3 câu truy vấn):
  * Trả lời Đúng: **0 câu (0.00%)**
  * Trả lời Sai: **3 câu (100.00%)**

---

## 3. Phân tích & Nhận định

1. **Hiệu năng tìm kiếm cơ sở dữ liệu (Retrieval)**:
   * Đạt mức baseline chấp nhận được với **61.00%** Recall. 
   * Có tới **54.00%** trường hợp đưa ra kết quả chuẩn xác nhất ngay ở vị trí Rank 1.
   * Cần cải thiện thuật toán chunking hoặc chọn mô hình nhúng mạnh hơn để giảm thiểu tỷ lệ thất thoát 39% câu hỏi không tìm thấy tài liệu gốc.

2. **Chất lượng mô hình ngôn ngữ sinh (LLM Generation)**:
   * Tỷ lệ trả lời đúng khá thấp (**12.00%** tổng quát).
   * Khi ngữ cảnh được cung cấp chuẩn ở Rank 1, LLM cũng chỉ trả lời đúng đạt **22.22%**.
   * *Nguyên nhân*:
     * Mô hình ngôn ngữ `qwen2:1.5b` (1.5 tỷ tham số) tối ưu cho CPU nhưng năng lực đọc hiểu ngữ cảnh dài và diễn đạt tự nhiên bằng tiếng Anh còn hạn chế so với các mô hình lớn hơn (như `llama3:8b` hoặc `qwen2:7b`).
     * Ngưỡng so khớp Cosine Similarity (`0.70`) có thể tương đối khắt khe đối với cách diễn đạt của LLM nhỏ so với văn bản gốc chứa nhiều thuật ngữ chuyên ngành.
