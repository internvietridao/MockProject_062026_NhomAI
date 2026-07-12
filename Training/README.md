## 📂 Train / Validation / Test split

`pipeline/build_train_dataset.py` sẽ xáo trộn dữ liệu (sử dụng `SPLIT_SEED`
trong `src/config.py` để mỗi lần chạy đều cho cùng một kết quả), sau đó chia
theo các tỷ lệ `TRAIN_RATIO`, `VAL_RATIO` và `TEST_RATIO`.

Các file được tạo gồm:

- 📘 **train.jsonl**: dùng để fine-tune model (`pipeline/train.py`).
- 📗 **val.jsonl**: dùng để theo dõi validation loss trong quá trình train
  (`eval_strategy="epoch"` của `SFTConfig`). Tập này chỉ phục vụ đánh giá,
  không tham gia cập nhật trọng số.
- 📕 **test.jsonl**: tập dữ liệu model chưa từng thấy trong quá trình train.
  `pipeline/evaluate.py` sử dụng tập này để đánh giá cuối cùng bằng RAGAs,
  phản ánh khả năng tổng quát hóa của model thay vì khả năng ghi nhớ dữ liệu.

`train.jsonl` và `val.jsonl` được lưu theo định dạng chat `messages`, phù hợp
để huấn luyện bằng `SFTTrainer`.

`test.jsonl` giữ nguyên các trường `{question, contexts, ground_truth}` vì
`evaluate.py` sẽ để model tự sinh câu trả lời trước khi tiến hành đánh giá.

---

## 🔍 Bật / tắt RAG

Hiện tại project **chưa kết nối với vector database** nên mặc định
`USE_RAG=False` (xem trong `src/config.py`).

Ở chế độ này, model được huấn luyện như một chatbot hỏi đáp thông thường.
`build_prompt()` sẽ không chèn phần ngữ cảnh (context) và system prompt cũng
được điều chỉnh để phù hợp với trường hợp không có tài liệu tham chiếu.

Khi đã tích hợp vector database, có thể bật RAG bằng:

```bash
MEDQUAD_USE_RAG=1 python -m pipeline.build_train_dataset
```

Khi đó:

- ✅ `build_train_dataset.py` sẽ tạo prompt có context.
- ✅ `evaluate.py` sẽ sử dụng đầy đủ các metric của RAGAs như
  `faithfulness`, `context_precision` và `context_recall`.

Nếu không bật RAG, chỉ sử dụng `answer_relevancy`.

`pipeline/chat.py` hoạt động độc lập với cờ này. Có thể truyền
`chunks=None` để thử chế độ không dùng RAG hoặc truyền danh sách context thật
sau khi đã tích hợp vector database.

---

## 🚀 Cách chạy

```bash
pip install -r requirements.txt

# 1. Đặt medquad.json vào thư mục data/

# 2. Tạo train/validation/test
python -m pipeline.build_train_dataset

# 3. Fine-tune LoRA
python -m pipeline.train

# 4. Demo chatbot
python -m pipeline.chat

# 5. Đánh giá
python -m pipeline.evaluate
```

Nên chạy bằng:

```bash
python -m pipeline.<script_name>
```

thay vì

```bash
python pipeline/<script_name>.py
```

để Python tự nhận đúng thư mục gốc của project.

---

## ⚙️ Đổi model hoặc đường dẫn

Hầu hết các thiết lập đều nằm trong `src/config.py`.

Ngoài ra có thể ghi đè bằng biến môi trường:

```bash
MEDQUAD_BASE_MODEL="Qwen/Qwen2.5-1.5B-Instruct" python -m pipeline.train

MEDQUAD_OUTPUT_DIR="/kaggle/working/output" python -m pipeline.train
```

---

## ☁️ Chạy trên Google Colab

- 📁 Mount Google Drive.
- 📂 Di chuyển vào thư mục project (`src/`, `pipeline/`, ...).
- ▶️ Chạy các lệnh như hướng dẫn ở trên.

Phiên bản hiện tại không cần thêm `sys.path.append(...)` thủ công.

---

## 🏆 Chạy trên Kaggle

Mở notebook `kaggle/main_pipeline.ipynb`.

Có thể:

- 📦 Upload toàn bộ project thành Kaggle Dataset.
- 🔗 Hoặc clone trực tiếp repository từ GitHub.

Notebook sẽ tự cài các thư viện trong `requirements.txt` và chạy toàn bộ
pipeline.

---

## 📝 Lưu ý

- 🤖 `pipeline/evaluate.py` sử dụng **hai model riêng biệt**.

  - **Model được đánh giá**: base model + LoRA adapter, chỉ dùng để sinh câu trả lời.
  - **Model giám khảo**: `prometheus-eval/prometheus-7b-v2.0`, chỉ dùng để chấm điểm.

  Cách làm này giúp giảm hiện tượng **self-preference bias** (model tự chấm cao
  câu trả lời của chính mình).

- 💾 Prometheus 2 mặc định được load ở chế độ **4-bit** (`JUDGE_LOAD_IN_4BIT`)
  để phù hợp với GPU miễn phí trên Colab hoặc Kaggle. Có thể thay đổi bằng
  `MEDQUAD_JUDGE_MODEL` hoặc `MEDQUAD_JUDGE_4BIT=0`.

- 📊 Điểm số từ Prometheus chỉ mang tính tham khảo. Nếu cần đánh giá có độ tin
  cậy cao hơn, nên sử dụng các LLM mạnh hơn như GPT-4 hoặc Claude.

- 🧩 Phiên bản hiện tại chưa tích hợp vector database. Vì vậy
  `build_train_dataset.py` đang dùng câu trả lời gốc của MedQuAD làm context
  giả lập. Khi hoàn thiện RAG, chỉ cần thay phần này bằng các chunks được truy
  xuất từ vector database.