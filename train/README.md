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
│   ├── evaluate_llm_judge.py # Script đánh giá nâng cao LLM-as-a-judge sử dụng API (Gemini/OpenAI)
│   └── train.py              # Script thực thi chính (kết nối pipeline)
├── data/                     # Thư mục chứa dữ liệu huấn luyện
│   └── final_train_dataset.json  # Bộ dữ liệu Q&A sạch (37,172 mẫu)
├── outputs/                  # Thư mục lưu kết quả sau khi train (sinh ra tự động hoặc tải về)
│   ├── checkpoint-1000/      # Thư mục lưu checkpoint bước 1000
│   ├── checkpoint-1859/      # Thư mục lưu checkpoint bước 1859 (cuối)
│   ├── adapter_config.json   # Cấu hình chi tiết LoRA adapter
│   ├── adapter_model.safetensors # Trọng số của LoRA adapter sau huấn luyện
│   ├── chat_template.jinja   # File mẫu prompt chat định dạng ChatML
│   ├── evaluation_results.csv # Bảng kết quả chạy thử nghiệm và tính điểm ROUGE, BLEU
│   ├── judge_prompt.md       # Prompt chi tiết phục vụ copy-paste lên các Chatbot Web UI để đánh giá CSV
│   ├── tokenizer.json        # Dữ liệu tokenizer cho mô hình
│   ├── tokenizer_config.json # Cấu hình tokenizer tương ứng
│   └── training_args.bin     # Tham số huấn luyện được lưu dưới dạng binary
├── .env.example              # Template chứa các biến môi trường nhạy cảm
├── .gitignore                # Cấu hình ẩn các file cache, checkpoints, và token bảo mật
├── requirements.txt          # Danh sách thư viện Python cần thiết
├── KAGGLE_NOTEBOOK.md        # Hướng dẫn sao chép code để chạy huấn luyện trên Kaggle
└── README.md                 # Hướng dẫn chi tiết sử dụng của module
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

## 📊 Kết quả huấn luyện thực tế

Quá trình fine-tune được thực hiện với mô hình nền `Qwen/Qwen2.5-0.5B-Instruct` sử dụng QLoRA 4-bit trên bộ dữ liệu 37,172 cặp Q&A. Dưới đây là thông số và kết quả đánh giá thực tế trên tập kiểm thử (100 mẫu ngẫu nhiên):

### 1. Cấu hình huấn luyện
- **Base Model:** `Qwen/Qwen2.5-0.5B-Instruct`
- **Phương pháp:** QLoRA 4-bit (`bitsandbytes`)
- **LoRA Hyperparameters:** $r = 16$, $\alpha = 32$, Dropout = 0.05
- **Target Modules:** Tất cả các lớp tuyến tính (`q_proj`, `k_proj`, `v_proj`, `o_proj`, `gate_proj`, `up_proj`, `down_proj`)
- **Tham số tối ưu:** Learning Rate = $2e-4$, Batch Size = 2, Gradient Accumulation Steps = 8 (Effective Batch Size = 16), Epochs = 1, Optimizer = `paged_adamw_8bit`

### 2. Các chỉ số đánh giá trung bình
Đo lường trên tập kiểm thử (Test Set - 100 samples) bằng cách so khớp từ ngữ giữa câu trả lời mẫu (Reference) và câu sinh ra từ mô hình (Prediction):

| Chỉ số | Kết quả | Ý nghĩa & Phân tích |
| :--- | :--- | :--- |
| **ROUGE-1** | **33.51%** | Độ trùng khớp n-gram đơn (từ đơn) giữa Prediction và Reference. |
| **ROUGE-2** | **15.05%** | Độ trùng khớp n-gram đôi (cụm 2 từ) giữa hai văn bản. |
| **ROUGE-L** | **27.25%** | Độ trùng khớp chuỗi con chung dài nhất (Longest Common Subsequence). |
| **BLEU** | **0.00%** | Điểm số BLEU-4 ở cấp độ câu đơn lẻ rất khắt khe và thường trả về 0 nếu không có cụm 4-gram nào trùng khớp tuyệt đối mà không có cơ chế làm trơn (smoothing). Do đó, điểm số này không phản ánh đầy đủ chất lượng nội dung y khoa, cần kết hợp đánh giá **LLM-as-a-judge**. |

### 3. Cấu trúc thư mục đầu ra `outputs/`
Sau khi chạy hoàn tất, các tệp tin sau được sinh ra trong thư mục `outputs/`:
- `adapter_config.json`: Cấu hình chi tiết của adapter LoRA.
- `adapter_model.safetensors`: Trọng số LoRA đã được tối ưu hóa sau khi huấn luyện.
- `tokenizer.json` & `tokenizer_config.json`: Cấu hình bộ mã hóa từ vựng tương thích.
- `chat_template.jinja`: Template định dạng prompt hội thoại dạng ChatML.
- `evaluation_results.csv`: Bảng kết quả so sánh chi tiết câu hỏi, câu mẫu và câu dự đoán kèm điểm số n-gram cho từng dòng.

---

## 🚀 Hướng dẫn thực thi

### Cách 1: Chạy trên Kaggle (GPU miễn phí - Khuyến nghị)
Xem chi tiết các bước thiết lập và copy-paste code tại file [KAGGLE_NOTEBOOK.md](file:///e:/AI_VTD/MockProject_062026_NhomAI/train/KAGGLE_NOTEBOOK.md).
Link Notebook mẫu: [https://www.kaggle.com/code/fthetoan/llm-nhms/notebook](https://www.kaggle.com/code/fthetoan/llm-nhms)

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
