"""
Carregador de configurações YAML para os CLIs.

Este módulo fornece funções para carregar configurações de arquivos YAML
e mesclá-las com valores padrão e parâmetros de linha de comando.
"""

from pathlib import Path
from typing import Any, TypeVar

import yaml

T = TypeVar("T")


def load_yaml_config(config_path: Path) -> dict[str, Any]:
    """
    Carrega configurações de um arquivo YAML.

    Args:
        config_path: Caminho para o arquivo YAML de configuração.

    Returns:
        Dicionário com as configurações carregadas.

    Raises:
        FileNotFoundError: Se o arquivo não existir.
        yaml.YAMLError: Se houver erro ao parsear o YAML.
    """
    if not config_path.exists():
        raise FileNotFoundError(
            f"Arquivo de configuração não encontrado: {config_path}"
        )

    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def get_config_value(
    cli_value: T | None,
    yaml_config: dict[str, Any],
    yaml_key: str,
    default: T
) -> T:
    """
    Obtém valor de configuração com precedência: CLI > YAML > default.

    Args:
        cli_value: Valor passado via CLI (None se não fornecido).
        yaml_config: Dicionário de configurações do YAML.
        yaml_key: Chave para buscar no YAML (suporta notação com ponto).
        default: Valor padrão caso não encontre em nenhuma fonte.

    Returns:
        Valor da configuração com a precedência correta.
    """
    if cli_value is not None:
        return cli_value

    keys = yaml_key.split(".")
    value = yaml_config
    for key in keys:
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            return default

    return value if value is not None else default


def merge_configs(
    defaults: dict[str, Any],
    yaml_config: dict[str, Any],
    cli_overrides: dict[str, Any]
) -> dict[str, Any]:
    """
    Mescla configurações de múltiplas fontes com precedência.

    Precedência: cli_overrides > yaml_config > defaults

    Args:
        defaults: Valores padrão.
        yaml_config: Configurações carregadas do YAML.
        cli_overrides: Valores passados via CLI (não-None são considerados).

    Returns:
        Dicionário com as configurações mescladas.
    """
    result = defaults.copy()

    def deep_merge(base: dict, override: dict) -> dict:
        for key, value in override.items():
            if (
                key in base
                and isinstance(base[key], dict)
                and isinstance(value, dict)
            ):
                base[key] = deep_merge(base[key], value)
            else:
                base[key] = value
        return base

    result = deep_merge(result, yaml_config)

    filtered_cli = {k: v for k, v in cli_overrides.items() if v is not None}
    result = deep_merge(result, filtered_cli)

    return result
