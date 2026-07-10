# LLM Fine-tuning Component

Thư mục này chứa toàn bộ mã nguồn và cấu hình phục vụ cho việc Fine-tune mô hình ngôn ngữ lớn (LLM) để xây dựng trợ lý AI chuyên ngành Quản lý Viện dưỡng lão tại Mỹ.

---

## 📂 Cấu trúc thư mục

```
train/
├── src/                      # Thư mục mã nguồn chính (Python packages)
│   ├── __init__.py           # Đánh dấu package
│   ├── config.py             # Cấu hình tập trung (Model, LoRA, Data, Training)
│   ├── data_utils.py         # Xử lý dữ liệu (Prompt format Alpaca/ChatML, Stratified Split)
│   ├── model_utils.py        # Tải Base Model, QLoRA 4-bit, tự động dò target_modules
│   ├── evaluation.py         # Đo đạc metrics (ROUGE, BLEU) và xuất CSV kết quả
│   └── train.py              # Script thực thi chính (kết nối pipeline)
├── data/                     # Thư mục chứa dữ liệu huấn luyện
│   └── final_train_dataset.json  # Bộ dữ liệu Q&A sạch (37,172 mẫu)
├── .env.example              # Template chứa các biến môi trường nhạy cảm
├── .gitignore                # Cấu hình ẩn các file cache, checkpoints, và token bảo mật
├── requirements.txt          # Danh sách thư viện Python cần thiết
├── KAGGLE_NOTEBOOK.md        # Hướng dẫn copy-paste code chạy trên Kaggle
└── README.md                 
```

---

## ⚙️ Chi tiết các Module

### 1. Cấu hình tập trung (`src/config.py`)
Gom toàn bộ tham số vào các `dataclasses` để dễ dàng quản lý:
*   `ModelConfig`: Model ID (`model_id`), kiểu dữ liệu (`torch_dtype`), thiết bị chạy (`device_map`).
*   `LoraConfig`: Cấu hình Adapter LoRA (Rank `r`, `lora_alpha`, `lora_dropout`, `target_modules`).
*   `DataConfig`: Tỉ lệ chia tập dữ liệu (`train_split_ratio`, `val_split_ratio`), `system_prompt`, `prompt_style` (Alpaca/ChatML).
*   `TrainConfig`: Tham số huấn luyện (learning rate, batch size, gradient accumulation, optimizer `paged_adamw_8bit` tối ưu VRAM, HF Hub upload).

### 2. Tiền xử lý dữ liệu (`src/data_utils.py`)
*   **Prompt Formatting**: Chuyển đổi dữ liệu thô dạng Q&A sang định dạng Prompt mong muốn (Alpaca hoặc ChatML).
*   **Stratified Split**: Chia dữ liệu thành 3 tập độc lập **Train (80%) / Validation (10%) / Test (10%)** phân tầng (stratify) theo cột `source` để đảm bảo phân phối nguồn dữ liệu đồng đều ở các tập.

### 3. Tải & Cấu hình Model (`src/model_utils.py`)
*   Thiết lập BitsAndBytes 4-bit phục vụ QLoRA.
*   Tự động dò tìm (auto-detect) các lớp tuyến tính (`nn.Linear`) của model được chọn để gán Adapter LoRA chuẩn xác mà không cần cấu hình thủ công cho từng dòng model khác nhau.

### 4. Đánh giá chất lượng (`src/evaluation.py`)
*   Tính toán các chỉ số `ROUGE-1/2/L` và `BLEU` bằng thư viện `evaluate` của HuggingFace.
*   Chạy sinh thử nghiệm (inference) trên tập **Test** sau khi train xong và xuất kết quả ra file `outputs/evaluation_results.csv` (lưu cả question, reference, prediction và điểm số chi tiết cho từng câu hỏi) nhằm chuẩn bị cho bước đánh giá nâng cao LLM-as-a-judge.

---

## 🚀 Hướng dẫn thực thi

### Cách 1: Chạy trên Kaggle (GPU miễn phí - Khuyến nghị)
Xem chi tiết các bước thiết lập và copy-paste code tại file [KAGGLE_NOTEBOOK.md](file:///e:/AI_VTD/MockProject_062026_NhomAI/train/KAGGLE_NOTEBOOK.md).

### Cách 2: Chạy ở máy Local (Yêu cầu GPU NVIDIA có CUDA)
1.  Cài đặt các thư viện:
    ```bash
    pip install -r requirements.txt
    ```
2.  Sao chép file `.env.example` thành `.env` và điền token Hugging Face của bạn:
    ```bash
    cp .env.example .env
    ```
3.  Chạy script huấn luyện:
    ```bash
    python src/train.py
    ```
4.  Kết quả adapter sẽ được lưu tại thư mục `outputs/`, file CSV đánh giá chất lượng được lưu tại `outputs/evaluation_results.csv`.
