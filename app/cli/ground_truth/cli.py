"""
Interface de linha de comando para geração de ground truth com parâmetros.

Processa arquivos SQL do ground truth, substituindo placeholders X1, Y1, etc.
por valores configurados em YAML, e salvando na estrutura compatível com
text2sql-execute.
"""

import re
import sys
from pathlib import Path
from typing import Annotated, Optional

import typer
from tqdm import tqdm

from app.cli.config_loader import get_config_value, load_yaml_config
from app.config.paths import GROUND_TRUTH_CONFIG_FILE, QUERIES_DIR

app = typer.Typer(
    name="ground-truth",
    help="Gera ground truth com parâmetros substituídos.",
    add_completion=False,
)


def get_question_parameters(question_id: int, yaml_config: dict) -> dict[str, str]:
    """
    Retorna parâmetros mesclados para uma pergunta específica.

    Args:
        question_id: ID da pergunta.
        yaml_config: Configuração YAML com seção 'parameters'.

    Returns:
        Dicionário com parâmetros mesclados (default + específicos).
    """
    params_config = yaml_config.get("parameters", {})
    default_params = params_config.get("default", {})
    questions_params = params_config.get("questions", {})

    merged = dict(default_params)
    question_specific = questions_params.get(question_id, {})
    if question_specific:
        merged.update(question_specific)

    return merged


def substitute_parameters(sql: str, params: dict[str, str]) -> str:
    """
    Substitui placeholders X1, Y1, etc. no SQL pelos valores dos parâmetros.

    Args:
        sql: Conteúdo SQL com placeholders.
        params: Dicionário com valores dos parâmetros.

    Returns:
        SQL com parâmetros substituídos.
    """
    result = sql
    for param_name, param_value in params.items():
        # Substitui 'X1' ou "X1" (com aspas) e X1 (sem aspas)
        result = re.sub(
            rf"['\"]?{re.escape(param_name)}['\"]?",
            str(param_value),
            result
        )
    return result


def discover_sql_files(source_dir: Path) -> list[dict]:
    """
    Descobre arquivos .sql no diretório fonte.

    Args:
        source_dir: Diretório com arquivos SQL do ground truth.

    Returns:
        Lista de dicionários com question_id e sql_file.
    """
    sql_files = []

    for sql_file in sorted(source_dir.glob("*.sql")):
        try:
            question_id = int(sql_file.stem)
            sql_files.append({
                "question_id": question_id,
                "sql_file": sql_file,
            })
        except ValueError:
            continue

    return sql_files


def process_ground_truth(
    sql_files: list[dict],
    output_dir: Path,
    run_name: str,
    yaml_config: dict,
) -> int:
    """
    Processa arquivos SQL substituindo parâmetros.

    Args:
        sql_files: Lista de arquivos SQL a processar.
        output_dir: Diretório base de saída.
        run_name: Nome da run.
        yaml_config: Configuração com parâmetros.

    Returns:
        Número de arquivos processados.
    """
    processed = 0
    run_folder = output_dir / run_name
    run_folder.mkdir(parents=True, exist_ok=True)

    for item in tqdm(sql_files, desc="Processando ground truth"):
        question_id = item["question_id"]
        sql_file = item["sql_file"]

        original_sql = sql_file.read_text(encoding="utf-8")
        params = get_question_parameters(question_id, yaml_config)

        processed_sql = substitute_parameters(original_sql, params)

        output_sql = run_folder / f"{question_id}.sql"
        output_sql.write_text(processed_sql, encoding="utf-8")

        processed += 1

    return processed


@app.command()
def run(
    config: Annotated[
        Optional[Path],
        typer.Option("--config", "-c", help="Arquivo YAML de configuração.")
    ] = GROUND_TRUTH_CONFIG_FILE,
    source_dir: Annotated[
        Optional[Path],
        typer.Option("--source", "-s", help="Diretório com SQL do ground truth.")
    ] = None,
    output_dir: Annotated[
        Optional[Path],
        typer.Option("--output", "-o", help="Diretório de saída.")
    ] = None,
    run: Annotated[
        Optional[str],
        typer.Option("--run", "-r", help="Nome da run.")
    ] = None,
) -> None:
    """
    Gera ground truth com parâmetros substituídos.

    Lê arquivos SQL do ground truth, substitui placeholders X1, Y1, etc.
    pelos valores configurados no YAML, e salva na estrutura:
    output/run/N.sql
    """
    yaml_config: dict = {}
    if config and config.exists():
        try:
            yaml_config = load_yaml_config(config)
            typer.echo(f"Configuração carregada de: {config}")
        except Exception as e:
            typer.echo(f"Erro ao carregar configuração: {e}", err=True)
            raise typer.Exit(1)

    cfg_source = get_config_value(
        source_dir, yaml_config, "paths.source", QUERIES_DIR / "ground_truth"
    )
    cfg_output = get_config_value(
        output_dir, yaml_config, "paths.output", QUERIES_DIR / "ground_truth"
    )
    cfg_run = get_config_value(run, yaml_config, "output.run", "default")

    if isinstance(cfg_source, str):
        cfg_source = Path(cfg_source)
    if isinstance(cfg_output, str):
        cfg_output = Path(cfg_output)

    if not cfg_source.exists():
        typer.echo(f"Erro: Diretório fonte não encontrado: {cfg_source}", err=True)
        raise typer.Exit(1)

    typer.echo("=" * 60)
    typer.echo("GERAÇÃO DE GROUND TRUTH COM PARÂMETROS")
    typer.echo("=" * 60)
    typer.echo(f"Diretório fonte: {cfg_source}")
    typer.echo(f"Diretório saída: {cfg_output}")
    typer.echo(f"Run: {cfg_run}")

    params_config = yaml_config.get("parameters", {})
    num_defaults = len(params_config.get("default", {}))
    num_questions = len(params_config.get("questions", {}))
    typer.echo(f"Parâmetros default: {num_defaults}")
    typer.echo(f"Questões com parâmetros específicos: {num_questions}")
    typer.echo("-" * 60)

    sql_files = discover_sql_files(cfg_source)
    typer.echo(f"Arquivos SQL encontrados: {len(sql_files)}")

    if not sql_files:
        typer.echo("Nenhum arquivo SQL encontrado.", err=True)
        raise typer.Exit(1)

    processed = process_ground_truth(sql_files, cfg_output, cfg_run, yaml_config)

    typer.echo("-" * 60)
    typer.echo(f"✓ {processed} arquivos processados")
    typer.echo(f"✓ Saída em: {cfg_output / cfg_run}")
    typer.echo("=" * 60)


@app.command()
def config() -> None:
    """Mostra o caminho do arquivo de configuração padrão."""
    typer.echo(f"Arquivo de configuração: {GROUND_TRUTH_CONFIG_FILE}")
    if GROUND_TRUTH_CONFIG_FILE.exists():
        typer.echo("Status: ✓ Existe")
    else:
        typer.echo("Status: ✗ Não encontrado")


def main() -> int:
    """
    Função principal do CLI de ground truth.

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

