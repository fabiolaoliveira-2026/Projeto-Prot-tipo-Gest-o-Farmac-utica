"""
Funções de inicialização para geração de queries SQL.

Este módulo contém as funções responsáveis por inicializar os componentes
do pipeline de geração: RAG engine e modelo LLM.
"""

import os
from pathlib import Path

from app.config.paths import CACHE_DIR


def initialize_rag(schema_path: Path, rag_model: str, similarity_threshold: float):
    """
    Inicializa o engine RAG para recuperação de contexto.

    Args:
        schema_path (Path): Caminho para o arquivo YAML do schema.
        rag_model (str): Nome do modelo sentence-transformers.
        similarity_threshold (float): Threshold de similaridade para recuperação.

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
        model_name (str): Nome do modelo no Hugging Face Hub.

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

