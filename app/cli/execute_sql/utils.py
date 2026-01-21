"""
Funções utilitárias para limpeza e preparação de queries SQL.

Fornece funções para sanitização de queries SQL geradas por LLMs,
removendo formatação markdown e ajustando funções de data.
"""

import re
from typing import Optional

import pandas as pd

from .config import DEFAULT_TARGET_DATE


def clean_sql_query(
    query: str,
    target_date: str = DEFAULT_TARGET_DATE,
) -> Optional[str]:
    """
    Limpa e prepara uma query SQL para execução.

    Remove formatação markdown e substitui CURRENT_DATE por data fixa
    para garantir reprodutibilidade dos resultados.

    Args:
        query: Query SQL a ser limpa.
        target_date: Data para substituir CURRENT_DATE.

    Returns:
        Query SQL limpa ou None se inválida/vazia.
    """
    if pd.isna(query) or not query:
        return None

    query = str(query)

    query = re.sub(r"```sql\s*", "", query)
    query = re.sub(r"```\s*", "", query)

    query = re.sub('"""', '"', query)

    query = re.sub(
        r"current_date(\(\))?",
        f"CAST('{target_date}' AS date)",
        query,
        flags=re.IGNORECASE,
    )

    query = query.strip()

    return query if query else None


def format_error_report(
    question_id: int,
    query: Optional[str],
    error_msg: str,
) -> str:
    """
    Formata um relatório de erro para salvamento em arquivo.

    Args:
        question_id: ID da pergunta que gerou erro.
        query: Query SQL que falhou (pode ser None).
        error_msg: Mensagem de erro da execução.

    Returns:
        Texto formatado do relatório de erro.
    """
    lines = [
        "ERRO NA EXECUÇÃO DA CONSULTA SQL",
        "=" * 80,
        "",
        f"Pergunta ID: {question_id}",
        "",
        "CONSULTA SQL:",
        "-" * 80,
        query if query else "N/A",
        "-" * 80,
        "",
        "MENSAGEM DE ERRO COMPLETA:",
        "-" * 80,
        error_msg if error_msg else "Erro desconhecido na execução da consulta",
        "-" * 80,
        "",
    ]
    return "\n".join(lines)


def format_empty_query_error(question_id: int, original_value: str) -> str:
    """
    Formata relatório de erro para query vazia ou inválida.

    Args:
        question_id: ID da pergunta.
        original_value: Valor original recebido (antes da limpeza).

    Returns:
        Texto formatado do relatório de erro.
    """
    lines = [
        "ERRO: Consulta SQL vazia ou inválida",
        "",
        f"Pergunta ID: {question_id}",
        f"Valor recebido: {original_value}",
    ]
    return "\n".join(lines)

