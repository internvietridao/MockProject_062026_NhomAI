import os
import json
import logging
import sys
from pathlib import Path
from typing import List, Dict
import numpy as np
import chromadb
from chromadb.utils import embedding_functions

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

# =====================================================================
# 1. CONFIGURATION BLOCK
# =====================================================================
VECTOR_DB_DIR = str(Path(__file__).parent.parent / "chroma_db")
COLLECTION_NAME = "rag_documents"
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
TOP_K = 3

LLM_PROVIDER = "ollama"
LLM_MODEL_NAME = "qwen2:1.5b"
LLM_API_KEY = ""
OLLAMA_API_URL = "http://localhost:11434/api/generate"

SIMILARITY_THRESHOLD = 0.70

# =====================================================================
# 1.5. RETRIEVAL LOGIC
# =====================================================================
def retrieve_context(
    query_text: str, 
    top_k: int = TOP_K, 
    vector_db_dir: str = VECTOR_DB_DIR, 
    collection_name: str = COLLECTION_NAME, 
    embedding_model_name: str = EMBEDDING_MODEL_NAME
) -> List[Dict]:
    if not os.path.exists(vector_db_dir):
        logging.error(f"ChromaDB persistent directory not found at: {vector_db_dir}")
        raise FileNotFoundError(f"Database directory missing: {vector_db_dir}")
        
    try:
        client = chromadb.PersistentClient(path=vector_db_dir)
        
        embedding_func = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=embedding_model_name
        )
        
        collection = client.get_collection(
            name=collection_name,
            embedding_function=embedding_func
        )
        
        results = collection.query(
            query_texts=[query_text],
            n_results=top_k
        )
        
        retrieved_chunks = []
        
        ids = results.get("ids", [[]])[0]
        distances = results.get("distances", [[]])[0]
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        
        for idx in range(len(ids)):
            meta = metadatas[idx] if idx < len(metadatas) else {}
            
            headings_str = meta.get("headings", "{}")
            try:
                headings_dict = json.loads(headings_str)
            except Exception:
                headings_dict = {}
                
            chunk_data = {
                "chunk_id": ids[idx],
                "score": distances[idx],
                "text_content": documents[idx],
                "metadata": {
                    "source": meta.get("source", ""),
                    "category": meta.get("category", ""),
                    "headings": headings_dict,
                    "chunk_index": meta.get("chunk_index", 0)
                }
            }
            retrieved_chunks.append(chunk_data)
            
        return retrieved_chunks
        
    except Exception as e:
        logging.error(f"Failed to query database for text '{query_text}': {str(e)}")
        raise e

# =====================================================================
# 2. PROMPT TEMPLATE
# =====================================================================
RAG_PROMPT_TEMPLATE = """You are an intelligent AI assistant. Answer the user's question DIRECTLY and ONLY based on the context provided below. If the context does not contain the answer, say "I don't know" and do not make up an answer.
---
CONTEXT:
{context}
---
QUESTION:
{question}
---
ANSWER:"""

# =====================================================================
# 3. LLM CONNECTOR LOGIC
# =====================================================================
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
        logging.error("Ollama connection failed! Please ensure the Ollama desktop app is running and your model is downloaded.")
        raise ConnectionError(f"Cannot connect to Ollama at {OLLAMA_API_URL}. Run 'ollama run {LLM_MODEL_NAME}' in terminal.")
    except Exception as e:
        logging.error(f"Error calling local Ollama LLM: {str(e)}")
        raise e

def call_openai(prompt: str) -> str:
    import requests
    
    if not LLM_API_KEY:
        raise ValueError("OpenAI API Key is missing. Please set LLM_API_KEY in the configuration block.")
        
    headers = {
        "Authorization": f"Bearer {LLM_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": LLM_MODEL_NAME,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.0
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
        return "Tôi không biết vì không tìm thấy ngữ cảnh phù hợp trong tài liệu."
        
    top_chunk = retrieved_chunks[0]
    content = top_chunk["text_content"]
    
    import re
    content_clean = re.sub(r"<!--.*?-->", "", content).strip()
    first_sentence = content_clean.splitlines()[0] if content_clean else ""
    if len(first_sentence) > 200:
        first_sentence = first_sentence[:197] + "..."
        
    mock_response = (
        f"[CÂU TRẢ LỜI GIẢ LẬP (Mock LLM: {LLM_MODEL_NAME})]\n"
        f"Dựa vào tài liệu tham khảo tìm được (Tệp: {top_chunk['metadata']['source']}):\n"
        f"-> \"{first_sentence}\"\n\n"
        f"LƯU Ý: Đây là câu trả lời giả lập. Để lấy câu trả lời thực tế từ LLM local trên CPU, "
        f"vui lòng khởi chạy ứng dụng Ollama và cài đặt cấu hình LLM_PROVIDER = 'ollama'."
    )
    return mock_response

# =====================================================================
# 4. RAG PIPELINE ORCHESTRATOR
# =====================================================================
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
            "answer": "Đã xảy ra lỗi khi tìm kiếm cơ sở dữ liệu Vector.",
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
        if LLM_PROVIDER == "ollama":
            answer = call_ollama(prompt)
        elif LLM_PROVIDER == "openai":
            answer = call_openai(prompt)
        elif LLM_PROVIDER == "mock":
            answer = call_mock_llm(prompt, retrieved_chunks)
        else:
            raise ValueError(f"Unknown LLM provider configured: {LLM_PROVIDER}")
            
    except Exception as llm_err:
        logging.warning(f"LLM generation failed: {str(llm_err)}. Falling back to local Mock LLM for flow testing.")
        answer = call_mock_llm(prompt, retrieved_chunks)
        
    return {
        "answer": answer,
        "question": question,
        "sources": sources
    }

# =====================================================================
# 5. PIPELINE EVALUATION
# =====================================================================
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

def print_rag_evaluation_report(report: Dict, top_k: int):
    summary = report["summary"]
    matrix = report["matrix"]
    total = summary["total_queries"]
    
    print("\n" + "=" * 60)
    print(f"RAG PIPELINE JOINT EVALUATION REPORT (k={top_k})")
    print(f"Embedding Cosine Similarity Threshold: {summary['similarity_threshold']}")
    print("=" * 60)
    print(f"Total Queries Evaluated: {total}")
    
    correct_rate = (summary['total_answers_correct'] / total) * 100 if total > 0 else 0
    incorrect_rate = (summary['total_answers_incorrect'] / total) * 100 if total > 0 else 0
    ret_correct_rate = (summary['total_retrieval_correct'] / total) * 100 if total > 0 else 0
    
    print(f"  - Total Correct Answers (LLM vs Ref): {summary['total_answers_correct']:>3d} / {total} ({correct_rate:.2f}%)")
    print(f"  - Total Incorrect Answers:            {summary['total_answers_incorrect']:>3d} / {total} ({incorrect_rate:.2f}%)")
    print(f"  - Total Correct Context Retrieval:    {summary['total_retrieval_correct']:>3d} / {total} ({ret_correct_rate:.2f}%)")
    print("-" * 60)
    print("2x2 PERFORMANCE MATRIX (RETRIEVAL VS. GENERATION)")
    print("-" * 60)
    print("1. RETRIEVAL CORRECT (Expected Context found in Top K):")
    
    for r in range(1, top_k + 1):
        corr = matrix["retrieval_correct_ans_correct"][str(r) if str(r) in matrix["retrieval_correct_ans_correct"] else r]
        incorr = matrix["retrieval_correct_ans_incorrect"][str(r) if str(r) in matrix["retrieval_correct_ans_incorrect"] else r]
        r_total = corr + incorr
        if r_total > 0:
            print(f"  - At Rank {r}: {r_total:>2d} queries")
            print(f"    * Answer Correct (Matches Ref):   {corr:>2d} ({corr/r_total*100:.2f}%)")
            print(f"    * Answer Incorrect:              {incorr:>2d} ({incorr/r_total*100:.2f}%)")
        else:
            print(f"  - At Rank {r}: 0 queries")
            
    print("\n2. RETRIEVAL INCORRECT (Expected Context NOT in Top K):")
    inc_total = matrix["retrieval_incorrect_ans_correct"] + matrix["retrieval_incorrect_ans_incorrect"]
    if inc_total > 0:
        corr = matrix["retrieval_incorrect_ans_correct"]
        incorr = matrix["retrieval_incorrect_ans_incorrect"]
        print(f"  - Total: {inc_total:>2d} queries")
        print(f"    * Answer Correct (Knowledge/Hallucination): {corr:>2d} ({corr/inc_total*100:.2f}%)")
        print(f"    * Answer Incorrect:                         {incorr:>2d} ({incorr/inc_total*100:.2f}%)")
    else:
        print("  - Total: 0 queries")
    print("=" * 60 + "\n")

# =====================================================================
# 6. DEMO EXECUTIVE INTERFACE
# =====================================================================
if __name__ == "__main__":
    print("Starting RAG Pipeline & Evaluation...")
    
    test_queries_path = Path(__file__).parent / "result" / "test_queries.json"
    
    if test_queries_path.exists():
        try:
            report = evaluate_rag_pipeline(str(test_queries_path))
            print_rag_evaluation_report(report, top_k=TOP_K)
        except Exception as e:
            print(f"Pipeline evaluation failed: {str(e)}")
    else:
        print("test_queries.json not found. Running single fallback query...")
        query = "What are the guidelines regarding resident rights and treatment?"
        result = generate_rag_response(query)
        
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
