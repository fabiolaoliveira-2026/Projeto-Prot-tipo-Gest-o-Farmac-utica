"""
Submódulo CLI para execução de queries SQL.

Fornece uma interface de linha de comando para executar consultas SQL
geradas pelo sistema Text2SQL em um banco de dados PostgreSQL,
salvando resultados e erros em estrutura organizada por questão.
"""

from .cli import main
from .config import DEFAULT_TARGET_DATE
from .executor import execute_query, get_db_config, test_connection
from .utils import clean_sql_query

__all__ = [
    "main",
    "execute_query",
    "get_db_config",
    "test_connection",
    "clean_sql_query",
    "DEFAULT_TARGET_DATE",
]

