"""
Submódulo CLI para geração de queries SQL.

Fornece uma interface de linha de comando para processar perguntas
em linguagem natural e gerar consultas SQL utilizando modelos de
linguagem com suporte a RAG (Retrieval-Augmented Generation).
"""

from .cli import main
from .config import AVAILABLE_MODELS, DEFAULT_BUSINESS_RULES, DEFAULT_SYSTEM_TEMPLATE
from .generator import predict
from .parameters import (
    generate_params_hash,
    get_question_parameters,
    has_custom_parameters,
    substitute_parameters,
)
from .utils import build_question_prompt, sanitize_sql_output

__all__ = [
    "main",
    "predict",
    "sanitize_sql_output",
    "build_question_prompt",
    "AVAILABLE_MODELS",
    "DEFAULT_SYSTEM_TEMPLATE",
    "DEFAULT_BUSINESS_RULES",
    "get_question_parameters",
    "substitute_parameters",
    "generate_params_hash",
    "has_custom_parameters",
]

