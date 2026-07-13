import os
import json
import logging
from pathlib import Path
from typing import List, Dict
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

# =====================================================================
# 2. RETRIEVAL LOGIC
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

def print_retrieved_results(results: List[Dict]):
    if not results:
        print("No matching results found in ChromaDB.")
        return
        
    print("\n" + "=" * 60)
    print(f"RETRIEVED RESULTS (TOP {len(results)})")
    print("=" * 60)
    
    for rank, item in enumerate(results, 1):
        meta = item["metadata"]
        headings = meta["headings"]
        
        headings_chain = " > ".join(headings.values()) if headings else "N/A"
        
        print(f"\n[Rank {rank}] Chunk ID: {item['chunk_id']}")
        print(f"  - Distance Score: {item['score']:.4f}")
        print(f"  - Source File: {meta['source']} (Category: {meta['category']})")
        print(f"  - Headings Path: {headings_chain}")
        print(f"  - Chunk Index: {meta['chunk_index']}")
        print("  - Content:")
        print("    " + "-" * 50)
        indented_lines = ["    " + line for line in item['text_content'].splitlines()]
        print("\n".join(indented_lines))
        print("    " + "-" * 50)
        
    print("\n" + "=" * 60 + "\n")

# =====================================================================
# 3. ACCURACY EVALUATION
# =====================================================================
def evaluate_retrieval_accuracy(test_queries_path: str, top_k: int = 3) -> Dict:
    path = Path(test_queries_path)
    if not path.exists():
        logging.error(f"Test queries file not found at: {test_queries_path}")
        raise FileNotFoundError(f"Missing file: {test_queries_path}")
        
    with open(path, 'r', encoding='utf-8') as f:
        test_data = json.load(f)
        
    total_queries = len(test_data)
    logging.info(f"Starting evaluation of {total_queries} queries from {test_queries_path} (top_k={top_k})...")
    
    rank_counts = {r: 0 for r in range(1, top_k + 1)}
    rank_counts["not_found"] = 0
    
    matches_by_rank = {str(r): [] for r in range(1, top_k + 1)}
    matches_by_rank["not_found"] = []
    
    print("\nEvaluating queries: [", end="", flush=True)
    step = max(1, total_queries // 20)
    
    for idx, item in enumerate(test_data, 1):
        query_text = item["query"]
        expected_chunk_id = item["chunk_id"]
        reference_answer = item.get("reference_answer", "")
        source_file = item.get("source_file", "")
        
        query_info = {
            "query": query_text,
            "expected_chunk_id": expected_chunk_id,
            "reference_answer": reference_answer,
            "source_file": source_file,
            "retrieved_results": []
        }
        
        if idx % step == 0:
            print(".", end="", flush=True)
            
        try:
            results = retrieve_context(query_text, top_k=top_k)
            
            for r_idx, res in enumerate(results, 1):
                query_info["retrieved_results"].append({
                    "chunk_id": res["chunk_id"],
                    "distance": res["score"],
                    "source": res["metadata"]["source"]
                })
            
            found_rank = None
            for rank_idx, result_item in enumerate(results, 1):
                if result_item["chunk_id"] == expected_chunk_id:
                    found_rank = rank_idx
                    break
                    
            if found_rank is not None and found_rank <= top_k:
                rank_counts[found_rank] += 1
                matches_by_rank[str(found_rank)].append(query_info)
            else:
                rank_counts["not_found"] += 1
                matches_by_rank["not_found"].append(query_info)
                
        except Exception as e:
            rank_counts["not_found"] += 1
            query_info["error"] = str(e)
            matches_by_rank["not_found"].append(query_info)
            
    print("] Done!\n")
            
    accuracies = {}
    for r in range(1, top_k + 1):
        accuracies[f"top_{r}"] = (rank_counts[r] / total_queries) * 100 if total_queries > 0 else 0
        
    not_found_rate = (rank_counts["not_found"] / total_queries) * 100 if total_queries > 0 else 0
    
    found_sum = sum(rank_counts[r] for r in range(1, top_k + 1))
    top_k_hit_rate = (found_sum / total_queries) * 100 if total_queries > 0 else 0
    
    acc_stats = {f"top_{r}": accuracies[f"top_{r}"] for r in range(1, top_k + 1)}
    acc_stats["not_found"] = not_found_rate
    acc_stats["top_k_hit_rate"] = top_k_hit_rate
    
    eval_results = {
        "total_queries": total_queries,
        "rank_counts": rank_counts,
        "accuracies": acc_stats
    }
    
    report_data = {
        "summary": {
            "total_queries": total_queries,
            "rank_counts": {str(k): v for k, v in rank_counts.items()},
            "accuracies": acc_stats
        },
        "matches_by_rank": matches_by_rank
    }
    
    output_report_path = Path(test_queries_path).parent / "evaluation_results.json"
    os.makedirs(output_report_path.parent, exist_ok=True)
    logging.info(f"Saving detailed evaluation results to: {output_report_path.resolve()}")
    try:
        with open(output_report_path, 'w', encoding='utf-8') as out_f:
            json.dump(report_data, out_f, ensure_ascii=False, indent=4)
        logging.info("Evaluation JSON file written successfully.")
    except Exception as save_err:
        logging.error(f"Failed to write evaluation results: {str(save_err)}")
    
    return eval_results

def print_evaluation_report(eval_results: Dict, top_k: int):
    total = eval_results["total_queries"]
    rank_counts = eval_results["rank_counts"]
    acc = eval_results["accuracies"]
    
    print("=" * 60)
    print(f"RETRIEVAL ACCURACY REPORT (k={top_k})")
    print("=" * 60)
    print(f"Total Queries Evaluated: {total}")
    print("\nDistribution of Matches:")
    
    for r in range(1, top_k + 1):
        print(f"  - Found at Rank {r}:         {rank_counts[r]:>3d} queries ({acc[f'top_{r}']:.2f}%)")
        
    print(f"  - Not found in top {top_k}:      {rank_counts['not_found']:>3d} queries ({acc['not_found']:.2f}%)")
    print("\nSummary Statistics:")
    print(f"  - Top 1 Accuracy (Exact):  {acc['top_1']:.2f}%")
    print(f"  - Top {top_k} Hit Rate (Recall): {acc['top_k_hit_rate']:.2f}%")
    print("=" * 60 + "\n")

# =====================================================================
# 4. DEMO INTERFACE
# =====================================================================
if __name__ == "__main__":
    print("Starting ChromaDB Similarity Search & Evaluation...")
    
    test_queries_path = Path(__file__).parent / "result" / "test_queries.json"
    
    if test_queries_path.exists():
        try:
            eval_results = evaluate_retrieval_accuracy(str(test_queries_path), top_k=TOP_K)
            print_evaluation_report(eval_results, top_k=TOP_K)
        except Exception as e:
            print(f"Accuracy evaluation failed: {str(e)}")
    else:
        print("test_queries.json not found. Running single fallback query...")
        test_query = "What are the guidelines regarding resident rights and treatment?"
        try:
            results = retrieve_context(test_query, top_k=TOP_K)
            print_retrieved_results(results)
        except Exception as ex:
            print(f"Demo failed: {str(ex)}")
