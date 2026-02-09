"""
Funções de carregamento de dados da aplicação.

Este módulo contém todas as funções responsáveis por carregar arquivos CSV
de métricas, resumos, queries SQL e resultados de execução dos modelos Text2SQL.
Utiliza a estrutura de pares: modelo/run.
"""

import re
from pathlib import Path

import pandas as pd
import yaml

from app.config.paths import GENERATE_CONFIG_FILE, QUERIES_DIR, QUESTIONS_SOURCE_FILE, RESULTS_DIR

AVAILABLE_MODELS = [
    "meta-llama/Meta-Llama-3.1-8B-Instruct",
    "Qwen/Qwen3-4B-Thinking-2507",
    "Qwen/Qwen3-14B-FP8",
    "Qwen/Qwen3-32B-AWQ",
    "Qwen/Qwen3-8B",
    "deepseek-ai/deepseek-coder-7b-instruct-v1.5",
    "Snowflake/Arctic-Text2SQL-R1-7B",
]


def get_available_models() -> list[str]:
    """
    Retorna lista de modelos disponíveis.

    Returns:
        Lista com nomes dos modelos.
    """
    return AVAILABLE_MODELS


def get_comparison_pairs() -> list[dict]:
    """
    Lista todos os pares de comparação disponíveis.

    Estrutura esperada: modelo/run/metricas.csv

    Returns:
        Lista de dicionários com informações dos pares.
    """
    pairs = []

    for model_dir in RESULTS_DIR.iterdir():
        if not model_dir.is_dir() or model_dir.name == "ground_truth":
            continue

        model_name = model_dir.name

        for run_dir in model_dir.iterdir():
            if not run_dir.is_dir():
                continue

            metricas_file = run_dir / "metricas.csv"
            if metricas_file.exists():
                pairs.append({
                    "model": model_name,
                    "run": run_dir.name,
                    "pair_name": f"{model_name}/{run_dir.name}",
                    "path": run_dir
                })

    return sorted(pairs, key=lambda x: x["pair_name"])


def load_pair_metrics(pair_name: str) -> pd.DataFrame | None:
    """
    Carrega o arquivo de métricas de um par de comparação.

    Args:
        pair_name: Nome do par no formato "modelo/run".

    Returns:
        DataFrame com métricas ou None se não existir.
    """
    path = RESULTS_DIR / pair_name / "metricas.csv"
    if path.exists():
        return pd.read_csv(path)
    return None


def load_pair_summary(pair_name: str) -> pd.DataFrame | None:
    """
    Carrega o arquivo de resumo de um par de comparação.

    Args:
        pair_name: Nome do par no formato "modelo/run".

    Returns:
        DataFrame com resumo ou None se não existir.
    """
    path = RESULTS_DIR / pair_name / "resumo.csv"
    if path.exists():
        return pd.read_csv(path)
    return None


def load_pair_sql(pair_name: str, is_ground_truth: bool = False) -> pd.DataFrame | None:
    """
    Carrega as queries SQL de um par.

    Args:
        pair_name: Nome do par no formato "modelo/run" ou apenas "run" para GT.
        is_ground_truth: Se True, carrega do ground_truth.

    Returns:
        DataFrame com queries SQL ou None se não existir.
    """
    if is_ground_truth:
        run = pair_name.split("/")[-1] if "/" in pair_name else pair_name
        path = RESULTS_DIR / "ground_truth" / run / "sql.csv"
        if not path.exists():
            path = RESULTS_DIR / "ground_truth" / "sql.csv"
    else:
        path = RESULTS_DIR / pair_name / "sql.csv"

    if path.exists():
        return pd.read_csv(path)
    return None


def load_sql_file(pair_name: str, question_id: int, is_ground_truth: bool = False) -> str | None:
    """
    Carrega o conteúdo de um arquivo SQL individual.

    Args:
        pair_name: Nome do par no formato "modelo/run" ou apenas "run" para GT.
        question_id: ID da pergunta.
        is_ground_truth: Se True, carrega do ground_truth.

    Returns:
        Conteúdo do arquivo SQL ou None se não existir.
    """
    if is_ground_truth:
        run = pair_name.split("/")[-1] if "/" in pair_name else pair_name
        paths_to_try = [
            QUERIES_DIR / "ground_truth" / run / f"{question_id}.sql",
            QUERIES_DIR / "ground_truth" / f"{question_id}.sql",
        ]
    else:
        paths_to_try = [
            QUERIES_DIR / pair_name / f"{question_id}.sql",
        ]

    for path in paths_to_try:
        if path.exists():
            try:
                return path.read_text(encoding="utf-8")
            except Exception:
                continue

    return None


def load_pair_result_preview(
    pair_name: str,
    question_id: int,
    is_ground_truth: bool = False,
    n_rows: int = 10
) -> pd.DataFrame | None:
    """
    Carrega preview do resultado de uma pergunta de um par.

    Args:
        pair_name: Nome do par no formato "modelo/run" ou "run" para GT.
        question_id: ID da pergunta.
        is_ground_truth: Se True, carrega do ground_truth.
        n_rows: Número de linhas a retornar.

    Returns:
        DataFrame com preview ou None se não existir.
    """
    if is_ground_truth:
        run = pair_name.split("/")[-1] if "/" in pair_name else pair_name
        path = RESULTS_DIR / "ground_truth" / run / str(question_id) / "resultado.csv"
    else:
        path = RESULTS_DIR / pair_name / str(question_id) / "resultado.csv"

    if path.exists():
        try:
            return pd.read_csv(path, nrows=n_rows)
        except Exception:
            return None
    return None


def load_result_csv(path) -> pd.DataFrame | None:
    """
    Carrega um arquivo CSV de resultado com colunas normalizadas.

    Args:
        path: Caminho para o arquivo CSV.

    Returns:
        DataFrame carregado e normalizado ou None se não existir.
    """
    from app.utils.dataframe import normalize_columns

    if isinstance(path, str):
        path = Path(path)

    if not path.exists():
        return None

    try:
        df = pd.read_csv(path)
        return normalize_columns(df)
    except Exception:
        return None


def get_summary_value(summary_df: pd.DataFrame, metric_name: str) -> float | None:
    """
    Obtém valor de uma métrica do resumo.

    Args:
        summary_df: DataFrame de resumo.
        metric_name: Nome da métrica.

    Returns:
        Valor da métrica ou None.
    """
    if summary_df is None:
        return None
    row = summary_df[summary_df["metrica"] == metric_name]
    if row.empty:
        return None
    return row.iloc[0]["valor"]


def load_parameters_config() -> dict:
    """
    Carrega a configuração de parâmetros do arquivo YAML.

    Returns:
        Dicionário com a configuração de parâmetros ou dict vazio se não existir.
    """
    if not GENERATE_CONFIG_FILE.exists():
        return {}

    try:
        with open(GENERATE_CONFIG_FILE, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        return config.get("parameters", {})
    except Exception:
        return {}


def get_question_parameters(question_id: int, params_config: dict) -> dict[str, str]:
    """
    Retorna parâmetros mesclados para uma pergunta específica.

    Args:
        question_id: ID da pergunta.
        params_config: Configuração de parâmetros do YAML.

    Returns:
        Dicionário com parâmetros mesclados (default + específicos).
    """
    default_params = params_config.get("default", {})
    questions_params = params_config.get("questions", {})

    merged = dict(default_params)
    question_specific = questions_params.get(question_id, {})
    if question_specific:
        merged.update(question_specific)

    return merged


def substitute_parameters(text: str, params: dict[str, str]) -> str:
    """
    Substitui placeholders X1, Y1, etc. no texto pelos valores dos parâmetros.

    Args:
        text: Texto contendo placeholders.
        params: Dicionário com valores dos parâmetros.

    Returns:
        Texto com parâmetros substituídos.
    """
    if not params or not text:
        return text

    result = text
    for param_name, param_value in params.items():
        if param_value and param_value != "default":
            pattern = rf"'{re.escape(param_name)}'|{re.escape(param_name)}"
            result = re.sub(pattern, str(param_value), result)

    return result


def apply_parameters_to_question(question_id: int, question_text: str) -> str:
    """
    Aplica substituição de parâmetros a uma pergunta.

    Args:
        question_id: ID da pergunta.
        question_text: Texto original da pergunta.

    Returns:
        Texto da pergunta com parâmetros substituídos.
    """
    params_config = load_parameters_config()
    params = get_question_parameters(question_id, params_config)
    return substitute_parameters(question_text, params)


_questions_source_cache: pd.DataFrame | None = None


def load_questions_source() -> pd.DataFrame | None:
    """
    Carrega o arquivo de perguntas fonte (questions_source.csv).

    Returns:
        DataFrame com as perguntas fonte ou None se não existir.
    """
    global _questions_source_cache

    if _questions_source_cache is not None:
        return _questions_source_cache

    if not QUESTIONS_SOURCE_FILE.exists():
        return None

    try:
        _questions_source_cache = pd.read_csv(QUESTIONS_SOURCE_FILE)
        return _questions_source_cache
    except Exception:
        return None


def get_question_source_info(question_id: int) -> dict | None:
    """
    Obtém informações completas de uma pergunta do arquivo fonte.

    Args:
        question_id: ID da pergunta.

    Returns:
        Dicionário com questao, intencao, tipo_dado ou None se não encontrada.
    """
    df = load_questions_source()
    if df is None:
        return None

    row = df[df["id"] == question_id]
    if row.empty:
        return None

    row = row.iloc[0]
    return {
        "questao": row.get("Questões", ""),
        "intencao": row.get("Intenção", ""),
        "tipo_dado": row.get("Tipo de dado necessário", ""),
    }


def get_question_with_params(question_id: int) -> dict:
    """
    Obtém a pergunta do arquivo fonte junto com os parâmetros utilizados.

    Args:
        question_id: ID da pergunta.

    Returns:
        Dicionário com questao, intencao, tipo_dado e parametros.
    """
    source_info = get_question_source_info(question_id)
    params_config = load_parameters_config()
    params = get_question_parameters(question_id, params_config)

    clean_params = {k: v for k, v in params.items() if v and v != "default"}

    if source_info:
        return {
            "questao": source_info["questao"],
            "intencao": source_info["intencao"],
            "tipo_dado": source_info["tipo_dado"],
            "parametros": clean_params,
        }

    return {
        "questao": "",
        "intencao": "",
        "tipo_dado": "",
        "parametros": clean_params,
    }
