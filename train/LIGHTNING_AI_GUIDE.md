# Hướng dẫn chạy Fine-tuning Pipeline trên Lightning AI Studio

> **Khi nào dùng file này?**
> Khi Kaggle hết quota GPU hoặc bạn muốn train dài (>6 tiếng) mà vẫn có thể
> tắt máy đi ngủ — Lightning AI cho phép chạy Python script nền, không mất session.

---

## Tổng quan

| Đặc điểm | Chi tiết |
|-----------|----------|
| **Nền tảng** | [Lightning AI Studio](https://lightning.ai) |
| **GPU miễn phí** | T4 (79h), L40S (5h), A100 (3h), H100 (3h), H200 (2h) — reset hàng tháng |
| **Tắt browser** | ✅ Script `.py` chạy nền — tắt máy vẫn train tiếp |
| **Persistent Storage** | 50 GB — file được giữ khi Studio sleep |
| **Chiến lược** | Clone repo GitHub → chạy `python src/train.py` trong Terminal |

---

## Bước 1 — Tạo Studio mới

1. Truy cập [lightning.ai](https://lightning.ai) và đăng nhập (hoặc tạo tài khoản miễn phí).
2. Click **"New Studio"** → đặt tên (ví dụ: `nursing-home-finetune`).
3. **Chọn GPU:** Trong bước setup, chọn machine phù hợp:

   | GPU | Free hours/tháng | Khuyến nghị |
   |-----|-----------------|-------------|
   | **T4** | 79 giờ | ✅ **Khuyến nghị** — dư dả thời gian cho training |
   | **L40S** | 5 giờ | ⚠️ Nhanh hơn T4 ~3x, nhưng chỉ đủ train ngắn |
   | **A100** | 3 giờ | ❌ Quá ít, không đủ train Phi-3-3.8B |
   | **H100** | 3 giờ | ❌ Quá ít |
   | **H200** | 2 giờ | ❌ Quá ít |

   > **Khuyến nghị:** Chọn **T4** (79 giờ free) — đủ thoải mái cho training Phi-3-3.8B (~9 tiếng).
   > Nếu muốn train nhanh hơn và chấp nhận rủi ro hết giờ, chọn **L40S** (5 giờ, nhanh ~3x).

4. Click **"Start"** để khởi động Studio.

---

## Bước 2 — Clone repo & cài thư viện

Mở **Terminal** trong Studio (không dùng Notebook) và chạy từng lệnh:

```bash
# Clone repository từ GitHub
git clone -b TangTheToan https://github.com/internvietridao/MockProject_062026_NhomAI.git ~/project

# Di chuyển vào thư mục train
cd ~/project/train

# Cài đặt thư viện
pip install -r requirements.txt
```

> **Lưu ý:** Thư mục `~/` (home directory) trên Lightning AI được **persistent** —
> dữ liệu được giữ ngay cả khi Studio sleep hoặc restart.

---

## Bước 3 — Tạo file `.env`

Lightning AI không có Kaggle Secrets, nên tạo file `.env` thủ công:

```bash
cd ~/project/train

# Tạo file .env với HF_TOKEN của bạn
cat > .env << 'EOF'
HF_TOKEN=hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
EOF
```

> **Cách lấy HF_TOKEN:**
> 1. Vào [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)
> 2. Tạo token loại **Write** (nếu muốn push model lên Hub)
> 3. Copy token và thay vào dòng `HF_TOKEN=...` ở trên

> ⚠️ **Bảo mật:** KHÔNG commit file `.env` lên GitHub. File `.gitignore` đã loại trừ nó.

---

## Bước 4 — (Tùy chọn) Điều chỉnh cấu hình

Nếu muốn thay đổi cấu hình trước khi train, sửa file `src/config.py`:

```bash
# Mở file config để xem/sửa
nano src/config.py
```

**Các tham số thường muốn thay đổi:**

```python
# === ModelConfig ===
model_id = "unsloth/Phi-3-mini-4k-instruct-bnb-4bit"  # Model cần train

# === DataConfig ===
max_seq_length = 2048   # Giảm xuống 1024 nếu bị OOM (Out of Memory)

# === TrainConfig ===
num_train_epochs = 1
per_device_train_batch_size = 2   # Giảm xuống 1 nếu bị OOM
gradient_accumulation_steps = 8
save_steps = 200                  # Lưu checkpoint mỗi 200 steps
push_to_hub = False               # Đổi True nếu muốn upload lên HF Hub
hub_model_id = None               # Đổi thành "username/model-name" nếu push
```

> **Tip cho Lightning AI:** Nếu dùng L40S hoặc A100 (hỗ trợ bfloat16 tốt hơn T4),
> bạn có thể đổi `fp16 = False` và `bf16 = True` trong `TrainConfig` để ổn định hơn.

---

## Bước 5 — Chạy Training (QUAN TRỌNG)

### 5a. Chạy bằng `nohup` — Có thể tắt browser đi ngủ ✅

```bash
cd ~/project/train

# Chạy training nền với nohup, log ghi vào file
nohup python src/train.py > training.log 2>&1 &

# Ghi lại PID để theo dõi sau
echo $!
```

**Giải thích:**
- `nohup` → giữ process chạy khi đóng terminal/browser
- `> training.log 2>&1` → ghi toàn bộ output vào file `training.log`
- `&` → chạy nền (background)

> 🎉 **Sau khi chạy lệnh trên, bạn có thể tắt browser và đi ngủ!**
> Script sẽ tiếp tục chạy trên cloud cho đến khi hoàn tất.

### 5b. Theo dõi tiến trình (khi quay lại)

```bash
# Xem log realtime
tail -f ~/project/train/training.log

# Hoặc xem 50 dòng cuối
tail -50 ~/project/train/training.log

# Kiểm tra process còn chạy không
ps aux | grep train.py
```

### 5c. (Cách thay thế) Chạy bằng `tmux` — Nâng cao hơn

```bash
# Tạo session tmux mới
tmux new -s training

# Chạy training bình thường (thấy log realtime)
cd ~/project/train
python src/train.py

# Để thoát mà KHÔNG dừng training: nhấn Ctrl+B, rồi nhấn D
# Để quay lại session sau:
tmux attach -t training
```

---

## Bước 6 — Kiểm tra kết quả sau khi train xong

```bash
cd ~/project/train

# Kiểm tra các file output đã tạo
ls -la outputs_Phi-3-3.8B/

# Xem kết quả evaluation
python -c "
import pandas as pd
results = pd.read_csv('outputs_Phi-3-3.8B/evaluation_results.csv')
print(f'Tổng số mẫu đánh giá: {len(results)}')
print(f'')
print(f'Kết quả trung bình:')
print(f'  ROUGE-1: {results[\"rouge1\"].mean():.4f}')
print(f'  ROUGE-2: {results[\"rouge2\"].mean():.4f}')
print(f'  ROUGE-L: {results[\"rougeL\"].mean():.4f}')
print(f'  BLEU:    {results[\"bleu\"].mean():.4f}')
"
```

---

## Bước 7 — Tải output về máy local

### Cách 1: Nén & tải qua giao diện Lightning AI (Đơn giản nhất) ✅

```bash
cd ~/project/train

# Nén toàn bộ thư mục output thành 1 file zip
zip -r ~/lora_adapter_phi3.zip outputs_Phi-3-3.8B/
```

Sau đó:
1. Mở **File Browser** trong Lightning AI Studio (panel bên trái).
2. Điều hướng đến thư mục Home (`~/`).
3. Tìm file `lora_adapter_phi3.zip`.
4. **Click chuột phải** → **Download** để tải về máy local.

### Cách 2: Push lên Hugging Face Hub (Khuyến nghị cho chia sẻ nhóm) ✅

Sửa config trước khi train hoặc chạy thủ công sau khi train:

```bash
cd ~/project/train

python -c "
from huggingface_hub import HfApi
import os
from dotenv import load_dotenv

load_dotenv()
api = HfApi(token=os.environ['HF_TOKEN'])

# Thay 'your-username/nursing-home-phi3-lora' bằng repo của bạn
api.upload_folder(
    folder_path='outputs_Phi-3-3.8B',
    repo_id='your-username/nursing-home-phi3-lora',
    repo_type='model',
    create_pr=False,
)
print('Upload hoàn tất!')
"
```

### Cách 3: Tải qua `scp` từ Terminal local (Nâng cao)

Lightning AI Studio hỗ trợ SSH. Trên máy local:

```bash
# Cài Lightning AI CLI (chỉ cần chạy 1 lần)
pip install lightning

# Login
lightning login

# Copy file về local
lightning cp studio:nursing-home-finetune:~/project/train/outputs_Phi-3-3.8B ./outputs_Phi-3-3.8B
```

---

## Xử lý sự cố thường gặp

### ❌ Out of Memory (OOM)

Nếu gặp lỗi CUDA OOM, giảm dần theo thứ tự ưu tiên:

```python
# Trong src/config.py → DataConfig
max_seq_length = 1024          # Giảm từ 2048 → 1024

# Trong src/config.py → TrainConfig
per_device_train_batch_size = 1   # Giảm từ 2 → 1
gradient_accumulation_steps = 16  # Tăng lên để giữ effective batch size
```

### ❌ Studio tự sleep giữa chừng

Lightning AI Studio tự sleep sau 10 phút **không có process hoạt động**.
Nếu script đang chạy (qua `nohup` hoặc `tmux`), Studio sẽ **không sleep**.

Nếu Studio sleep bất ngờ:
1. Mở lại Studio → nó sẽ **tự resume** về trạng thái trước đó.
2. Kiểm tra xem process có còn chạy: `ps aux | grep train.py`
3. Nếu process đã tắt → chạy lại `python src/train.py` — code tự động detect checkpoint và **resume training**.

### ❌ Hết credit giữa chừng

- Checkpoint được lưu mỗi 200 steps (cấu hình `save_steps` trong `TrainConfig`).
- Khi có thêm credit, chạy lại `python src/train.py` → tự động resume từ checkpoint mới nhất.
- Hoặc tải checkpoint về và chuyển sang Kaggle khi quota reset.

---

## So sánh nhanh: Lightning AI vs Kaggle vs Colab

| Tiêu chí | Lightning AI | Kaggle | Google Colab |
|----------|-------------|--------|-------------|
| **Tắt browser** | ✅ Script chạy nền | ✅ Save Version | ❌ Mất session |
| **GPU miễn phí** | T4, L40S, A100, H100, H200 | T4 x2, P100 | T4 |
| **Quota/tháng** | 79h T4 (hoặc 5h L40S) | 30h GPU/tuần | ~4-8h liên tục |
| **Persistent storage** | ✅ 50 GB | ✅ (output) | ❌ |
| **Resume checkpoint** | ✅ Tự động | ✅ Cần mount | ❌ Khó |
| **Terminal chạy script** | ✅ Native | ⚠️ Chỉ Notebook | ⚠️ Chỉ Notebook |

---

## Checklist nhanh

- [ ] Tạo tài khoản Lightning AI
- [ ] Tạo Studio mới, chọn GPU (khuyến nghị L40S)
- [ ] Clone repo & cài thư viện
- [ ] Tạo file `.env` với `HF_TOKEN`
- [ ] (Tùy chọn) Sửa `config.py` nếu cần
- [ ] Chạy `nohup python src/train.py > training.log 2>&1 &`
- [ ] Tắt browser đi ngủ 😴
- [ ] Quay lại kiểm tra `training.log`
- [ ] Tải output về local (zip + download hoặc push HF Hub)
