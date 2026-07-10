# Hướng dẫn tạo Kaggle Notebook cho Fine-tuning Pipeline

> File này mô tả chính xác nội dung từng cell cần tạo trên Kaggle Notebook.
> Sao chép từng block code vào các cell tương ứng trên Kaggle.

---

## Cell 1 (Markdown) — Tiêu đề

```markdown
# Nursing Home AI Chatbot — LLM Fine-tuning Pipeline

Fine-tune mô hình LLM (Llama, Mistral, Gemma...) trên bộ dữ liệu y tế chuyên ngành
Nursing Home bằng QLoRA 4-bit. Pipeline tự động hóa hoàn toàn từ data → train → evaluate → upload.

**Chiến lược:** Code `.py` được quản lý trên GitHub, notebook này chỉ là UI Controller.
```

---

## Cell 2 (Code) — Clone repo & cài thư viện

```python
# Clone repository từ GitHub với nhánh cụ thể
!git clone -b TangTheToan https://github.com/internvietridao/MockProject_062026_NhomAI.git /kaggle/working/project

# Di chuyển vào thư mục train
%cd /kaggle/working/project/train

# Cài đặt thư viện từ requirements.txt
!pip install -q -r requirements.txt
```

---

## Cell 3 (Code) — Tạo file `.env` an toàn từ Kaggle Secrets

```python
# Sử dụng Kaggle Secrets để lấy token — KHÔNG gõ token trực tiếp vào code!
# Trước khi chạy cell này, hãy:
#   1. Vào Kaggle → Add-ons → Secrets
#   2. Thêm secret key: HF_TOKEN với giá trị là Hugging Face Write Token
#   3. (Tùy chọn) Thêm: WANDB_API_KEY

from kaggle_secrets import UserSecretsClient

secrets = UserSecretsClient()

# Lấy token từ Kaggle Secrets
hf_token = secrets.get_secret("HF_TOKEN")
wandb_key = secrets.get_secret("WANDB_API_KEY") if "WANDB_API_KEY" in dir(secrets) else ""

# Ghi file .env
with open(".env", "w") as f:
    f.write(f"HF_TOKEN={hf_token}\n")
    if wandb_key:
        f.write(f"WANDB_API_KEY={wandb_key}\n")

print("✅ File .env đã tạo thành công (token được ẩn)")
```

---

## Cell 4 (Code) — (Tùy chọn) Tùy chỉnh cấu hình trước khi train

```python
# Nếu muốn thay đổi cấu hình, sửa trực tiếp file config.py:
#
# Ví dụ: Đổi model sang Mistral
# !sed -i 's/unsloth\/Llama-3.2-1B-Instruct/mistralai\/Mistral-7B-Instruct-v0.3/g' src/config.py
#
# Ví dụ: Bật push_to_hub
# !sed -i 's/push_to_hub: bool = False/push_to_hub: bool = True/g' src/config.py
# !sed -i 's/hub_model_id: Optional\[str\] = None/hub_model_id: Optional[str] = "your-username\/nursing-home-chatbot-lora"/g' src/config.py
#
# Hoặc giảm max_seq_length nếu OOM:
# !sed -i 's/max_seq_length: int = 1024/max_seq_length: int = 512/g' src/config.py

print("ℹ️ Cấu hình mặc định — bỏ comment các dòng trên nếu cần thay đổi")
```

---

## Cell 5 (Code) — Chạy Pipeline

```python
# Kích hoạt toàn bộ Fine-tuning Pipeline
!python src/train.py
```

---

## Cell 6 (Code) — Xem kết quả evaluation

```python
import pandas as pd

# Đọc file kết quả evaluation
results = pd.read_csv("outputs/evaluation_results.csv")

print(f"Tổng số mẫu đánh giá: {len(results)}")
print(f"\n📊 Kết quả trung bình:")
print(f"  ROUGE-1: {results['rouge1'].mean():.4f}")
print(f"  ROUGE-2: {results['rouge2'].mean():.4f}")
print(f"  ROUGE-L: {results['rougeL'].mean():.4f}")
print(f"  BLEU:    {results['bleu'].mean():.4f}")

# Xem 5 mẫu đầu tiên
print(f"\n📝 Mẫu dự đoán:")
results.head()
```

---

## Cell 7 (Code) — (Tùy chọn) Download adapter về máy local

```python
# Nén adapter để download
!zip -r /kaggle/working/lora_adapter.zip outputs/

from IPython.display import FileLink
FileLink("/kaggle/working/lora_adapter.zip")
```

---

## Cấu hình Kaggle Notebook

| Cấu hình | Giá trị |
|-----------|---------|
| **Accelerator** | GPU T4 x2 (hoặc P100) |
| **Persistence** | Files |
| **Internet** | ON (cần để download model & push to hub) |
| **Kaggle Secrets** | Thêm `HF_TOKEN` |
