"""
config.py
---------
Cấu hình dùng chung cho toàn bộ pipeline (build data, train, chat, evaluate).
Gom hết đường dẫn + tên model vào 1 chỗ để tránh lệch cấu hình giữa các bước
(vd: train xong dùng model A nhưng chat.py lại load model B).

Đường dẫn được tính TƯƠNG ĐỐI theo vị trí file này (BASE_DIR = gốc project),
nên chạy được cả ở local, Colab (miễn đã mount + cd đúng vào thư mục project
trong Drive) lẫn Kaggle (miễn đã add project vào sys.path / Kaggle Dataset).

Có thể override bằng biến môi trường nếu cần (ví dụ đổi nơi lưu output khi
chạy trên Kaggle: MEDQUAD_OUTPUT_DIR=/kaggle/working/output).
"""

import os
from pathlib import Path

# Gốc project = thư mục cha của src/
BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = Path(os.environ.get("MEDQUAD_DATA_DIR", BASE_DIR / "data"))
OUTPUT_DIR = Path(os.environ.get("MEDQUAD_OUTPUT_DIR", BASE_DIR / "output"))

# ---- Dữ liệu ----
INPUT_FILE = DATA_DIR / "final_train_dataset.json"
TRAIN_FILE = OUTPUT_DIR / "train.jsonl"
VAL_FILE = OUTPUT_DIR / "val.jsonl"
TEST_FILE = OUTPUT_DIR / "test.jsonl"
TRAIN_SAMPLE_LIMIT = None  # số sample lấy từ final_train_dataset.json để build dataset

# Tỷ lệ chia train/val/test (phải cộng lại = 1.0)
TRAIN_RATIO = 0.7
VAL_RATIO = 0.15
TEST_RATIO = 0.15

# Seed cố định để chia tập lần nào cũng ra kết quả giống nhau (reproducible)
SPLIT_SEED = 42

# ---- RAG toggle ----
USE_RAG = os.environ.get("MEDQUAD_USE_RAG", "0") == "1"

# ---- Model ----
BASE_MODEL_NAME = os.environ.get("MEDQUAD_BASE_MODEL", "Qwen/Qwen2.5-0.5B-Instruct")
ADAPTER_DIR = OUTPUT_DIR / "output_model"

# ---- Sinh dự đoán ra CSV (ROUGE/BLEU) ----
# Sau khi train xong, chạy inference thật trên tập TEST rồi lưu CSV
# (question, reference, prediction, rouge1/2/L, bleu). CSV này dùng làm input cho bước LLM Judge ở evaluate.py 
# -- KHÔNG generate lại câu trả lời lần 2 ở đó nữa.
PREDICTIONS_CSV = OUTPUT_DIR / "evaluation_results.csv"

# Bảng tổng hợp 1 dòng cuối cùng: model, rouge1/2/L, bleu, perplexity,
# train_loss, val_loss, mean_token_accuracy -- dễ so sánh giữa các lần train.
SUMMARY_CSV = OUTPUT_DIR / "training_summary.csv"

SYSTEM_PROMPT = os.environ.get(
    "MEDQUAD_SYSTEM_PROMPT",
    "You are a helpful medical assistant. Answer the question accurately and concisely.",
)
# "chatml" khớp với chat template của Qwen2.5-Instruct. Đổi "alpaca" nếu base
# model khác dùng format instruction/response thay vì chat template.
PROMPT_STYLE = os.environ.get("MEDQUAD_PROMPT_STYLE", "chatml")

# ---- Đánh giá (RAGAs) ----
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"  # free, nhẹ

# Ưu tiên gọi giám khảo qua API (xem JUDGE_API_* bên dưới) -- nhanh và không
# tốn VRAM. Prometheus 2 cục bộ (local HF model) chỉ dùng làm PHƯƠNG ÁN DỰ
# PHÒNG khi không có JUDGE_API_KEY.
JUDGE_MODEL_NAME = os.environ.get("MEDQUAD_JUDGE_MODEL", "prometheus-eval/prometheus-7b-v2.0")
JUDGE_LOAD_IN_4BIT = os.environ.get("MEDQUAD_JUDGE_4BIT", "1") != "0"

# ---- Giám khảo qua API ----
JUDGE_API_BASE = os.environ.get("MEDQUAD_JUDGE_API_BASE", "https://api.openai.com/v1")
JUDGE_API_KEY = os.environ.get("MEDQUAD_JUDGE_API_KEY", "")
JUDGE_API_MODEL = os.environ.get("MEDQUAD_JUDGE_API_MODEL", "gpt-4o-mini")

# ---- Sinh câu trả lời ----
MAX_NEW_TOKENS_TRAIN_GEN = 300   # dùng khi generate answer cho eval
MAX_NEW_TOKENS_CHAT = 300        # dùng khi chat/inference thật