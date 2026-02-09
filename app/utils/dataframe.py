"""
Utilitários para manipulação de DataFrames.

Este módulo contém funções auxiliares para normalização e operações
comuns em DataFrames pandas.
"""

import pandas as pd


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normaliza os nomes das colunas de um DataFrame.
    
    Converte para minúsculo e remove espaços extras.
    
    Args:
        df: DataFrame a ser normalizado.
        
    Returns:
        DataFrame com colunas normalizadas.
    """
    df.columns = df.columns.str.lower().str.strip()
    return df


def find_common_column(df_gt: pd.DataFrame, df_model: pd.DataFrame, validation_columns: str) -> str | None:
    """
    Encontra a primeira coluna comum entre ground truth e modelo.
    
    Percorre a lista de colunas de validação e retorna a primeira
    que exista em ambos os DataFrames.
    
    Args:
        df_gt: DataFrame do ground truth.
        df_model: DataFrame do modelo.
        validation_columns: String com colunas separadas por vírgula.
        
    Returns:
        Nome da coluna comum encontrada ou None se nenhuma for encontrada.
    """
    if not validation_columns or pd.isna(validation_columns):
        return None
    
    columns = [col.strip().lower() for col in validation_columns.split(",")]
    gt_cols = set(df_gt.columns)
    model_cols = set(df_model.columns)
    
    for col in columns:
        if col in gt_cols and col in model_cols:
            return col
    
    return None

