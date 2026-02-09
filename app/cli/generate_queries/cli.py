"""
Interface de linha de comando para geração de queries SQL.

Processa argumentos de linha de comando e orquestra a geração de queries SQL
a partir de perguntas em linguagem natural utilizando modelos de linguagem.
"""

import os
import sys
from pathlib import Path
from typing import Annotated, Optional

import pandas as pd
import typer
from dotenv import load_dotenv
from tqdm import tqdm

from app.cli.config_loader import get_config_value, load_yaml_config
from app.config.paths import (
    CACHE_DIR,
    GENERATE_CONFIG_FILE,
    QUERIES_DIR,
    QUESTIONS_FILE,
    RESULTS_DIR,
    SCHEMA_FILE,
)

from .config import (
    AVAILABLE_MODELS,
    DEFAULT_BUSINESS_RULES,
    DEFAULT_MAX_COLUMNS_PER_TABLE,
    DEFAULT_MAX_CONTEXT_LENGTH,
    DEFAULT_MAX_NEW_TOKENS,
    DEFAULT_MAX_TABLES,
    DEFAULT_MODEL,
    DEFAULT_RAG_MODEL,
    DEFAULT_SIMILARITY_THRESHOLD,
    DEFAULT_SYSTEM_TEMPLATE,
    DEFAULT_TEMPERATURE,
    DEFAULT_TOP_P,
)
from .generator import predict
from .parameters import get_question_parameters
from .utils import build_question_prompt

app = typer.Typer(
    name="generate",
    help="Gera queries SQL a partir de perguntas em linguagem natural.",
    add_completion=False,
)


def initialize_rag(schema_path: Path, rag_model: str, similarity_threshold: float):
    """
    Inicializa o engine RAG para recuperação de contexto.

    Args:
        schema_path: Caminho para o arquivo YAML do schema.
        rag_model: Nome do modelo sentence-transformers.
        similarity_threshold: Threshold de similaridade para recuperação.

    Returns:
        Instância do Text2SQLWithRAG.

    Raises:
        ImportError: Se o módulo Text2SQLWithRAG não puder ser importado.
        Exception: Se houver erro na inicialização do RAG.
    """
    from app.llm.rag import Text2SQLWithRAG

    return Text2SQLWithRAG(
        schema_path=str(schema_path),
        model_name=rag_model,
        similarity_threshold=similarity_threshold,
        cache_dir=str(CACHE_DIR)
    )


def initialize_model(model_name: str):
    """
    Carrega o modelo de linguagem para geração.

    Args:
        model_name: Nome do modelo no Hugging Face Hub.

    Returns:
        Instância do TransformerModel carregado.

    Raises:
        ImportError: Se o módulo TransformerModel não puder ser importado.
        Exception: Se houver erro no carregamento do modelo.
    """
    from app.llm.model.transformer import TransformerModel

    model = TransformerModel()
    token = os.environ.get("LLM_TOKEN") if "Meta" in model_name else None
    model.load_transformer_model(model_name, token=token)
    return model


def process_questions_incremental(
    df: pd.DataFrame,
    rag,
    model,
    question_column: str,
    extra_columns: list[str],
    max_new_tokens: int,
    temperature: float,
    top_p: float,
    enable_thinking: bool,
    max_tables: int,
    max_columns: int,
    system_template: str,
    business_rules: str,
    yaml_config: dict,
    model_name: str,
    run_name: str,
    save_queries: bool,
    results_dir: Path,
    queries_dir: Path,
    resume: bool = True,
) -> tuple[pd.DataFrame, Path, Path | None]:
    """
    Processa perguntas gerando queries SQL e salvando incrementalmente.

    Cada query é salva imediatamente após ser gerada, garantindo que
    resultados parciais não sejam perdidos em caso de interrupção.

    Args:
        df: DataFrame com as perguntas.
        rag: Instância do Text2SQLWithRAG.
        model: Instância do TransformerModel.
        question_column: Nome da coluna com as perguntas.
        extra_columns: Colunas extras para incluir no prompt.
        max_new_tokens: Número máximo de tokens a gerar.
        temperature: Temperatura para geração.
        top_p: Top-p para geração.
        enable_thinking: Se ativa o modo de raciocínio.
        max_tables: Máximo de tabelas no contexto.
        max_columns: Máximo de colunas por tabela.
        system_template: Template do sistema para o prompt.
        business_rules: Regras de negócio para o prompt.
        yaml_config: Configuração YAML com parâmetros de substituição.
        model_name: Nome do modelo utilizado.
        run_name: Nome da run (execução).
        save_queries: Se deve salvar queries em arquivos separados.
        results_dir: Diretório base para salvar resultados CSV.
        queries_dir: Diretório base para salvar queries SQL.
        resume: Se deve retomar de onde parou (default True).

    Returns:
        Tupla com (DataFrame processado, caminho CSV, caminho queries ou None).
    """
    model_config = {
        "max_new_tokens": max_new_tokens,
        "temperature": temperature,
        "do_sample": True,
        "top_p": top_p,
        "enable_thinking": enable_thinking
    }

    rag_config = {
        "max_tables": max_tables,
        "max_columns_per_table": max_columns,
        "max_context_length": DEFAULT_MAX_CONTEXT_LENGTH
    }

    model_short_name = model_name.split("/")[-1]
    csv_save_path = results_dir / model_short_name / run_name / "sql.csv"
    csv_save_path.parent.mkdir(parents=True, exist_ok=True)

    queries_base_path = None
    if save_queries:
        queries_base_path = queries_dir / model_short_name / run_name
        queries_base_path.mkdir(parents=True, exist_ok=True)

    existing_sql_data = {}
    questions_to_process = []

    if "SQL" not in df.columns:
        df["SQL"] = ""
    if "Parameters" not in df.columns:
        df["Parameters"] = ""
    if enable_thinking and "Thinking" not in df.columns:
        df["Thinking"] = ""

    if resume and save_queries and queries_base_path and queries_base_path.exists():
        existing_files = list(queries_base_path.glob("*.sql"))
        for sql_file in existing_files:
            try:
                question_id = int(sql_file.stem)
                sql_content = sql_file.read_text()
                if sql_content.strip():
                    existing_sql_data[question_id] = sql_content
            except (ValueError, IOError):
                continue

        for question_id, sql_content in existing_sql_data.items():
            idx = question_id - 1
            if idx < len(df):
                df.at[idx, "SQL"] = sql_content
                params = get_question_parameters(question_id, yaml_config)
                df.at[idx, "Parameters"] = str(params) if params else ""

        for idx in range(len(df)):
            question_id = idx + 1
            if question_id not in existing_sql_data:
                questions_to_process.append((idx, question_id))

        if existing_sql_data:
            typer.echo(f"  ↻ {len(existing_sql_data)} queries já existentes (pulando)")

        if questions_to_process:
            missing_ids = [q[1] for q in questions_to_process]
            if len(missing_ids) <= 10:
                typer.echo(f"  → Faltam processar: {missing_ids}")
            else:
                typer.echo(f"  → Faltam processar: {len(missing_ids)} queries")

    else:
        for idx in range(len(df)):
            questions_to_process.append((idx, idx + 1))

    if not questions_to_process:
        typer.echo("  ✓ Todas as perguntas já foram processadas")
        df.to_csv(csv_save_path, index=False)
        return df, csv_save_path, queries_base_path

    processed = 0
    for idx, question_id in tqdm(questions_to_process, desc="Processando"):
        row = df.iloc[idx]

        params = get_question_parameters(question_id, yaml_config)
        prompt = build_question_prompt(row, question_column, extra_columns, params)

        result = predict(
            rag,
            prompt,
            system_template,
            business_rules,
            rag_config,
            model,
            model_config
        )

        if isinstance(result, tuple):
            sql_content, thinking_content = result
        else:
            sql_content = result
            thinking_content = ""

        df.at[idx, "SQL"] = sql_content
        df.at[idx, "Parameters"] = str(params) if params else ""

        if enable_thinking:
            df.at[idx, "Thinking"] = thinking_content

        if save_queries and queries_base_path:
            query_file = queries_base_path / f"{question_id}.sql"
            query_file.write_text(str(sql_content))

        df.to_csv(csv_save_path, index=False)
        processed += 1

    typer.echo(f"  ✓ {processed} queries geradas")
    return df, csv_save_path, queries_base_path




@app.command()
def run(
    config: Annotated[
        Optional[Path],
        typer.Option("--config", "-c", help="Arquivo YAML de configuração.")
    ] = GENERATE_CONFIG_FILE,
    model: Annotated[
        Optional[str],
        typer.Option("--model", "-m", help="Nome do modelo LLM a utilizar.")
    ] = None,
    questions: Annotated[
        Optional[Path],
        typer.Option("--questions", "-q", help="Caminho para o arquivo CSV de perguntas.")
    ] = None,
    question_column: Annotated[
        Optional[str],
        typer.Option("--question-column", help="Nome da coluna com as perguntas.")
    ] = None,
    extra_columns: Annotated[
        Optional[list[str]],
        typer.Option("--extra-columns", help="Colunas extras para incluir no prompt.")
    ] = None,
    schema: Annotated[
        Optional[Path],
        typer.Option("--schema", "-s", help="Caminho para o arquivo YAML do schema.")
    ] = None,
    run: Annotated[
        Optional[str],
        typer.Option("--run", "-r", help="Nome da run (execução).")
    ] = None,
    enable_thinking: Annotated[
        Optional[bool],
        typer.Option("--enable-thinking/--no-thinking", help="Ativa o modo de raciocínio.")
    ] = None,
    max_new_tokens: Annotated[
        Optional[int],
        typer.Option("--max-new-tokens", help="Número máximo de tokens a gerar.")
    ] = None,
    temperature: Annotated[
        Optional[float],
        typer.Option("--temperature", help="Temperatura para geração.")
    ] = None,
    top_p: Annotated[
        Optional[float],
        typer.Option("--top-p", help="Top-p para geração.")
    ] = None,
    rag_model: Annotated[
        Optional[str],
        typer.Option("--rag-model", help="Modelo sentence-transformers para RAG.")
    ] = None,
    similarity_threshold: Annotated[
        Optional[float],
        typer.Option("--similarity-threshold", help="Threshold de similaridade RAG.")
    ] = None,
    max_tables: Annotated[
        Optional[int],
        typer.Option("--max-tables", help="Máximo de tabelas no contexto.")
    ] = None,
    max_columns: Annotated[
        Optional[int],
        typer.Option("--max-columns", help="Máximo de colunas por tabela.")
    ] = None,
    save_queries: Annotated[
        Optional[bool],
        typer.Option("--save-queries/--no-save-queries", help="Salva queries em arquivos .sql.")
    ] = None,
    resume: Annotated[
        bool,
        typer.Option("--resume/--no-resume", help="Retoma processamento de onde parou.")
    ] = True,
) -> None:
    """
    Gera queries SQL a partir de perguntas em linguagem natural.

    Processa um arquivo CSV contendo perguntas e utiliza um modelo de linguagem
    com suporte a RAG para gerar consultas SQL correspondentes.

    Configurações podem ser passadas via arquivo YAML (--config) e/ou parâmetros.
    Parâmetros de linha de comando têm precedência sobre o arquivo YAML.
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

    cfg_model = get_config_value(model, yaml_config, "model.name", DEFAULT_MODEL)
    cfg_questions = get_config_value(questions, yaml_config, "paths.questions", QUESTIONS_FILE)
    cfg_question_column = get_config_value(question_column, yaml_config, "data.question_column", "Questões")
    cfg_extra_columns = get_config_value(
        extra_columns, yaml_config, "data.extra_columns", ["Tipo de dado necessário", "Intenção"]
    )
    cfg_schema = get_config_value(schema, yaml_config, "paths.schema", SCHEMA_FILE)
    cfg_run = get_config_value(run, yaml_config, "output.run", "default")
    cfg_enable_thinking = get_config_value(enable_thinking, yaml_config, "model.enable_thinking", False)
    cfg_max_new_tokens = get_config_value(max_new_tokens, yaml_config, "model.max_new_tokens", DEFAULT_MAX_NEW_TOKENS)
    cfg_temperature = get_config_value(temperature, yaml_config, "model.temperature", DEFAULT_TEMPERATURE)
    cfg_top_p = get_config_value(top_p, yaml_config, "model.top_p", DEFAULT_TOP_P)
    cfg_rag_model = get_config_value(rag_model, yaml_config, "rag.model_name", DEFAULT_RAG_MODEL)
    cfg_similarity_threshold = get_config_value(
        similarity_threshold, yaml_config, "rag.similarity_threshold", DEFAULT_SIMILARITY_THRESHOLD
    )
    cfg_max_tables = get_config_value(max_tables, yaml_config, "rag.max_tables", DEFAULT_MAX_TABLES)
    cfg_max_columns = get_config_value(max_columns, yaml_config, "rag.max_columns_per_table", DEFAULT_MAX_COLUMNS_PER_TABLE)
    cfg_save_queries = get_config_value(save_queries, yaml_config, "output.save_queries", True)
    cfg_queries_dir = get_config_value(None, yaml_config, "output.queries_dir", QUERIES_DIR)
    cfg_results_dir = get_config_value(None, yaml_config, "output.results_dir", RESULTS_DIR)

    cfg_system_template = yaml_config.get("templates", {}).get("system", DEFAULT_SYSTEM_TEMPLATE)
    cfg_business_rules = yaml_config.get("templates", {}).get("business_rules", DEFAULT_BUSINESS_RULES)

    if isinstance(cfg_queries_dir, str):
        cfg_queries_dir = Path(cfg_queries_dir)
    if isinstance(cfg_results_dir, str):
        cfg_results_dir = Path(cfg_results_dir)

    if isinstance(cfg_questions, str):
        cfg_questions = Path(cfg_questions)
    if isinstance(cfg_schema, str):
        cfg_schema = Path(cfg_schema)

    if not cfg_questions.exists():
        typer.echo(f"Erro: Arquivo de perguntas não encontrado: {cfg_questions}", err=True)
        raise typer.Exit(1)

    if not cfg_schema.exists():
        typer.echo(f"Erro: Arquivo de schema não encontrado: {cfg_schema}", err=True)
        raise typer.Exit(1)

    typer.echo("=" * 60)
    typer.echo("GERAÇÃO DE QUERIES SQL")
    typer.echo("=" * 60)
    typer.echo(f"Modelo LLM: {cfg_model}")
    typer.echo(f"Modelo RAG: {cfg_rag_model}")
    typer.echo(f"Arquivo de perguntas: {cfg_questions}")
    typer.echo(f"Schema: {cfg_schema}")
    typer.echo(f"Modo thinking: {'Sim' if cfg_enable_thinking else 'Não'}")
    typer.echo(f"Temperature: {cfg_temperature}")
    typer.echo(f"Max tokens: {cfg_max_new_tokens}")
    typer.echo(f"Run: {cfg_run}")
    typer.echo(f"Diretório de queries: {cfg_queries_dir}")
    typer.echo(f"Diretório de resultados: {cfg_results_dir}")
    typer.echo(f"Modo resume: {'Sim' if resume else 'Não'}")
    typer.echo("-" * 60)

    typer.echo("Inicializando RAG...")
    try:
        rag = initialize_rag(cfg_schema, cfg_rag_model, cfg_similarity_threshold)
        typer.echo("  ✓ RAG inicializado")
    except ImportError as e:
        typer.echo(f"Erro ao importar módulos: {e}", err=True)
        typer.echo("Certifique-se de que os pacotes estão instalados corretamente.", err=True)
        raise typer.Exit(1)
    except Exception as e:
        typer.echo(f"  ✗ Erro ao inicializar RAG: {e}", err=True)
        raise typer.Exit(1)

    typer.echo("Carregando modelo LLM...")
    try:
        llm_model = initialize_model(cfg_model)
        typer.echo("  ✓ Modelo carregado")
    except ImportError as e:
        typer.echo(f"Erro ao importar módulos: {e}", err=True)
        typer.echo("Certifique-se de que os pacotes estão instalados corretamente.", err=True)
        raise typer.Exit(1)
    except Exception as e:
        typer.echo(f"  ✗ Erro ao carregar modelo: {e}", err=True)
        raise typer.Exit(1)

    df = pd.read_csv(cfg_questions)
    typer.echo(f"  ✓ {len(df)} perguntas carregadas")

    if cfg_question_column not in df.columns:
        typer.echo(f"Erro: Coluna '{cfg_question_column}' não encontrada no CSV.", err=True)
        typer.echo(f"Colunas disponíveis: {list(df.columns)}", err=True)
        raise typer.Exit(1)

    params_config = yaml_config.get("parameters", {})
    has_params = bool(params_config.get("questions", {}))
    if has_params:
        num_questions_with_params = len(params_config.get("questions", {}))
        typer.echo(f"Parâmetros configurados: {num_questions_with_params} perguntas")

    typer.echo("-" * 60)
    typer.echo("Processando perguntas (salvamento incremental)...")

    df, csv_path, queries_path = process_questions_incremental(
        df, rag, llm_model, cfg_question_column, cfg_extra_columns,
        cfg_max_new_tokens, cfg_temperature, cfg_top_p, cfg_enable_thinking,
        cfg_max_tables, cfg_max_columns, cfg_system_template, cfg_business_rules,
        yaml_config, cfg_model, cfg_run, cfg_save_queries,
        cfg_results_dir, cfg_queries_dir, resume
    )

    typer.echo(f"  ✓ CSV salvo em: {csv_path}")
    if queries_path:
        typer.echo(f"  ✓ Queries salvas em: {queries_path}")

    typer.echo("=" * 60)
    typer.echo("Geração concluída com sucesso!")


@app.command()
def list_models() -> None:
    """Lista os modelos LLM disponíveis para geração."""
    typer.echo("Modelos disponíveis:")
    for model_name in AVAILABLE_MODELS:
        typer.echo(f"  - {model_name}")


@app.command()
def config() -> None:
    """Mostra o caminho do arquivo de configuração padrão."""
    typer.echo(f"Arquivo de configuração: {GENERATE_CONFIG_FILE}")
    if GENERATE_CONFIG_FILE.exists():
        typer.echo("Status: ✓ Existe")
    else:
        typer.echo("Status: ✗ Não encontrado")


def main() -> int:
    """
    Função principal do CLI de geração de queries.

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
