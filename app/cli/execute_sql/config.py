"""
Configurações e constantes para execução de queries SQL.

Define valores padrão para conexão com banco de dados e parâmetros
de substituição em queries SQL.
"""

# Data padrão para substituição de CURRENT_DATE
DEFAULT_TARGET_DATE = "2024-06-01"

# Timeout padrão em segundos (None = sem limite)
DEFAULT_TIMEOUT = 60

# Configurações de conexão padrão (sobrescritas por variáveis de ambiente)
DEFAULT_DB_CONFIG = {
    "host": "localhost",
    "port": "5432",
    "database": "",
    "user": "postgres",
    "password": "",
}

# Nomes dos arquivos de saída
OUTPUT_RESULT_FILE = "resultado.csv"
OUTPUT_ERROR_FILE = "erro.txt"
OUTPUT_SUMMARY_FILE = "resumo_execucao.csv"

