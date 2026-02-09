"""
CLI para geração de queries SQL a partir de perguntas em linguagem natural.

Este módulo fornece uma interface de linha de comando para processar
um arquivo CSV de perguntas e gerar consultas SQL utilizando um modelo
de linguagem com suporte a RAG (Retrieval-Augmented Generation).
"""

import argparse
import os
import re
import sys
from pathlib import Path
from typing import Optional

import pandas as pd
from dotenv import load_dotenv
from tqdm import tqdm

from app.config.paths import (
    CACHE_DIR,
    DATA_DIR,
    QUERIES_DIR,
    QUESTIONS_FILE,
    RESULTS_DIR,
    SCHEMA_FILE,
)


DEFAULT_RAG_MODEL = "neuralmind/bert-large-portuguese-cased"
DEFAULT_SIMILARITY_THRESHOLD = 0.3
DEFAULT_MAX_TABLES = 5
DEFAULT_MAX_COLUMNS_PER_TABLE = 20
DEFAULT_MAX_CONTEXT_LENGTH = 32768

DEFAULT_SYSTEM_TEMPLATE = """Você é um conversor de linguagem natural para SQL.
Sua tarefa é converter perguntas em linguagem natural em consultas SQL precisas.

Contexto do Banco de Dados:
{context}

Regras de negócio:
{business_rules}

Diretrizes Importantes:
- Sempre utilize os nomes de tabelas e colunas corretos, conforme mostrado no contexto.
- Utilize JOINs explícitos ao acessar múltiplas tabelas.
- Utilize cláusulas WHERE apropriadas para filtragem.
- Considere valores NULL em suas consultas.
- Utilize funções de agregação (SUM, COUNT, AVG) quando apropriado.
- Sempre utilize aliases para as tabelas para maior clareza.
- Quando existir operações de única coluna no select, nomeie a coluna com o nome de antes da operação.

Regras de Resposta:
1. NÃO inicie com "Aqui está o SQL" ou explicações.
2. NÃO utilize blocos de código markdown (```sql). Retorne apenas o texto cru da query.
3. NÃO inclua comentários ou notas finais.

Output esperado: Apenas a string SQL válida iniciada por SELECT.
"""

DEFAULT_BUSINESS_RULES = """## Valores não informados:
Ao ser solicitado um valor não informado, considere como 'X' para o valor.

## Definição de estoque crítico:
Estoque crítico é o nível mínimo de estoque abaixo do qual existe risco de desabastecimento.
Considera-se estoque crítico quando a cobertura é igual ou menor que 15 dias de consumo médio.

## Consumo médio mensal:
O consumo médio mensal é calculado considerando os últimos 3 meses.
"""


def sanitize_sql_output(raw_text: str) -> str:
    """
    Remove marcadores especiais e formata o SQL final.

    Args:
        raw_text: Texto bruto retornado pelo modelo.

    Returns:
        SQL limpo e formatado.
    """
    cleaned = re.sub(r"<\|\S+\|>|```sql|```", "", raw_text)
    if "</think>" in cleaned:
        cleaned = cleaned[cleaned.find("</think>") + len("</think>"):]
    return cleaned.strip()


def predict(
    rag_engine,
    question: str,
    system_template: str,
    business_rules: str,
    rag_config: dict,
    model,
    model_config: dict
) -> tuple[str, str]:
    """
    Gera uma query SQL a partir de uma pergunta em linguagem natural.

    Args:
        rag_engine: Instância do Text2SQLWithRAG.
        question: Pergunta em linguagem natural.
        system_template: Template do sistema para o prompt.
        business_rules: Regras de negócio para incluir no prompt.
        rag_config: Configurações do RAG (max_tables, max_columns_per_table, etc).
        model: Instância do TransformerModel.
        model_config: Configurações de geração do modelo.

    Returns:
        Tupla contendo (sql_gerado, conteudo_thinking).
    """
    prompt_payload = rag_engine.get_enhanced_prompt(
        question,
        system_template=system_template.format(context="{context}", business_rules=business_rules),
        max_tables=rag_config.get("max_tables", DEFAULT_MAX_TABLES),
        max_columns_per_table=rag_config.get("max_columns_per_table", DEFAULT_MAX_COLUMNS_PER_TABLE),
        max_context_length=rag_config.get("max_context_length", DEFAULT_MAX_CONTEXT_LENGTH),
    )

    prompt = model.generate_prompt(
        system=prompt_payload["system"].format(context="{context}", business_rules=business_rules),
        user=prompt_payload["user"],
        enable_thinking=model_config.get("enable_thinking", False)
    )
    response = model.generate(prompt, model_config=model_config)

    if model_config.get("enable_thinking") and isinstance(response, dict):
        sql_content = sanitize_sql_output(response.get("content", ""))
        thinking_content = response.get("thinking", "")
        return (sql_content, thinking_content)
    else:
        sql_content = sanitize_sql_output(response if isinstance(response, str) else response.get("content", ""))
        return (sql_content, "")


def get_available_models() -> list[str]:
    """
    Retorna lista de modelos candidatos disponíveis.

    Returns:
        Lista com nomes dos modelos.
    """
    return [
        "meta-llama/Meta-Llama-3.1-8B-Instruct",
        "Qwen/Qwen3-4B-Thinking-2507",
        "Qwen/Qwen3-14B-FP8",
        "Qwen/Qwen3-32B-AWQ",
        "Qwen/Qwen3-8B",
        "deepseek-ai/deepseek-coder-7b-instruct-v1.5",
        "Snowflake/Arctic-Text2SQL-R1-7B",
    ]


def build_question_prompt(row: pd.Series, question_column: str, extra_columns: list[str]) -> str:
    """
    Constrói o prompt da pergunta a partir de uma linha do DataFrame.

    Args:
        row: Linha do DataFrame.
        question_column: Nome da coluna com a pergunta.
        extra_columns: Colunas adicionais para incluir no prompt.

    Returns:
        Prompt formatado com a pergunta e informações extras.
    """
    parts = [f"Pergunta: {row[question_column]}"]
    for col in extra_columns:
        if col in row and pd.notna(row[col]):
            parts.append(f"{col}: {row[col]}")
    return "\n".join(parts)


def main() -> int:
    """
    Função principal do CLI de geração de queries.

    Processa argumentos de linha de comando e executa a geração de queries SQL
    a partir de perguntas em linguagem natural.

    Returns:
        Código de saída (0 para sucesso, 1 para erro).
    """
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="Gera queries SQL a partir de perguntas em linguagem natural.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  %(prog)s                              # Usa modelo padrão
  %(prog)s --model Qwen/Qwen3-8B        # Especifica modelo
  %(prog)s --enable-thinking            # Ativa modo de raciocínio
  %(prog)s --output-suffix _v2          # Adiciona sufixo ao nome da saída
        """
    )

    parser.add_argument(
        "--model", "-m",
        type=str,
        default="Qwen/Qwen3-32B-AWQ",
        help="Nome do modelo LLM a utilizar (padrão: Qwen/Qwen3-32B-AWQ)"
    )

    parser.add_argument(
        "--questions", "-q",
        type=Path,
        default=QUESTIONS_FILE,
        help=f"Caminho para o arquivo CSV de perguntas (padrão: {QUESTIONS_FILE})"
    )

    parser.add_argument(
        "--question-column",
        type=str,
        default="Questões",
        help="Nome da coluna com as perguntas (padrão: Questões)"
    )

    parser.add_argument(
        "--extra-columns",
        type=str,
        nargs="*",
        default=["Tipo de dado necessário", "Intenção"],
        help="Colunas extras para incluir no prompt"
    )

    parser.add_argument(
        "--schema", "-s",
        type=Path,
        default=SCHEMA_FILE,
        help=f"Caminho para o arquivo YAML do schema (padrão: {SCHEMA_FILE})"
    )

    parser.add_argument(
        "--output-suffix",
        type=str,
        default="_br",
        help="Sufixo para o diretório de saída (padrão: _br)"
    )

    parser.add_argument(
        "--enable-thinking",
        action="store_true",
        help="Ativa o modo de raciocínio (thinking) para modelos que suportam"
    )

    parser.add_argument(
        "--max-new-tokens",
        type=int,
        default=32768,
        help="Número máximo de tokens a gerar (padrão: 32768)"
    )

    parser.add_argument(
        "--temperature",
        type=float,
        default=0.0001,
        help="Temperatura para geração (padrão: 0.0001)"
    )

    parser.add_argument(
        "--rag-model",
        type=str,
        default=DEFAULT_RAG_MODEL,
        help=f"Modelo sentence-transformers para RAG (padrão: {DEFAULT_RAG_MODEL})"
    )

    parser.add_argument(
        "--similarity-threshold",
        type=float,
        default=DEFAULT_SIMILARITY_THRESHOLD,
        help=f"Threshold de similaridade RAG (padrão: {DEFAULT_SIMILARITY_THRESHOLD})"
    )

    parser.add_argument(
        "--max-tables",
        type=int,
        default=DEFAULT_MAX_TABLES,
        help=f"Máximo de tabelas no contexto (padrão: {DEFAULT_MAX_TABLES})"
    )

    parser.add_argument(
        "--max-columns",
        type=int,
        default=DEFAULT_MAX_COLUMNS_PER_TABLE,
        help=f"Máximo de colunas por tabela (padrão: {DEFAULT_MAX_COLUMNS_PER_TABLE})"
    )

    parser.add_argument(
        "--save-queries",
        action="store_true",
        default=True,
        help="Salva cada query em arquivo .sql separado (padrão: True)"
    )

    parser.add_argument(
        "--no-save-queries",
        action="store_false",
        dest="save_queries",
        help="Não salva queries em arquivos separados"
    )

    parser.add_argument(
        "--list-models",
        action="store_true",
        help="Lista modelos disponíveis e sai"
    )

    args = parser.parse_args()

    if args.list_models:
        print("Modelos disponíveis:")
        for model in get_available_models():
            print(f"  - {model}")
        return 0

    if not args.questions.exists():
        print(f"Erro: Arquivo de perguntas não encontrado: {args.questions}")
        return 1

    if not args.schema.exists():
        print(f"Erro: Arquivo de schema não encontrado: {args.schema}")
        return 1

    print("=" * 60)
    print("GERAÇÃO DE QUERIES SQL")
    print("=" * 60)
    print(f"Modelo LLM: {args.model}")
    print(f"Modelo RAG: {args.rag_model}")
    print(f"Arquivo de perguntas: {args.questions}")
    print(f"Schema: {args.schema}")
    print(f"Modo thinking: {'Sim' if args.enable_thinking else 'Não'}")
    print("-" * 60)

    try:
        from app.llm.model.transformer import TransformerModel
        from app.llm.rag import Text2SQLWithRAG
    except ImportError as e:
        print(f"Erro ao importar módulos: {e}")
        print("Certifique-se de que os pacotes estão instalados corretamente.")
        return 1

    print("Inicializando RAG...")
    try:
        rag = Text2SQLWithRAG(
            schema_path=str(args.schema),
            model_name=args.rag_model,
            similarity_threshold=args.similarity_threshold,
            cache_dir=str(CACHE_DIR)
        )
        print("  ✓ RAG inicializado")
    except Exception as e:
        print(f"  ✗ Erro ao inicializar RAG: {e}")
        return 1

    print("Carregando modelo LLM...")
    try:
        model = TransformerModel()
        token = os.environ.get("LLM_TOKEN") if "Meta" in args.model else None
        model.load_transformer_model(args.model, token=token)
        print("  ✓ Modelo carregado")
    except Exception as e:
        print(f"  ✗ Erro ao carregar modelo: {e}")
        return 1

    df = pd.read_csv(args.questions)
    print(f"  ✓ {len(df)} perguntas carregadas")

    if args.question_column not in df.columns:
        print(f"Erro: Coluna '{args.question_column}' não encontrada no CSV.")
        print(f"Colunas disponíveis: {list(df.columns)}")
        return 1

    model_config = {
        "max_new_tokens": args.max_new_tokens,
        "temperature": args.temperature,
        "do_sample": True,
        "top_p": 0.95,
        "enable_thinking": args.enable_thinking
    }

    rag_config = {
        "max_tables": args.max_tables,
        "max_columns_per_table": args.max_columns,
        "max_context_length": DEFAULT_MAX_CONTEXT_LENGTH
    }

    print("-" * 60)
    print("Processando perguntas...")
    tqdm.pandas()

    results = df.progress_apply(
        lambda row: predict(
            rag,
            build_question_prompt(row, args.question_column, args.extra_columns),
            DEFAULT_SYSTEM_TEMPLATE,
            DEFAULT_BUSINESS_RULES,
            rag_config,
            model,
            model_config
        ),
        axis=1
    )

    df["SQL"] = results.apply(lambda x: x[0] if isinstance(x, tuple) else x)
    if args.enable_thinking:
        df["Thinking"] = results.apply(lambda x: x[1] if isinstance(x, tuple) else "")

    model_short_name = args.model.split("/")[-1]
    output_dir_name = f"{model_short_name}{args.output_suffix}"

    csv_save_path = RESULTS_DIR / output_dir_name / "sql.csv"
    csv_save_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(csv_save_path, index=False)
    print(f"  ✓ CSV salvo em: {csv_save_path}")

    if args.save_queries:
        queries_save_path = QUERIES_DIR / output_dir_name
        queries_save_path.mkdir(parents=True, exist_ok=True)
        for i, sql in enumerate(df["SQL"].values, start=1):
            query_file = queries_save_path / f"{i}.sql"
            query_file.write_text(sql)
        print(f"  ✓ Queries salvas em: {queries_save_path}")

    print("=" * 60)
    print("Geração concluída com sucesso!")
    return 0


if __name__ == "__main__":
    sys.exit(main())

