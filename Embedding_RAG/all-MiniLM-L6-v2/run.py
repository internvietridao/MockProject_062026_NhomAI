import sys
import subprocess
import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

def run_script(script_path: Path):
    logging.info("=" * 60)
    logging.info(f"RUNNING: {script_path}")
    logging.info("=" * 60)
    
    cwd = script_path.parent
    try:
        result = subprocess.run(
            [sys.executable, script_path.name],
            cwd=str(cwd),
            check=True
        )
        if result.returncode == 0:
            logging.info(f"SUCCESS: {script_path.name} finished successfully.\n")
    except subprocess.CalledProcessError as err:
        logging.error(f"FAILED: {script_path.name} failed with exit code {err.returncode}.\n")
        sys.exit(err.returncode)

if __name__ == "__main__":
    current_dir = Path(__file__).parent.resolve()
    
    # 1. embedding_storage.py
    embedding_script = current_dir / "embedding_storage.py"
    
    # 2. generate_and_test_queries.py
    queries_script = current_dir / "test_vector_db" / "generate_and_test_queries.py"
    
    # 3. query_vector_db.py
    search_script = current_dir / "test_vector_db" / "query_vector_db.py"
    
    # Execute sequentially
    run_script(embedding_script)
    run_script(queries_script)
    run_script(search_script)
    
    logging.info("=" * 60)
    logging.info("ALL PIPELINE SCRIPTS EXECUTED SUCCESSFULLY!")
    logging.info("=" * 60)
