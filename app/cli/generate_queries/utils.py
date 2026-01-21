"""
Funções utilitárias para geração de queries SQL.

Contém funções auxiliares para sanitização de saídas do modelo
e construção de prompts a partir de dados de entrada.
"""

import re
from typing import Optional

import pandas as pd

from .parameters import substitute_parameters


def sanitize_sql_output(raw_text: str) -> str:
    """
    Remove marcadores especiais e formata o SQL final.

    Args:
        raw_text: Texto bruto retornado pelo modelo.

    Returns:
        SQL limpo e formatado.
    """
    cleaned = re.sub(r"<\|\S+\|>|```sql|```", "", raw_text)
    if "</think>" in cleaned:
        cleaned = cleaned[cleaned.find("</think>") + len("</think>"):]
    return cleaned.strip()


def build_question_prompt(
    row: pd.Series,
    question_column: str,
    extra_columns: list[str],
    params: Optional[dict[str, str]] = None
) -> str:
    """
    Constrói o prompt da pergunta a partir de uma linha do DataFrame.

    Opcionalmente aplica substituição de parâmetros (X1, X2, Y1, Y2, etc.)
    no texto da pergunta e nas colunas extras.

    Args:
        row: Linha do DataFrame.
        question_column: Nome da coluna com a pergunta.
        extra_columns: Colunas adicionais para incluir no prompt.
        params: Dicionário de parâmetros para substituição (opcional).

    Returns:
        Prompt formatado com a pergunta e informações extras.
    """
    question_text = str(row[question_column])

    if params:
        question_text = substitute_parameters(question_text, params)

    parts = [f"Pergunta: {question_text}"]

    for col in extra_columns:
        if col in row and pd.notna(row[col]):
            col_value = str(row[col])
            if params:
                col_value = substitute_parameters(col_value, params)
            parts.append(f"{col}: {col_value}")

    return "\n".join(parts)
