import os
from pathlib import Path

# PATHS AND DIRECTORIES
BASE_DIR = Path(__file__).parent.resolve()

CHUNKS_JSON_PATH = str(BASE_DIR.parent / "chucks" / "all_chunks.json")

VECTOR_DB_DIR = str(BASE_DIR / "chroma_db")
COLLECTION_NAME = "rag_documents"

TEST_QUERIES_DIR = str(BASE_DIR / "test_vector_db" / "result")
TEST_QUERIES_FILE_NAME = "test_queries.json"
TEST_QUERIES_PATH = str(BASE_DIR / "test_vector_db" / "result" / "test_queries.json")

# PARAMETERS

EMBEDDING_MODEL_NAME = "nomic-ai/nomic-embed-text-v1.5"
BATCH_SIZE = 32
TOP_K = 3

RESET_DB = True

RETRIEVAL_MODE = "hybrid"

NUM_TEST_QUERIES = 100

LLM_PROVIDER = "ollama"
LLM_MODEL_NAME = "qwen2:1.5b"
LLM_API_KEY = ""
OLLAMA_API_URL = "http://localhost:11434/api/generate"

SIMILARITY_THRESHOLD = 0.70
