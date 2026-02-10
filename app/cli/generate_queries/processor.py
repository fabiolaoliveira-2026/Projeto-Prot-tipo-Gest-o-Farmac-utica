"""
Processador de perguntas para geração de queries SQL.

Este módulo contém a lógica de processamento incremental de perguntas,
gerando queries SQL e salvando resultados.
"""

from pathlib import Path

import pandas as pd
import typer
from tqdm import tqdm

from app.config.constants import DEFAULT_MAX_CONTEXT_LENGTH
from app.utils.parameters import get_question_parameters

from .generator import predict
from .utils import build_question_prompt


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
        df (pd.DataFrame): DataFrame com as perguntas.
        rag: Instância do Text2SQLWithRAG.
        model: Instância do TransformerModel.
        question_column (str): Nome da coluna com as perguntas.
        extra_columns (list[str]): Colunas extras para incluir no prompt.
        max_new_tokens (int): Número máximo de tokens a gerar.
        temperature (float): Temperatura para geração.
        top_p (float): Top-p para geração.
        enable_thinking (bool): Se ativa o modo de raciocínio.
        max_tables (int): Máximo de tabelas no contexto.
        max_columns (int): Máximo de colunas por tabela.
        system_template (str): Template do sistema para o prompt.
        business_rules (str): Regras de negócio para o prompt.
        yaml_config (dict): Configuração YAML com parâmetros de substituição.
        model_name (str): Nome do modelo utilizado.
        run_name (str): Nome da run (execução).
        save_queries (bool): Se deve salvar queries em arquivos separados.
        results_dir (Path): Diretório base para salvar resultados CSV.
        queries_dir (Path): Diretório base para salvar queries SQL.
        resume (bool): Se deve retomar de onde parou (default True).

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

