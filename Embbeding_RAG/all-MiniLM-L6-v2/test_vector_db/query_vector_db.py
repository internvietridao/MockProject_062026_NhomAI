import os
import json
import logging
import sys
from pathlib import Path
from typing import List, Dict

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
TOP_K = config.TOP_K

sys.path.append(str(Path(__file__).resolve().parent))
try:
    from retrieval import retrieve_context
except ImportError:
    from .retrieval import retrieve_context

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

# 2. ACCURACY EVALUATION
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
    
    total_reciprocal_rank = 0.0
    total_precision_at_k = 0.0
    
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
                total_reciprocal_rank += 1.0 / found_rank
                total_precision_at_k += 1.0 / top_k
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
    
    mrr = (total_reciprocal_rank / total_queries) if total_queries > 0 else 0.0
    precision_at_k = (total_precision_at_k / total_queries) if total_queries > 0 else 0.0
    
    acc_stats = {f"top_{r}": accuracies[f"top_{r}"] for r in range(1, top_k + 1)}
    acc_stats["not_found"] = not_found_rate
    acc_stats["top_k_hit_rate"] = top_k_hit_rate
    acc_stats["mrr"] = mrr
    acc_stats[f"precision_at_{top_k}"] = precision_at_k
    
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
    
    try:
        save_markdown_report(eval_results, test_queries_path, top_k)
    except Exception as md_err:
        logging.error(f"Failed to write Markdown report: {str(md_err)}")
        
    return eval_results

def save_markdown_report(eval_results: Dict, test_queries_path: str, top_k: int):
    from datetime import datetime
    
    total = eval_results["total_queries"]
    rank_counts = eval_results["rank_counts"]
    acc = eval_results["accuracies"]
    
    model_name_clean = config.EMBEDDING_MODEL_NAME.replace("/", "_")
    retrieval_mode = config.RETRIEVAL_MODE
    date_str = datetime.now().strftime("%d-%m-%Y")
    filename = f"{model_name_clean}_{retrieval_mode}_{date_str}.md"
    
    output_dir = Path(test_queries_path).parent
    output_path = output_dir / filename
    
    readable_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    md_content = f"""# Retrieval Evaluation Report

- **Evaluation Time**: {readable_time}
- **Embedding Model**: `{config.EMBEDDING_MODEL_NAME}`
- **Retrieval Mode**: `{config.RETRIEVAL_MODE.upper()}`
- **Total Queries Evaluated**: {total}

---

## 1. Summary Statistics

| Metric | Value |
| :--- | :---: |
| **Top 1 Accuracy (Exact)** | {acc['top_1']:.2f}% |
| **Top {top_k} Hit Rate (Recall)** | {acc['top_k_hit_rate']:.2f}% |
| **Precision@{top_k}** | {acc[f'precision_at_{top_k}'] * 100:.2f}% |
| **Mean Reciprocal Rank (MRR)** | {acc['mrr'] * 100:.2f}% |

---

## 2. Distribution of Matches

| Rank | Match Count | Percentage |
| :--- | :---: | :---: |
"""
    for r in range(1, top_k + 1):
        md_content += f"| **Rank {r}** | {rank_counts[r]} | {acc[f'top_{r}']:.2f}% |\n"
        
    md_content += f"| **Not Found** | {rank_counts['not_found']} | {acc['not_found']:.2f}% |\n"
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(md_content)
        logging.info(f"Saved evaluation markdown report to: {output_path.resolve()}")
    except Exception as e:
        logging.error(f"Failed to write markdown report: {str(e)}")

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
    print(f"  - Precision@{top_k}:            {acc[f'precision_at_{top_k}'] * 100:.2f}%")
    print(f"  - Mean Reciprocal Rank (MRR): {acc['mrr'] * 100:.2f}%")
    print("=" * 60 + "\n")

# 3. DEMO INTERFACE
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
