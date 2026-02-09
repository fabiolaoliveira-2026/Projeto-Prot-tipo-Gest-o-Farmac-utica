"""
CLI para criação e gerenciamento do índice RAG do schema do banco de dados.

Este módulo fornece uma interface de linha de comando para criar e reconstruir
o índice de embeddings usado pelo sistema RAG (Retrieval-Augmented Generation)
para recuperação de contexto do schema do banco de dados.
"""

import sys
from pathlib import Path
from typing import Annotated, Optional

import typer

from app.cli.config_loader import get_config_value, load_yaml_config
from app.config.paths import CACHE_DIR, RAG_INDEX_CONFIG_FILE, SCHEMA_FILE

app = typer.Typer(
    name="text2sql-rag-index",
    help="Cria e gerencia o índice RAG do schema do banco de dados.",
    add_completion=False,
)

DEFAULT_MODEL_NAME = "neuralmind/bert-large-portuguese-cased"
DEFAULT_THRESHOLD = 0.3


def _create_index(
    schema_path: Path,
    model_name: str,
    cache_dir: Path,
    force_rebuild: bool
) -> bool:
    """
    Cria ou reconstrói o índice de embeddings do schema.

    Args:
        schema_path: Caminho para o arquivo YAML do schema.
        model_name: Nome do modelo sentence-transformers a utilizar.
        cache_dir: Diretório para armazenar o cache dos embeddings.
        force_rebuild: Se True, força a reconstrução mesmo se o cache existir.

    Returns:
        True se o índice foi criado com sucesso, False caso contrário.
    """
    try:
        from app.llm.rag import SchemaIndexer
    except ImportError as e:
        typer.echo(f"Erro ao importar SchemaIndexer: {e}", err=True)
        typer.echo("Certifique-se de que o pacote app.llm está instalado corretamente.", err=True)
        return False

    if not schema_path.exists():
        typer.echo(f"Erro: Arquivo de schema não encontrado: {schema_path}", err=True)
        return False

    typer.echo("Configuração:")
    typer.echo(f"  Schema: {schema_path}")
    typer.echo(f"  Modelo: {model_name}")
    typer.echo(f"  Cache: {cache_dir}")
    typer.echo(f"  Forçar reconstrução: {force_rebuild}")
    typer.echo("-" * 50)

    try:
        indexer = SchemaIndexer(
            schema_path=str(schema_path),
            model_name=model_name,
            cache_dir=str(cache_dir)
        )

        indexer.build_index(force_rebuild=force_rebuild)

        typer.echo("-" * 50)
        typer.echo("✓ Índice criado com sucesso!")
        return True

    except Exception as e:
        typer.echo(f"✗ Erro ao criar índice: {e}", err=True)
        return False


def _test_retriever(
    schema_path: Path,
    model_name: str,
    cache_dir: Path,
    question: str,
    similarity_threshold: float
) -> bool:
    """
    Testa o retriever com uma pergunta de exemplo.

    Args:
        schema_path: Caminho para o arquivo YAML do schema.
        model_name: Nome do modelo sentence-transformers.
        cache_dir: Diretório do cache dos embeddings.
        question: Pergunta para testar o retriever.
        similarity_threshold: Threshold de similaridade para recuperação.

    Returns:
        True se o teste foi executado com sucesso, False caso contrário.
    """
    try:
        from app.llm.rag import SchemaIndexer, SchemaRetriever
    except ImportError as e:
        typer.echo(f"Erro ao importar módulos RAG: {e}", err=True)
        return False

    if not schema_path.exists():
        typer.echo(f"Erro: Arquivo de schema não encontrado: {schema_path}", err=True)
        return False

    try:
        indexer = SchemaIndexer(
            schema_path=str(schema_path),
            model_name=model_name,
            cache_dir=str(cache_dir)
        )

        retriever = SchemaRetriever(indexer, similarity_threshold=similarity_threshold)
        context = retriever.get_context_for_query(
            question,
            max_columns_per_table=20,
            include_scores=False
        )

        typer.echo(f"Pergunta: {question}")
        typer.echo("-" * 50)
        typer.echo("Contexto recuperado:")
        typer.echo(context)
        return True

    except Exception as e:
        typer.echo(f"✗ Erro ao testar retriever: {e}", err=True)
        return False


@app.command()
def build(
    config: Annotated[
        Optional[Path],
        typer.Option("--config", "-c", help="Arquivo YAML de configuração.")
    ] = RAG_INDEX_CONFIG_FILE,
    schema: Annotated[
        Optional[Path],
        typer.Option("--schema", "-s", help="Caminho para o arquivo YAML do schema.")
    ] = None,
    model: Annotated[
        Optional[str],
        typer.Option("--model", "-m", help="Nome do modelo sentence-transformers.")
    ] = None,
    cache_dir: Annotated[
        Optional[Path],
        typer.Option("--cache-dir", help="Diretório para cache dos embeddings.")
    ] = None,
    force: Annotated[
        Optional[bool],
        typer.Option("--force/--no-force", "-f", help="Força reconstrução do índice.")
    ] = None,
) -> None:
    """
    Cria ou reconstrói o índice de embeddings do schema.

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

    cfg_schema = get_config_value(schema, yaml_config, "paths.schema", SCHEMA_FILE)
    cfg_model = get_config_value(model, yaml_config, "rag.model_name", DEFAULT_MODEL_NAME)
    cfg_cache_dir = get_config_value(cache_dir, yaml_config, "paths.cache_dir", CACHE_DIR)
    cfg_force = get_config_value(force, yaml_config, "rag.force_rebuild", False)

    if isinstance(cfg_schema, str):
        cfg_schema = Path(cfg_schema)
    if isinstance(cfg_cache_dir, str):
        cfg_cache_dir = Path(cfg_cache_dir)

    success = _create_index(
        schema_path=cfg_schema,
        model_name=cfg_model,
        cache_dir=cfg_cache_dir,
        force_rebuild=cfg_force
    )
    if not success:
        raise typer.Exit(1)


@app.command()
def test(
    question: Annotated[
        str,
        typer.Argument(help="Pergunta para testar o retriever.")
    ],
    config: Annotated[
        Optional[Path],
        typer.Option("--config", "-c", help="Arquivo YAML de configuração.")
    ] = RAG_INDEX_CONFIG_FILE,
    schema: Annotated[
        Optional[Path],
        typer.Option("--schema", "-s", help="Caminho para o arquivo YAML do schema.")
    ] = None,
    model: Annotated[
        Optional[str],
        typer.Option("--model", "-m", help="Nome do modelo sentence-transformers.")
    ] = None,
    cache_dir: Annotated[
        Optional[Path],
        typer.Option("--cache-dir", help="Diretório para cache dos embeddings.")
    ] = None,
    threshold: Annotated[
        Optional[float],
        typer.Option("--threshold", "-t", help="Threshold de similaridade para o retriever.")
    ] = None,
) -> None:
    """
    Testa o retriever com uma pergunta de exemplo.

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

    cfg_schema = get_config_value(schema, yaml_config, "paths.schema", SCHEMA_FILE)
    cfg_model = get_config_value(model, yaml_config, "rag.model_name", DEFAULT_MODEL_NAME)
    cfg_cache_dir = get_config_value(cache_dir, yaml_config, "paths.cache_dir", CACHE_DIR)
    cfg_threshold = get_config_value(threshold, yaml_config, "rag.similarity_threshold", DEFAULT_THRESHOLD)

    if isinstance(cfg_schema, str):
        cfg_schema = Path(cfg_schema)
    if isinstance(cfg_cache_dir, str):
        cfg_cache_dir = Path(cfg_cache_dir)

    success = _test_retriever(
        schema_path=cfg_schema,
        model_name=cfg_model,
        cache_dir=cfg_cache_dir,
        question=question,
        similarity_threshold=cfg_threshold
    )
    if not success:
        raise typer.Exit(1)


@app.command()
def show_config() -> None:
    """Mostra o caminho do arquivo de configuração padrão."""
    typer.echo(f"Arquivo de configuração: {RAG_INDEX_CONFIG_FILE}")
    if RAG_INDEX_CONFIG_FILE.exists():
        typer.echo("Status: ✓ Existe")
    else:
        typer.echo("Status: ✗ Não encontrado")


def main() -> int:
    """
    Função principal do CLI de criação do índice RAG.

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
