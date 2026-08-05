import os
from pathlib import Path

# PATHS AND DIRECTORIES
BASE_DIR = Path(__file__).parent.resolve()

# Chunks file location (sử dụng thư mục chuẩn 'chunks')
CHUNKS_JSON_PATH = str(BASE_DIR.parent / "chunks" / "all_chunks.json")

VECTOR_DB_DIR = str(BASE_DIR / "chroma_db")
COLLECTION_NAME = "rag_documents"

TEST_QUERIES_DIR = str(BASE_DIR / "test_vector_db" / "result")
TEST_QUERIES_FILE_NAME = "test_queries.json"
TEST_QUERIES_PATH = str(BASE_DIR / "test_vector_db" / "result" / "test_queries.json")

# PARAMETERS
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
BATCH_SIZE = 32
TOP_K = 3

RESET_DB = True

# Retrieval Mode Options: "cosine", "bm25", "hybrid" (combines both using RRF)
RETRIEVAL_MODE = "hybrid"

NUM_TEST_QUERIES = 100

# LLM PROVIDER CONFIGURATION
# Supported providers: "lightning", "ollama", "openai", "mock"
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "lightning")

# Lightning AI Studio FastAPI Endpoint Configuration
LIGHTNING_API_URL = os.getenv("LIGHTNING_API_URL", "https://8000-01kz8gqwpzzmqz0zw9z3gp5zar.cloudspaces.litng.ai/")

# Fallback Provider Settings
LLM_MODEL_NAME = "Qwen2.5-0.5B-Instruct"
LLM_API_KEY = os.getenv("OPENAI_API_KEY", "")
OLLAMA_API_URL = "http://localhost:11434/api/generate"

SIMILARITY_THRESHOLD = 0.70
