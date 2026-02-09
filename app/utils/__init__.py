"""
Módulo de utilitários da aplicação.

Contém funções auxiliares para formatação SQL, manipulação de DataFrames,
geração de relatórios HTML e outras operações utilitárias.
"""

from app.utils.dataframe import find_common_column, normalize_columns
from app.utils.html_exporter import generate_full_html_report
from app.utils.sql_formatter import format_sql, generate_sql_diff_html

__all__ = [
    "format_sql",
    "generate_sql_diff_html",
    "generate_full_html_report",
    "normalize_columns",
    "find_common_column",
]

