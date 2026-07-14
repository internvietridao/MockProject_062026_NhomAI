# Medical Chatbot Fine-tuning Pipeline

Fine-tune LoRA cho chatbot hỏi-đáp y tế, base model `Qwen/Qwen2.5-0.5B-Instruct`.

---

## 📂 Train / Validation / Test split

`pipeline/build_train_dataset.py` đọc dữ liệu gốc từ `data/final_train_dataset.json`, xáo trộn (dùng `SPLIT_SEED` trong `src/config.py`
để mỗi lần chạy ra cùng kết quả), rồi chia theo:

- `TRAIN_RATIO = 0.7`
- `VAL_RATIO = 0.15`
- `TEST_RATIO = 0.15`

Các file được tạo trong `output/`:

- 📘 **train.jsonl**: fine-tune model (`pipeline/train.py`).
- 📗 **val.jsonl**: theo dõi validation loss trong lúc train (eval theo step,
  không phải theo epoch) + dùng cho early stopping. Không tham gia cập nhật
  trọng số.
- 📕 **test.jsonl**: tập model chưa từng thấy lúc train, giữ nguyên trường thô
  `{question, answer}` — dùng ở 2 bước đánh giá cuối (ROUGE/BLEU trong
  `train.py`, và LLM Judge trong `pipeline/evaluate.py`).

`train.jsonl` / `val.jsonl` lưu theo định dạng chat `messages`, sẵn sàng cho
`SFTTrainer`.

---

## 🔍 Bật / tắt RAG

Mặc định `USE_RAG=False` (chưa nối vector database thật). Bật bằng:

```bash
MEDQUAD_USE_RAG=1 python -m pipeline.build_train_dataset
```

---

## 🚀 Cách chạy

```bash
pip install -r requirements.txt

# 1. Đặt final_train_dataset.json vào thư mục data/

# 2. Tạo train/validation/test
python -m pipeline.build_train_dataset

# 3. Fine-tune LoRA (train.py TỰ ĐỘNG chạy luôn bước ROUGE/BLEU sau khi train xong)
python -m pipeline.train

# 4. Demo chatbot
python -m pipeline.chat

# 5. Đánh giá bằng LLM Judge (đọc CSV do bước 3 xuất ra)
python -m pipeline.evaluate
```

Chạy bằng `python -m pipeline.<script_name>` (không phải
`python pipeline/<script_name>.py`) để Python nhận đúng thư mục gốc project.

---

## 🧪 Quy trình đánh giá — 2 bước tách rời

Khác với các phiên bản trước, đánh giá được chia làm **2 bước độc lập**:

### Bước 1 — ROUGE/BLEU (chạy TỰ ĐỘNG ngay trong `pipeline/train.py`)

Sau khi train xong và lưu checkpoint tốt nhất, `train.py` gọi
`save_predictions_csv()` (trong `src/evaluation.py`):

- Lấy **100 mẫu đầu tiên** của `test.jsonl` (mặc định `max_samples=100`,
  không phải toàn bộ tập test — vì generate tuần tự từng mẫu khá chậm).
- Sinh câu trả lời bằng model vừa train, tính ROUGE-1/2/L + BLEU cho từng mẫu.
- Xuất ra `output/evaluation_results.csv` (cột: `question, reference,
  prediction, rouge1, rouge2, rougeL, bleu`).
- Ghi thêm 1 dòng tổng hợp vào `output/training_summary.csv` (model,
  rouge1/2/L, bleu, perplexity, train_loss, val_loss, mean_token_accuracy) —
  dễ so sánh giữa các lần train.

⚠️ BLEU tính theo geometric mean 1-4 gram nên rất dễ về gần 0 với câu trả lời
bị paraphrase (không trùng nguyên văn 4-gram liên tiếp) — không có nghĩa là
model kém, chỉ là BLEU quá khắt khe với kiểu dữ liệu này. ROUGE đáng tin hơn
trong trường hợp này.

⚠️ Vì chỉ chạy trên 100/1733 mẫu, con số này chỉ mang tính **ước lượng nhanh
(proxy)**, không đại diện đầy đủ cho toàn bộ tập test. Muốn số đáng tin hơn để
báo cáo chính thức, cần tăng `max_samples` trong lời gọi `save_predictions_csv`
(đánh đổi bằng thời gian chạy lâu hơn).

### Bước 2 — LLM Judge (`pipeline/evaluate.py`, chạy riêng, thủ công)

Đọc CSV từ bước 1, dùng LLM giám khảo **tách biệt** với model đang được đánh
giá để chấm điểm ngữ nghĩa (không chỉ so khớp từ vựng như ROUGE/BLEU):

- Ưu tiên gọi qua **API** (`MEDQUAD_JUDGE_API_KEY`, endpoint kiểu
  OpenAI-compatible, mặc định model `gpt-4o-mini`) — nhanh, không tốn VRAM.
- Nếu không có API key, fallback về Prometheus 2 (`prometheus-eval/prometheus-7b-v2.0`)
  chạy cục bộ, mặc định load 4-bit (`JUDGE_LOAD_IN_4BIT=1`) để vừa GPU free
  tier (Colab/Kaggle T4).

Tách 2 model (model bị đánh giá vs. model giám khảo) để tránh **self-preference
bias** — model có xu hướng tự chấm cao câu trả lời của chính mình nếu dùng
chung 1 model.

---

## ⚙️ Đổi model hoặc đường dẫn

Hầu hết thiết lập nằm trong `src/config.py`, có thể ghi đè bằng biến môi trường:

```bash
MEDQUAD_BASE_MODEL="Qwen/Qwen2.5-1.5B-Instruct" python -m pipeline.train
MEDQUAD_OUTPUT_DIR="/kaggle/working/output" python -m pipeline.train
MEDQUAD_JUDGE_API_KEY="sk-..." python -m pipeline.evaluate
```

---

## 🏆 Chạy trên Kaggle

Mở `main_pipeline.ipynb`, chạy tuần tự các cell theo thứ tự
build_train_dataset → train → (chat demo) → evaluate.

Lưu ý: Kaggle free tier giới hạn thời gian GPU/phiên khá ngắn — nếu train +
inference ROUGE/BLEU đang chạy dở mà hết giờ, checkpoint model (`output_model/`)
vẫn đã được lưu an toàn từ trước đó, nhưng `evaluation_results.csv` chỉ được
ghi ra **sau khi chạy xong toàn bộ vòng lặp inference**, nên có thể mất nếu bị
ngắt giữa chừng bước này.