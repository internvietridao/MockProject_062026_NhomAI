import os
import json
import logging
import sys
from pathlib import Path
from typing import List, Dict
import numpy as np
from chromadb.utils import embedding_functions

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

# 1. CONFIGURATION & IMPORTS
sys.path.append(str(Path(__file__).resolve().parent.parent))
import config

VECTOR_DB_DIR = config.VECTOR_DB_DIR
COLLECTION_NAME = config.COLLECTION_NAME
EMBEDDING_MODEL_NAME = config.EMBEDDING_MODEL_NAME

TOP_K = config.TOP_K
LLM_PROVIDER = config.LLM_PROVIDER
LIGHTNING_API_URL = config.LIGHTNING_API_URL
LLM_MODEL_NAME = config.LLM_MODEL_NAME
LLM_API_KEY = config.LLM_API_KEY
OLLAMA_API_URL = config.OLLAMA_API_URL
SIMILARITY_THRESHOLD = config.SIMILARITY_THRESHOLD

sys.path.append(str(Path(__file__).resolve().parent))
try:
    from retrieval import retrieve_context
except ImportError:
    from .retrieval import retrieve_context

# 2. PROMPT TEMPLATE
RAG_PROMPT_TEMPLATE = """You are an intelligent AI nursing home management assistant. Answer the user's question DIRECTLY and ONLY based on the context provided below. If the context does not contain enough information, say "I don't know" and do not make up an answer.
---
CONTEXT:
{context}
---
QUESTION:
{question}
---
ANSWER:"""

# 3. LLM CONNECTOR LOGIC

def call_lightning_api(prompt: str) -> str:
    """Gọi REST API đến LLM fine-tuned Qwen-0.5B / Gemma-2B đang host trên Lightning AI Studio."""
    import requests
    
    if not LIGHTNING_API_URL or "8000-xxxx" in LIGHTNING_API_URL:
        logging.warning("⚠️ LIGHTNING_API_URL đang dùng URL mặc định (placeholder). Hãy cập nhật URL Public từ Lightning Studio vào config.py!")
        
    endpoint = f"{LIGHTNING_API_URL.rstrip('/')}/generate"
    payload = {
        "prompt": prompt,
        "max_new_tokens": 512,
        "temperature": 0.1,
        "top_p": 0.9
    }
    headers = {"Content-Type": "application/json"}
    
    try:
        logging.info(f"Đang gửi request tới Lightning AI API: {endpoint}")
        response = requests.post(endpoint, json=payload, headers=headers, timeout=60)
        response.raise_for_status()
        data = response.json()
        return data.get("answer", "").strip()
    except requests.exceptions.ConnectionError:
        logging.error(f"❌ Không thể kết lộ tới Lightning AI API tại: {endpoint}. Hãy đảm bảo Lightning Studio đang Bật và Port 8000 đã đặt ở chế độ Public!")
        raise ConnectionError(f"Lightning AI Connection Failed: {endpoint}")
    except Exception as e:
        logging.error(f"❌ Lỗi khi gọi API Lightning AI: {str(e)}")
        raise e

def call_ollama(prompt: str) -> str:
    import requests
    
    payload = {
        "model": LLM_MODEL_NAME,
        "prompt": prompt,
        "stream": False
    }
    try:
        response = requests.post(OLLAMA_API_URL, json=payload, timeout=45)
        response.raise_for_status()
        return response.json().get("response", "").strip()
    except requests.exceptions.ConnectionError:
        logging.error("Ollama connection failed! Please ensure Ollama desktop app is running.")
        raise ConnectionError(f"Cannot connect to Ollama at {OLLAMA_API_URL}.")
    except Exception as e:
        logging.error(f"Error calling local Ollama LLM: {str(e)}")
        raise e

def call_openai(prompt: str) -> str:
    import requests
    
    if not LLM_API_KEY:
        raise ValueError("OpenAI API Key is missing. Set OPENAI_API_KEY environment variable.")
        
    headers = {
        "Authorization": f"Bearer {LLM_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": LLM_MODEL_NAME,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1
    }
    try:
        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        logging.error(f"Error calling OpenAI API: {str(e)}")
        raise e

def call_mock_llm(prompt: str, retrieved_chunks: List[Dict]) -> str:
    if not retrieved_chunks:
        return "Tôi không tìm thấy thông tin phù hợp trong tài liệu."
        
    top_chunk = retrieved_chunks[0]
    content = top_chunk["text_content"]
    
    import re
    content_clean = re.sub(r"<!--.*?-->", "", content).strip()
    first_sentence = content_clean.splitlines()[0] if content_clean else ""
    if len(first_sentence) > 200:
        first_sentence = first_sentence[:197] + "..."
        
    mock_response = (
        f"[CÂU TRẢ LỜI GIẢ LẬP (Mock LLM: {LLM_MODEL_NAME})]\n"
        f"Dựa vào tài liệu tham khảo (File: {top_chunk['metadata']['source']}):\n"
        f"-> \"{first_sentence}\"\n\n"
        f"LƯU Ý: Đây là câu trả lời giả lập. Để nhận phản hồi thực tế từ Lightning AI Cloud API, "
        f"vui lòng khởi chạy FastAPI server trên Lightning AI Studio và cập nhật LIGHTNING_API_URL trong config.py."
    )
    return mock_response

# 4. RAG PIPELINE ORCHESTRATOR
def generate_rag_response(question: str) -> Dict:
    logging.info(f"RAG Pipeline: Processing question: '{question}'")
    
    try:
        retrieved_chunks = retrieve_context(
            question, 
            top_k=TOP_K,
            vector_db_dir=VECTOR_DB_DIR,
            collection_name=COLLECTION_NAME,
            embedding_model_name=EMBEDDING_MODEL_NAME
        )
        logging.info(f"Retrieved {len(retrieved_chunks)} relevant contexts.")
    except Exception as err:
        logging.error(f"Failed to retrieve context during RAG pipeline: {str(err)}")
        return {
            "answer": "Đã xảy ra lỗi khi tìm kiếm dữ liệu Vector.",
            "question": question,
            "sources": []
        }
        
    context_str_list = []
    sources = []
    
    for item in retrieved_chunks:
        meta = item["metadata"]
        context_str_list.append(f"Source: {meta['source']}\nContent: {item['text_content']}")
        
        sources.append({
            "chunk_id": item["chunk_id"],
            "source_file": meta["source"],
            "headings": meta["headings"]
        })
        
    context_block = "\n\n---\n\n".join(context_str_list)
    prompt = RAG_PROMPT_TEMPLATE.format(context=context_block, question=question)
    
    try:
        if LLM_PROVIDER == "lightning":
            answer = call_lightning_api(prompt)
        elif LLM_PROVIDER == "ollama":
            answer = call_ollama(prompt)
        elif LLM_PROVIDER == "openai":
            answer = call_openai(prompt)
        elif LLM_PROVIDER == "mock":
            answer = call_mock_llm(prompt, retrieved_chunks)
        else:
            raise ValueError(f"Unknown LLM provider configured: {LLM_PROVIDER}")
            
    except Exception as llm_err:
        logging.warning(f"LLM generation via '{LLM_PROVIDER}' failed: {str(llm_err)}. Falling back to Mock LLM.")
        answer = call_mock_llm(prompt, retrieved_chunks)
        
    return {
        "answer": answer,
        "question": question,
        "sources": sources
    }

# 5. PIPELINE EVALUATION
def evaluate_rag_pipeline(test_queries_path: str) -> Dict:
    path = Path(test_queries_path)
    if not path.exists():
        logging.error(f"Test queries file not found at: {test_queries_path}")
        raise FileNotFoundError(f"Missing file: {test_queries_path}")
        
    with open(path, 'r', encoding='utf-8') as f:
        test_data = json.load(f)
        
    total = len(test_data)
    logging.info(f"Starting full RAG pipeline evaluation on {total} queries...")
    
    embedding_func = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=EMBEDDING_MODEL_NAME
    )
    
    retrieval_correct_ans_correct = {r: 0 for r in range(1, TOP_K + 1)}
    retrieval_correct_ans_incorrect = {r: 0 for r in range(1, TOP_K + 1)}
    
    retrieval_incorrect_ans_correct = 0
    retrieval_incorrect_ans_incorrect = 0
    
    results_by_category = {
        "retrieval_correct_answer_correct": {str(r): [] for r in range(1, TOP_K + 1)},
        "retrieval_correct_answer_incorrect": {str(r): [] for r in range(1, TOP_K + 1)},
        "retrieval_incorrect_answer_correct": [],
        "retrieval_incorrect_answer_incorrect": []
    }
    
    print("\nEvaluating RAG pipeline: [", end="", flush=True)
    step = max(1, total // 10)
    
    for idx, item in enumerate(test_data, 1):
        query_text = item["query"]
        expected_chunk_id = item["chunk_id"]
        reference_answer = item.get("reference_answer", "")
        source_file = item.get("source_file", "")
        
        if idx % step == 0:
            print(".", end="", flush=True)
            
        try:
            rag_output = generate_rag_response(query_text)
            llm_answer = rag_output["answer"]
            retrieved_sources = rag_output["sources"]
            
            found_rank = None
            for rank_idx, src in enumerate(retrieved_sources, 1):
                if src["chunk_id"] == expected_chunk_id:
                    found_rank = rank_idx
                    break
            
            retrieval_is_correct = (found_rank is not None and found_rank <= TOP_K)
            
            emb1 = np.array(embedding_func([llm_answer])[0])
            emb2 = np.array(embedding_func([reference_answer])[0])
            
            dot = np.dot(emb1, emb2)
            norm1 = np.linalg.norm(emb1)
            norm2 = np.linalg.norm(emb2)
            similarity = dot / (norm1 * norm2) if norm1 > 0 and norm2 > 0 else 0.0
            
            answer_is_correct = (similarity >= SIMILARITY_THRESHOLD)
            
            query_info = {
                "query": query_text,
                "expected_chunk_id": expected_chunk_id,
                "reference_answer": reference_answer,
                "llm_answer": llm_answer,
                "similarity_score": float(similarity),
                "retrieved_rank": found_rank,
                "source_file": source_file
            }
            
            if retrieval_is_correct:
                if answer_is_correct:
                    retrieval_correct_ans_correct[found_rank] += 1
                    results_by_category["retrieval_correct_answer_correct"][str(found_rank)].append(query_info)
                else:
                    retrieval_correct_ans_incorrect[found_rank] += 1
                    results_by_category["retrieval_correct_answer_incorrect"][str(found_rank)].append(query_info)
            else:
                if answer_is_correct:
                    retrieval_incorrect_ans_correct += 1
                    results_by_category["retrieval_incorrect_answer_correct"].append(query_info)
                else:
                    retrieval_incorrect_ans_incorrect += 1
                    results_by_category["retrieval_incorrect_answer_incorrect"].append(query_info)
                    
        except Exception as e:
            logging.error(f"Error evaluating query {idx}: {str(e)}")
            retrieval_incorrect_ans_incorrect += 1
            results_by_category["retrieval_incorrect_answer_incorrect"].append({
                "query": query_text,
                "expected_chunk_id": expected_chunk_id,
                "reference_answer": reference_answer,
                "llm_answer": None,
                "error": str(e),
                "source_file": source_file
            })
            
    print("] Done!\n")
    
    total_retrieval_correct = sum(retrieval_correct_ans_correct.values()) + sum(retrieval_correct_ans_incorrect.values())
    total_retrieval_incorrect = retrieval_incorrect_ans_correct + retrieval_incorrect_ans_incorrect
    
    total_ans_correct = sum(retrieval_correct_ans_correct.values()) + retrieval_incorrect_ans_correct
    total_ans_incorrect = sum(retrieval_correct_ans_incorrect.values()) + retrieval_incorrect_ans_incorrect
    
    report = {
        "summary": {
            "total_queries": total,
            "similarity_threshold": SIMILARITY_THRESHOLD,
            "total_retrieval_correct": total_retrieval_correct,
            "total_retrieval_incorrect": total_retrieval_incorrect,
            "total_answers_correct": total_ans_correct,
            "total_answers_incorrect": total_ans_incorrect
        },
        "matrix": {
            "retrieval_correct_ans_correct": retrieval_correct_ans_correct,
            "retrieval_correct_ans_incorrect": retrieval_correct_ans_incorrect,
            "retrieval_incorrect_ans_correct": retrieval_incorrect_ans_correct,
            "retrieval_incorrect_ans_incorrect": retrieval_incorrect_ans_incorrect
        }
    }
    
    pipeline_report_path = Path(test_queries_path).parent / "rag_pipeline_evaluation.json"
    os.makedirs(pipeline_report_path.parent, exist_ok=True)
    logging.info(f"Saving RAG pipeline evaluation report to: {pipeline_report_path.resolve()}")
    try:
        with open(pipeline_report_path, 'w', encoding='utf-8') as out_f:
            json.dump({
                "summary": report["summary"],
                "results_by_category": results_by_category
            }, out_f, ensure_ascii=False, indent=4)
        logging.info("RAG evaluation JSON report written successfully.")
    except Exception as save_err:
        logging.error(f"Failed to save RAG report: {str(save_err)}")
        
    return report

# 6. DEMO INTERFACE
if __name__ == "__main__":
    print("Starting RAG Pipeline Interface (Provider: Lightning AI API)...")
    
    test_query = "What are the guidelines regarding resident rights and treatment in nursing homes?"
    result = generate_rag_response(test_query)
    
    print("\n" + "=" * 60)
    print(f"CÂU HỎI: {result['question']}")
    print("=" * 60)
    print(f"TRẢ LỜI:\n{result['answer']}")
    print("=" * 60)
    print("NGUỒN THAM KHẢO:")
    for src in result["sources"]:
        headings_str = " > ".join(src["headings"].values()) if src["headings"] else "N/A"
        print(f"  - Chunk ID: {src['chunk_id']}")
        print(f"    File: {src['source_file']} | Cấu trúc tiêu đề: {headings_str}\n")
    print("=" * 60 + "\n")
