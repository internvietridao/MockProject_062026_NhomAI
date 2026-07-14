import os
import json
import random
import re
import logging
from pathlib import Path
from typing import List, Dict

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

import sys

# 1. CONFIGURATION
sys.path.append(str(Path(__file__).resolve().parent.parent))
import config

CHUNKS_JSON_PATH = config.CHUNKS_JSON_PATH
NUM_TEST_QUERIES = config.NUM_TEST_QUERIES
OUTPUT_FILE_NAME = config.TEST_QUERIES_FILE_NAME

# 2. HELPER LOGIC FOR QUERY GENERATION
def clean_text(text: str) -> str:
    text = re.sub(r"<!--.*?-->", "", text)
    text = re.sub(r"\[.*?\]\(.*?\)", "", text)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return " ".join(lines)

def generate_query_from_chunk(chunk: Dict) -> str:
    text_content = chunk.get("text_content", "")
    cleaned_body = clean_text(text_content)
    
    sentences = re.split(r'(?<=[.!?])\s+', cleaned_body)
    first_sentence = sentences[0] if sentences else cleaned_body
    first_sentence = first_sentence.rstrip(".!?")
    
    words = first_sentence.split()
    if not words:
        return "What are the standard guidelines described in this section?"
        
    if len(words) > 12:
        topic = " ".join(words[:12]) + "..."
    else:
        topic = " ".join(words)
        
    topic_lower = topic[0].lower() + topic[1:] if len(topic) > 1 else topic
    
    templates = [
        f"What are the specific requirements and regulations regarding {topic_lower}?",
        f"According to the documentation, what is specified about {topic_lower}?",
        f"Can you explain the guidelines for {topic_lower}?",
        f"What does the policy document state about {topic_lower}?"
    ]
    
    template_idx = len(topic) % len(templates)
    return templates[template_idx]

# 3. MAIN RUNNER
if __name__ == "__main__":
    logging.info("Starting Test Query Generator...")
    
    try:
        chunks_path = Path(CHUNKS_JSON_PATH)
        if not chunks_path.exists():
            logging.error(f"Source chunks JSON file not found at: {CHUNKS_JSON_PATH}")
            raise FileNotFoundError(f"Missing file: {CHUNKS_JSON_PATH}")
            
        with open(chunks_path, 'r', encoding='utf-8') as f:
            chunks = json.load(f)
            
        if not chunks:
            logging.error("The source chunks JSON file is empty.")
            raise ValueError("No data inside chunks JSON.")
            
        logging.info(f"Loaded {len(chunks)} chunks.")
        
        num_to_sample = min(NUM_TEST_QUERIES, len(chunks))
        logging.info(f"Selecting {num_to_sample} random chunks to generate questions...")
        sampled_chunks = random.sample(chunks, num_to_sample)
        
        test_queries = []
        for idx, chunk in enumerate(sampled_chunks):
            query_str = generate_query_from_chunk(chunk)
            
            meta = chunk.get("metadata", {})
            ref_answer = clean_text(chunk.get("text_content", ""))
            
            query_item = {
                "query": query_str,
                "reference_answer": ref_answer,
                "source_file": meta.get("source_file", ""),
                "chunk_id": chunk.get("chunk_id", "")
            }
            test_queries.append(query_item)
            logging.info(f"Generated Question {idx+1}: {query_str}")
            
        current_dir = Path(__file__).parent
        output_dir = current_dir / "result"
        os.makedirs(output_dir, exist_ok=True)
        output_path = output_dir / OUTPUT_FILE_NAME
        
        logging.info(f"Saving test queries to: {output_path.resolve()}")
        with open(output_path, 'w', encoding='utf-8') as out_f:
            json.dump(test_queries, out_f, ensure_ascii=False, indent=4)
            
        logging.info("=" * 60)
        logging.info("SUCCESS: Test queries generated successfully!")
        logging.info(f"Total questions written: {len(test_queries)}")
        logging.info("=" * 60)
        
    except Exception as ex:
        logging.critical(f"Query generation failed: {str(ex)}")
