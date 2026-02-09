"""
Módulo de carregamento e manipulação de dados.

Contém funções para carregar arquivos CSV de métricas, resumos, queries SQL
e resultados de execução dos modelos Text2SQL.
"""

from app.data.loaders import (
    apply_parameters_to_question,
    get_available_models,
    get_comparison_pairs,
    get_question_parameters,
    get_question_source_info,
    get_question_with_params,
    get_summary_value,
    load_pair_metrics,
    load_pair_result_preview,
    load_pair_sql,
    load_pair_summary,
    load_parameters_config,
    load_questions_source,
    load_result_csv,
    load_sql_file,
    substitute_parameters,
)

__all__ = [
    "apply_parameters_to_question",
    "get_available_models",
    "get_comparison_pairs",
    "get_question_parameters",
    "get_question_source_info",
    "get_question_with_params",
    "get_summary_value",
    "load_pair_metrics",
    "load_pair_result_preview",
    "load_pair_sql",
    "load_pair_summary",
    "load_parameters_config",
    "load_questions_source",
    "load_result_csv",
    "load_sql_file",
    "substitute_parameters",
]
