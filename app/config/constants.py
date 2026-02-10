"""
Constantes centralizadas da aplicação Text2SQL.

Este módulo contém todas as constantes e valores padrão utilizados
pela aplicação, evitando duplicação em múltiplos arquivos.
"""

# Modelos LLM disponíveis para geração de queries
AVAILABLE_MODELS = [
    "meta-llama/Meta-Llama-3.1-8B-Instruct",
    "Qwen/Qwen3-4B-Thinking-2507",
    "Qwen/Qwen3-14B-FP8",
    "Qwen/Qwen3-32B-AWQ",
    "Qwen/Qwen3-8B",
    "deepseek-ai/deepseek-coder-7b-instruct-v1.5",
    "Snowflake/Arctic-Text2SQL-R1-7B",
]

# Configurações padrão do modelo LLM
DEFAULT_MODEL = "Qwen/Qwen3-32B-AWQ"
DEFAULT_MAX_NEW_TOKENS = 32768
DEFAULT_TEMPERATURE = 0.0001
DEFAULT_TOP_P = 0.95

# Configurações padrão do RAG
DEFAULT_RAG_MODEL = "neuralmind/bert-large-portuguese-cased"
DEFAULT_SIMILARITY_THRESHOLD = 0.3
DEFAULT_MAX_TABLES = 5
DEFAULT_MAX_COLUMNS_PER_TABLE = 20
DEFAULT_MAX_CONTEXT_LENGTH = 32768

