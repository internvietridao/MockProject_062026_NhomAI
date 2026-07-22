"""
src/rag_bridge.py
------------------
Cầu nối gọi retrieve_context() từ project RAG riêng (Embedding_RAG/ của
thành viên khác) mà KHÔNG bị đụng độ tên module.

CẤU HÌNH:
  Set biến môi trường MEDQUAD_RAG_DIR trỏ đúng vào thư mục model RAG muốn
  dùng, ví dụ:
      export MEDQUAD_RAG_DIR=/path/to/Embbeding_RAG/nomic-embed-text-v1.5
"""

import os
import sys
import importlib
from pathlib import Path

from src.config import BASE_DIR

_DEFAULT_RAG_DIR = BASE_DIR.parent / "Embbeding_RAG" / "nomic-embed-text-v1.5"
RAG_PROJECT_DIR = Path(os.environ.get("MEDQUAD_RAG_DIR", str(_DEFAULT_RAG_DIR))).resolve()

_cached_retrieve_fn = None
_cached_rag_config = None
_warned_non_cosine = False


def _load_retrieve_context_fn():
    """Import retrieval.py + config.py từ RAG project 1 LẦN DUY NHẤT, cách
    ly sys.path an toàn (thêm rồi xoá ngay). Trả về (retrieve_context_fn,
    rag_config_module)."""
    global _cached_retrieve_fn, _cached_rag_config
    if _cached_retrieve_fn is not None:
        return _cached_retrieve_fn, _cached_rag_config

    test_vector_db_dir = RAG_PROJECT_DIR / "test_vector_db"
    if not test_vector_db_dir.exists():
        raise FileNotFoundError(
            f"Không tìm thấy {test_vector_db_dir}. "
            f"Kiểm tra lại biến môi trường MEDQUAD_RAG_DIR có trỏ đúng vào "
            f"thư mục model RAG (vd .../Embbeding_RAG/nomic-embed-text-v1.5) không."
        )

    paths_to_add = [str(test_vector_db_dir)]
    inserted = []
    try:
        for stale in ("config", "retrieval"):
            sys.modules.pop(stale, None)

        for p in paths_to_add:
            if p not in sys.path:
                sys.path.insert(0, p)
                inserted.append(p)

        # retrieval.py tự thêm parent dir (RAG_PROJECT_DIR) vào sys.path và
        # `import config` bên trong nó -- không cần mình làm thay.
        retrieval_module = importlib.import_module("retrieval")
        _cached_retrieve_fn = retrieval_module.retrieve_context
        # config.py của RAG project (đã bị retrieval.py import ở trên rồi,
        # nên giờ chỉ cần lấy lại từ sys.modules, KHÔNG import lại lần nữa).
        _cached_rag_config = sys.modules.get("config")

        print(
            f"[rag_bridge] Đã load retrieval module từ: {RAG_PROJECT_DIR}\n"
            f"[rag_bridge] RETRIEVAL_MODE = {getattr(_cached_rag_config, 'RETRIEVAL_MODE', '?')} | "
            f"SIMILARITY_THRESHOLD = {getattr(_cached_rag_config, 'SIMILARITY_THRESHOLD', '?')}"
        )
    finally:
        for p in inserted:
            if p in sys.path:
                sys.path.remove(p)

    return _cached_retrieve_fn, _cached_rag_config


def get_context_texts(question: str, top_k: int = 3) -> list[str]:
    """
    [GIỮ LẠI ĐỂ TƯƠNG THÍCH NGƯỢC -- không lọc theo similarity]
    Trả về danh sách text_content của top_k chunks, KHÔNG áp threshold.
    Dùng get_context_with_similarity() nếu muốn lọc context không liên quan.
    """
    retrieve_context, _ = _load_retrieve_context_fn()
    results = retrieve_context(question, top_k=top_k)
    return [r["text_content"] for r in results]


def get_context_with_similarity(
    question: str,
    top_k: int = 3,
    similarity_threshold: float = None,
    relative_threshold: float = 0.5,
) -> dict:
    """
    Retrieve top-k contexts và tự động lọc theo mức độ liên quan.

    - Cosine: sử dụng ngưỡng similarity tuyệt đối (`similarity_threshold`).
    - BM25/Hybrid: sử dụng ngưỡng tương đối (`relative_threshold`), tính theo
    tỷ lệ điểm của mỗi context so với context có điểm cao nhất trong top-k.
    Các context dưới ngưỡng sẽ bị loại.

    Returns:
        {
            "used_contexts": Context được đưa vào prompt,
            "raw_contexts": Tất cả context retrieve được,
            "scores": Điểm retrieval gốc,
            "similarity_pct": Similarity tuyệt đối (chỉ Cosine),
            "relative_pct": Similarity tương đối (chỉ BM25/Hybrid),
            "rag_used": Có sử dụng context hay không,
            "retrieval_mode": Chế độ retrieval hiện tại,
        }
    """
    retrieve_context, rag_config = _load_retrieve_context_fn()
    retrieval_mode = getattr(rag_config, "RETRIEVAL_MODE", "cosine")

    results = retrieve_context(question, top_k=top_k)
    raw_contexts = [r["text_content"] for r in results]
    scores = [r["score"] for r in results]

    similarity_pct = [None] * len(raw_contexts)
    relative_pct = [None] * len(raw_contexts)

    if retrieval_mode == "cosine":
        threshold = (
            similarity_threshold
            if similarity_threshold is not None
            else getattr(rag_config, "SIMILARITY_THRESHOLD", 0.70)
        )
        # Chroma cosine distance -> similarity = 1 - distance, clip về 0..1
        similarity_pct = [max(0.0, min(1.0, 1.0 - s)) * 100 for s in scores]
        used_contexts = [
            ctx for ctx, pct in zip(raw_contexts, similarity_pct)
            if pct >= threshold * 100
        ]
    else:
        # bm25/hybrid: KHÔNG có thang cố định giữa các câu hỏi -- nhưng vẫn
        # tự động đo được % TƯƠNG ĐỐI trong chính top-k này (không cần người dùng tự đoán số).
        max_score = max(scores) if scores else 0.0
        if max_score > 0:
            relative_pct = [max(0.0, s / max_score) * 100 for s in scores]
        else:
            relative_pct = [0.0 for _ in scores]

        used_contexts = [
            ctx for ctx, pct in zip(raw_contexts, relative_pct)
            if pct >= relative_threshold * 100
        ]

    return {
        "used_contexts": used_contexts,
        "raw_contexts": raw_contexts,
        "scores": scores,
        "similarity_pct": similarity_pct,
        "relative_pct": relative_pct,
        "rag_used": len(used_contexts) > 0,
        "retrieval_mode": retrieval_mode,
    }