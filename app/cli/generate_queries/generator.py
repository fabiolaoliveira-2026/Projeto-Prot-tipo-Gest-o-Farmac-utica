"""
Gerador de queries SQL usando LLM com RAG.

Contém a lógica principal de geração de queries SQL a partir
de perguntas em linguagem natural utilizando modelos de linguagem
com suporte a RAG (Retrieval-Augmented Generation).
"""

from .config import DEFAULT_MAX_COLUMNS_PER_TABLE, DEFAULT_MAX_CONTEXT_LENGTH, DEFAULT_MAX_TABLES
from .utils import sanitize_sql_output


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

