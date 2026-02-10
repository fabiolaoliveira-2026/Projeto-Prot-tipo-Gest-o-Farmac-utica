"""
Funções centralizadas para gerenciamento de parâmetros dinâmicos.

Este módulo fornece funções para carregar, mesclar e substituir parâmetros
indexados (X1, X2, Y1, Y2, etc.) nas perguntas e queries SQL,
permitindo personalização por questão.
"""

import hashlib
import json
import re
from pathlib import Path
from typing import Any

import yaml

from app.config.paths import GENERATE_CONFIG_FILE


def load_parameters_config(config_path: Path | None = None) -> dict:
    """
    Carrega a configuração de parâmetros do arquivo YAML.

    Args:
        config_path (Path | None): Caminho para o arquivo de configuração.
            Se None, usa GENERATE_CONFIG_FILE.

    Returns:
        Dicionário com a configuração de parâmetros ou dict vazio se não existir.
    """
    path = config_path or GENERATE_CONFIG_FILE
    if not path.exists():
        return {}

    try:
        with open(path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        return config.get("parameters", {})
    except Exception:
        return {}


def get_question_parameters(question_id: int, yaml_config: dict) -> dict[str, str]:
    """
    Retorna parâmetros mesclados para uma pergunta específica.

    Combina parâmetros default com parâmetros específicos da pergunta,
    onde os específicos têm precedência sobre os default.

    Args:
        question_id (int): ID da pergunta (índice da linha no CSV, começando em 1).
        yaml_config (dict): Dicionário de configurações carregado do YAML.

    Returns:
        Dicionário com parâmetros mesclados (chave: nome do parâmetro, valor: valor).
    """
    params_config = yaml_config.get("parameters", {})
    default_params = params_config.get("default", {})
    questions_params = params_config.get("questions", {})

    merged = dict(default_params)

    question_specific = questions_params.get(question_id, {})
    if question_specific:
        merged.update(question_specific)

    return merged


def substitute_parameters(text: str, params: dict[str, str]) -> str:
    """
    Substitui parâmetros indexados no texto pelos seus valores.

    Substitui ocorrências de X1, X2, Y1, Y2, etc. no texto pelos valores
    correspondentes do dicionário de parâmetros.

    Args:
        text (str): Texto contendo placeholders (X1, X2, Y1, Y2, etc.).
        params (dict[str, str]): Dicionário com valores dos parâmetros.

    Returns:
        Texto com os parâmetros substituídos pelos valores.
    """
    if not params or not text:
        return text

    result = text
    for param_name, param_value in params.items():
        if param_value and param_value != "default":
            pattern = rf"'{re.escape(param_name)}'|{re.escape(param_name)}"
            result = re.sub(pattern, str(param_value), result)

    return result


def substitute_sql_parameters(sql: str, params: dict[str, str]) -> str:
    """
    Substitui placeholders X1, Y1, etc. no SQL pelos valores dos parâmetros.

    Versão específica para SQL que trata aspas adequadamente.

    Args:
        sql (str): Conteúdo SQL com placeholders.
        params (dict[str, str]): Dicionário com valores dos parâmetros.

    Returns:
        SQL com parâmetros substituídos.
    """
    if not params or not sql:
        return sql

    result = sql
    for param_name, param_value in params.items():
        result = re.sub(
            rf"['\"]?{re.escape(param_name)}['\"]?",
            str(param_value),
            result
        )
    return result


def generate_params_hash(params: dict[str, str]) -> str:
    """
    Gera hash curto dos parâmetros para identificação de execuções.

    Cria um hash MD5 de 6 caracteres a partir do JSON serializado dos parâmetros.
    Se não houver parâmetros, retorna "default".

    Args:
        params (dict[str, str]): Dicionário com parâmetros da pergunta.

    Returns:
        Hash de 6 caracteres ou "default" se params vazio.
    """
    if not params:
        return "default"

    sorted_params = dict(sorted(params.items()))
    params_json = json.dumps(sorted_params, sort_keys=True, ensure_ascii=False)
    hash_full = hashlib.md5(params_json.encode("utf-8")).hexdigest()

    return hash_full[:6]


def has_custom_parameters(question_id: int, yaml_config: dict) -> bool:
    """
    Verifica se a pergunta tem parâmetros específicos configurados.

    Args:
        question_id (int): ID da pergunta.
        yaml_config (dict): Dicionário de configurações do YAML.

    Returns:
        True se a pergunta tem parâmetros específicos, False caso contrário.
    """
    params_config = yaml_config.get("parameters", {})
    questions_params = params_config.get("questions", {})
    return question_id in questions_params


def get_all_parameter_names(yaml_config: dict) -> set[str]:
    """
    Retorna todos os nomes de parâmetros definidos na configuração.

    Coleta nomes de parâmetros tanto do default quanto das perguntas específicas.

    Args:
        yaml_config (dict): Dicionário de configurações do YAML.

    Returns:
        Conjunto com todos os nomes de parâmetros únicos.
    """
    params_config = yaml_config.get("parameters", {})
    param_names = set()

    default_params = params_config.get("default", {})
    param_names.update(default_params.keys())

    questions_params = params_config.get("questions", {})
    for question_params in questions_params.values():
        if isinstance(question_params, dict):
            param_names.update(question_params.keys())

    return param_names


def apply_parameters_to_question(question_id: int, question_text: str) -> str:
    """
    Aplica substituição de parâmetros a uma pergunta.

    Args:
        question_id (int): ID da pergunta.
        question_text (str): Texto original da pergunta.

    Returns:
        Texto da pergunta com parâmetros substituídos.
    """
    params_config = load_parameters_config()
    params = get_question_parameters(question_id, {"parameters": params_config})
    return substitute_parameters(question_text, params)

