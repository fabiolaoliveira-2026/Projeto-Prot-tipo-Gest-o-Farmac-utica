"""
CLI de comparação de resultados Text2SQL.

Este módulo fornece uma interface de linha de comando para comparar
os resultados de modelos de IA com o ground truth, gerando arquivos
CSV com métricas e resumos.
"""

import sys
from pathlib import Path
from typing import Annotated, Optional

import pandas as pd
import typer

from app.cli.config_loader import get_config_value, load_yaml_config
from app.config.paths import COMPARE_CONFIG_FILE, QUESTIONS_FILE, RESULTS_DIR
from app.metrics.comparator import compare_model

app = typer.Typer(
    name="text2sql-compare",
    help="Compara resultados de modelos Text2SQL com o ground truth.",
    add_completion=False,
)


def get_available_models() -> list[str]:
    """
    Lista todos os modelos disponíveis no diretório de resultados.

    Returns:
        Lista com nomes dos modelos (excluindo ground_truth).
    """
    models = []
    for item in RESULTS_DIR.iterdir():
        if item.is_dir() and item.name != "ground_truth":
            models.append(item.name)
    return sorted(models)


@app.command()
def compare(
    config: Annotated[
        Optional[Path],
        typer.Option("--config", "-c", help="Arquivo YAML de configuração.")
    ] = COMPARE_CONFIG_FILE,
    modelos: Annotated[
        Optional[list[str]],
        typer.Option("--modelo", "-m", help="Nome do modelo a processar (pode repetir para múltiplos).")
    ] = None,
    questions_file: Annotated[
        Optional[Path],
        typer.Option("--questions", "-q", help="Caminho para o arquivo CSV de perguntas.")
    ] = None,
    results_dir: Annotated[
        Optional[Path],
        typer.Option("--results-dir", "-r", help="Diretório com os resultados dos modelos.")
    ] = None,
) -> None:
    """
    Compara resultados de modelos Text2SQL com o ground truth.

    Se nenhum modelo for especificado, processa todos os modelos disponíveis.
    Configurações podem ser passadas via arquivo YAML (--config) e/ou parâmetros.
    """
    yaml_config: dict = {}
    if config and config.exists():
        try:
            yaml_config = load_yaml_config(config)
            typer.echo(f"Configuração carregada de: {config}")
        except Exception as e:
            typer.echo(f"Erro ao carregar configuração: {e}", err=True)
            raise typer.Exit(1)

    cfg_questions = get_config_value(questions_file, yaml_config, "paths.questions", QUESTIONS_FILE)
    cfg_results_dir = get_config_value(results_dir, yaml_config, "paths.results_dir", RESULTS_DIR)
    cfg_modelos = get_config_value(modelos, yaml_config, "models", None)

    if isinstance(cfg_questions, str):
        cfg_questions = Path(cfg_questions)
    if isinstance(cfg_results_dir, str):
        cfg_results_dir = Path(cfg_results_dir)

    if not cfg_questions.exists():
        typer.echo(f"Erro: Arquivo de perguntas não encontrado: {cfg_questions}", err=True)
        raise typer.Exit(1)

    questions_df = pd.read_csv(cfg_questions)

    available_models = get_available_models()

    if not available_models:
        typer.echo("Nenhum modelo encontrado em data/results/", err=True)
        raise typer.Exit(1)

    if cfg_modelos:
        models_to_process = []
        for model in cfg_modelos:
            if model in available_models:
                models_to_process.append(model)
            else:
                typer.echo(f"Aviso: Modelo '{model}' não encontrado. Modelos disponíveis: {available_models}")
    else:
        models_to_process = available_models

    if not models_to_process:
        typer.echo("Nenhum modelo válido para processar.", err=True)
        raise typer.Exit(1)

    typer.echo(f"Modelos a processar: {models_to_process}")
    typer.echo("-" * 50)

    for model_name in models_to_process:
        typer.echo(f"\nProcessando modelo: {model_name}")

        try:
            metricas_df, resumo_df = compare_model(model_name, questions_df)

            model_dir = cfg_results_dir / model_name
            metricas_path = model_dir / "metricas.csv"
            resumo_path = model_dir / "resumo.csv"

            metricas_df.to_csv(metricas_path, index=False)
            resumo_df.to_csv(resumo_path, index=False)

            typer.echo(f"  ✓ Métricas salvas em: {metricas_path}")
            typer.echo(f"  ✓ Resumo salvo em: {resumo_path}")

            f1_media = resumo_df[resumo_df["metrica"] == "f1_media"]["valor"].values[0]
            taxa_sucesso = resumo_df[resumo_df["metrica"] == "taxa_execucao_sucesso"]["valor"].values[0]
            typer.echo(f"  → F1 médio: {f1_media}")
            typer.echo(f"  → Taxa de execução com sucesso: {taxa_sucesso:.1%}")

        except Exception as e:
            typer.echo(f"  ✗ Erro ao processar modelo {model_name}: {e}", err=True)

    typer.echo("\n" + "=" * 50)
    typer.echo("Comparação concluída!")


@app.command()
def list_models() -> None:
    """Lista os modelos disponíveis para comparação."""
    available_models = get_available_models()

    if not available_models:
        typer.echo("Nenhum modelo encontrado em data/results/")
        raise typer.Exit(1)

    typer.echo("Modelos disponíveis:")
    for model in available_models:
        typer.echo(f"  - {model}")


@app.command()
def show_config() -> None:
    """Mostra o caminho do arquivo de configuração padrão."""
    typer.echo(f"Arquivo de configuração: {COMPARE_CONFIG_FILE}")
    if COMPARE_CONFIG_FILE.exists():
        typer.echo("Status: ✓ Existe")
    else:
        typer.echo("Status: ✗ Não encontrado")


def main() -> int:
    """
    Função principal do CLI de comparação.

    Returns:
        Código de saída (0 para sucesso, 1 para erro).
    """
    try:
        app()
        return 0
    except SystemExit as e:
        return e.code if isinstance(e.code, int) else 1


if __name__ == "__main__":
    sys.exit(main())
