"""
Configuração de caminhos de diretórios da aplicação.

Define os caminhos para os diretórios de dados, resultados, perguntas
e configurações utilizados pela aplicação.
"""

from pathlib import Path


PROJECT_ROOT = Path(__file__).parent.parent.parent.resolve()
CONFIG_DIR = PROJECT_ROOT / "config"
DATA_DIR = PROJECT_ROOT / "data"
RESULTS_DIR = DATA_DIR / "results"
QUESTIONS_FILE = DATA_DIR / "questions.csv"
QUESTIONS_SOURCE_FILE = DATA_DIR / "questions_source.csv"
QUERIES_DIR = DATA_DIR / "queries"

# RAG Configuration
SCHEMA_FILE = DATA_DIR / "schema.yaml"
CACHE_DIR = PROJECT_ROOT / ".cache" / "embeddings"

# CLI Configuration Files
GENERATE_CONFIG_FILE = CONFIG_DIR / "generate_config.yaml"
COMPARE_CONFIG_FILE = CONFIG_DIR / "compare_config.yaml"
RAG_INDEX_CONFIG_FILE = CONFIG_DIR / "rag_index_config.yaml"
EXECUTE_CONFIG_FILE = CONFIG_DIR / "execute_config.yaml"
GROUND_TRUTH_CONFIG_FILE = CONFIG_DIR / "ground_truth_config.yaml"
