"""
Interface de linha de comando para execução de queries SQL.

Processa arquivos .sql gerados pelo text2sql-generate e executa cada query
em um banco de dados PostgreSQL, salvando resultados e erros na mesma
estrutura de diretórios em data/results/.
"""

import sys
from pathlib import Path
from typing import Annotated, Optional

import pandas as pd
import typer
from dotenv import load_dotenv
from tqdm import tqdm

from app.cli.config_loader import get_config_value, load_yaml_config
from app.config.paths import EXECUTE_CONFIG_FILE, QUERIES_DIR, RESULTS_DIR

from .config import (
    DEFAULT_TARGET_DATE,
    DEFAULT_TIMEOUT,
    OUTPUT_ERROR_FILE,
    OUTPUT_RESULT_FILE,
    OUTPUT_SUMMARY_FILE,
)
from .executor import execute_query, get_db_config, test_connection
from .utils import clean_sql_query, format_empty_query_error, format_error_report

app = typer.Typer(
    name="execute",
    help="Executa queries SQL geradas pelo Text2SQL em banco PostgreSQL.",
    add_completion=False,
)


def discover_sql_files(queries_dir: Path) -> list[dict]:
    """
    Descobre todos os arquivos .sql no diretório.

    Estrutura esperada: queries_dir/N.sql (onde N é o ID da questão)

    Args:
        queries_dir: Diretório contendo os arquivos .sql.

    Returns:
        Lista de dicionários com informações de cada arquivo SQL encontrado.
    """
    sql_files = []

    if not queries_dir.exists():
        return sql_files

    for sql_file in sorted(queries_dir.glob("*.sql")):
        try:
            question_id = int(sql_file.stem)
            sql_files.append({
                "question_id": question_id,
                "sql_file": sql_file,
            })
        except ValueError:
            continue

    return sql_files


def check_already_executed(results_dir: Path, question_id: int) -> dict | None:
    """
    Verifica se uma query já foi executada anteriormente.

    Args:
        results_dir: Diretório base de resultados.
        question_id: ID da pergunta.

    Returns:
        Dicionário com resultado anterior ou None se não executada.
    """
    result_folder = results_dir / str(question_id)

    result_file = result_folder / OUTPUT_RESULT_FILE
    if result_file.exists():
        try:
            df = pd.read_csv(result_file)
            return {
                "pergunta_id": question_id,
                "status": "sucesso",
                "mensagem": "(já executado)",
                "linhas_retornadas": len(df),
            }
        except Exception:
            pass

    error_file = result_folder / OUTPUT_ERROR_FILE
    if error_file.exists():
        return {
            "pergunta_id": question_id,
            "status": "erro",
            "mensagem": "(já executado)",
            "linhas_retornadas": 0,
        }

    return None


def process_sql_files(
    sql_files: list[dict],
    results_dir: Path,
    target_date: str,
    db_config: dict[str, str],
    resume: bool = True,
    timeout: int | None = None,
) -> pd.DataFrame:
    """
    Processa e executa todos os arquivos SQL descobertos.

    Salva resultados incrementalmente após cada execução.

    Args:
        sql_files: Lista de arquivos SQL a processar.
        results_dir: Diretório base para salvar resultados.
        target_date: Data para substituir CURRENT_DATE.
        db_config: Configuração de conexão com o banco.
        resume: Se deve pular queries já executadas.

    Returns:
        DataFrame com resumo das execuções.
    """
    execution_results = []
    skipped_count = 0
    summary_file = results_dir / OUTPUT_SUMMARY_FILE

    if resume:
        for item in sql_files:
            question_id = item["question_id"]
            existing_result = check_already_executed(results_dir, question_id)
            if existing_result:
                execution_results.append(existing_result)
                skipped_count += 1

        if skipped_count > 0:
            typer.echo(f"  ↻ {skipped_count} queries já executadas (pulando)")

    to_process = []
    for item in sql_files:
        question_id = item["question_id"]
        if resume and check_already_executed(results_dir, question_id):
            continue
        to_process.append(item)

    if not to_process:
        typer.echo("  ✓ Todas as queries já foram executadas")
        return pd.DataFrame(execution_results)

    for item in tqdm(to_process, desc="Executando queries"):
        question_id = item["question_id"]
        sql_file = item["sql_file"]

        original_sql = sql_file.read_text(encoding="utf-8")
        query = clean_sql_query(original_sql, target_date)

        result_folder = results_dir / str(question_id)
        result_folder.mkdir(parents=True, exist_ok=True)

        if not query:
            error_content = format_empty_query_error(question_id, original_sql[:200])
            error_file = result_folder / OUTPUT_ERROR_FILE
            error_file.write_text(error_content, encoding="utf-8")

            result = {
                "pergunta_id": question_id,
                "status": "erro",
                "mensagem": "Consulta SQL vazia ou inválida",
                "linhas_retornadas": 0,
            }
            execution_results.append(result)

            df_summary = pd.DataFrame(execution_results)
            df_summary.to_csv(summary_file, index=False)
            continue

        df_result, error_msg = execute_query(query, db_config, timeout=timeout)

        if df_result is not None:
            output_file = result_folder / OUTPUT_RESULT_FILE
            df_result.to_csv(output_file, index=False)

            result = {
                "pergunta_id": question_id,
                "status": "sucesso",
                "mensagem": "",
                "linhas_retornadas": len(df_result),
            }
        else:
            error_content = format_error_report(question_id, query, error_msg or "")
            error_file = result_folder / OUTPUT_ERROR_FILE
            error_file.write_text(error_content, encoding="utf-8")

            result = {
                "pergunta_id": question_id,
                "status": "erro",
                "mensagem": error_msg or "Erro desconhecido",
                "linhas_retornadas": 0,
            }

        execution_results.append(result)

        df_summary = pd.DataFrame(execution_results)
        df_summary.to_csv(summary_file, index=False)

    return pd.DataFrame(execution_results)


def print_summary(df_summary: pd.DataFrame) -> None:
    """
    Exibe resumo das execuções no terminal.

    Args:
        df_summary: DataFrame com resultados das execuções.
    """
    total = len(df_summary)
    if total == 0:
        typer.echo("Nenhuma query executada.")
        return

    success = len(df_summary[df_summary["status"] == "sucesso"])
    errors = len(df_summary[df_summary["status"] == "erro"])

    typer.echo("")
    typer.echo("=" * 60)
    typer.echo("RESUMO DA EXECUÇÃO")
    typer.echo("=" * 60)
    typer.echo(f"Total de queries: {total}")
    typer.echo(f"Sucesso: {success} ({success/total*100:.1f}%)")
    typer.echo(f"Erros: {errors} ({errors/total*100:.1f}%)")
    typer.echo("=" * 60)


@app.command()
def run(
    config: Annotated[
        Optional[Path],
        typer.Option("--config", "-c", help="Arquivo YAML de configuração.")
    ] = EXECUTE_CONFIG_FILE,
    queries_dir: Annotated[
        Optional[Path],
        typer.Option("--queries", "-q", help="Diretório com arquivos .sql gerados.")
    ] = None,
    results_dir: Annotated[
        Optional[Path],
        typer.Option("--results", "-r", help="Diretório para salvar resultados.")
    ] = None,
    target_date: Annotated[
        Optional[str],
        typer.Option("--target-date", help="Data para substituir CURRENT_DATE.")
    ] = None,
    resume: Annotated[
        bool,
        typer.Option("--resume/--no-resume", help="Retoma execução de onde parou.")
    ] = True,
    timeout: Annotated[
        Optional[int],
        typer.Option("--timeout", "-t", help="Timeout em segundos para cada query.")
    ] = None,
) -> None:
    """
    Executa queries SQL dos arquivos .sql gerados pelo text2sql-generate.

    Processa a estrutura de diretórios gerada (queries/modelo/questao/hash/*.sql),
    executa cada query no banco de dados e salva os resultados na mesma estrutura
    em results/modelo/questao/hash/.

    Requer variáveis de ambiente: DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD.
    """
    load_dotenv()

    yaml_config: dict = {}
    if config and config.exists():
        try:
            yaml_config = load_yaml_config(config)
            typer.echo(f"Configuração carregada de: {config}")
        except Exception as e:
            typer.echo(f"Erro ao carregar configuração: {e}", err=True)
            raise typer.Exit(1)

    cfg_queries = get_config_value(queries_dir, yaml_config, "paths.queries", QUERIES_DIR)
    cfg_results = get_config_value(results_dir, yaml_config, "paths.results", RESULTS_DIR)
    cfg_target_date = get_config_value(target_date, yaml_config, "sql.target_date", DEFAULT_TARGET_DATE)
    cfg_timeout = get_config_value(timeout, yaml_config, "sql.timeout", DEFAULT_TIMEOUT)

    if isinstance(cfg_queries, str):
        cfg_queries = Path(cfg_queries)
    if isinstance(cfg_results, str):
        cfg_results = Path(cfg_results)

    if not cfg_queries.exists():
        typer.echo(f"Erro: Diretório de queries não encontrado: {cfg_queries}", err=True)
        raise typer.Exit(1)

    typer.echo("=" * 60)
    typer.echo("EXECUÇÃO DE QUERIES SQL")
    typer.echo("=" * 60)
    typer.echo(f"Diretório de queries: {cfg_queries}")
    typer.echo(f"Diretório de resultados: {cfg_results}")
    typer.echo(f"Data alvo: {cfg_target_date}")
    typer.echo(f"Timeout: {cfg_timeout}s" if cfg_timeout else "Timeout: sem limite")
    typer.echo(f"Modo resume: {'Sim' if resume else 'Não'}")
    typer.echo("-" * 60)

    typer.echo("Testando conexão com o banco...")
    db_config = get_db_config(yaml_config)
    success, msg = test_connection(db_config)

    if not success:
        typer.echo(f"  ✗ Falha na conexão: {msg}", err=True)
        typer.echo("Verifique as variáveis de ambiente DB_*", err=True)
        raise typer.Exit(1)

    typer.echo("  ✓ Conexão estabelecida")

    typer.echo("Descobrindo arquivos SQL...")
    sql_files = discover_sql_files(cfg_queries)
    typer.echo(f"  ✓ {len(sql_files)} arquivos SQL encontrados")

    if not sql_files:
        typer.echo("Nenhum arquivo SQL encontrado na estrutura de diretórios.", err=True)
        raise typer.Exit(1)

    typer.echo("-" * 60)

    cfg_results.mkdir(parents=True, exist_ok=True)
    df_summary = process_sql_files(sql_files, cfg_results, cfg_target_date, db_config, resume, cfg_timeout)

    summary_file = cfg_results / OUTPUT_SUMMARY_FILE
    df_summary.to_csv(summary_file, index=False)
    typer.echo(f"  ✓ Resumo salvo em: {summary_file}")

    print_summary(df_summary)


@app.command()
def test_db(
    config: Annotated[
        Optional[Path],
        typer.Option("--config", "-c", help="Arquivo YAML de configuração.")
    ] = EXECUTE_CONFIG_FILE,
) -> None:
    """Testa a conexão com o banco de dados PostgreSQL."""
    load_dotenv()

    yaml_config: dict = {}
    if config and config.exists():
        try:
            yaml_config = load_yaml_config(config)
        except Exception:
            pass

    typer.echo("Testando conexão com o banco de dados...")
    typer.echo("-" * 40)

    db_config = get_db_config(yaml_config)
    typer.echo(f"Host: {db_config['host']}")
    typer.echo(f"Port: {db_config['port']}")
    typer.echo(f"Database: {db_config['database']}")
    typer.echo(f"User: {db_config['user']}")
    typer.echo("-" * 40)

    success, msg = test_connection(db_config)

    if success:
        typer.echo(f"✓ {msg}")
    else:
        typer.echo(f"✗ Erro: {msg}", err=True)
        raise typer.Exit(1)


@app.command()
def config() -> None:
    """Mostra o caminho do arquivo de configuração padrão."""
    typer.echo(f"Arquivo de configuração: {EXECUTE_CONFIG_FILE}")
    if EXECUTE_CONFIG_FILE.exists():
        typer.echo("Status: ✓ Existe")
    else:
        typer.echo("Status: ✗ Não encontrado")


def main() -> int:
    """
    Função principal do CLI de execução de queries.

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

