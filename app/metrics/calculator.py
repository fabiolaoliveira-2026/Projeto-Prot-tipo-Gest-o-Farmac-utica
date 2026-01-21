"""
Funções de cálculo de métricas para comparação Text2SQL.

Este módulo contém as funções responsáveis por calcular métricas de precision,
recall, accuracy e F1 para perguntas de listagem, e validação exata para
perguntas de quantidade.
"""

from collections import Counter

import pandas as pd


def calculate_listing_metrics(gt_values: list, model_values: list) -> dict[str, float]:
    """
    Calcula métricas para perguntas de listagem usando multiset (considera duplicatas).
    
    Utiliza contadores para comparar listas de valores, considerando a frequência
    de cada elemento para calcular true positives corretamente.
    
    Args:
        gt_values: Lista de valores do ground truth (pode ter duplicatas).
        model_values: Lista de valores do modelo (pode ter duplicatas).
        
    Returns:
        Dicionário com precision, recall, accuracy e f1.
    """
    if not gt_values and not model_values:
        return {"precision": 1.0, "recall": 1.0, "accuracy": 1.0, "f1": 1.0}
    
    if not model_values:
        return {"precision": 0.0, "recall": 0.0, "accuracy": 0.0, "f1": 0.0}
    
    if not gt_values:
        return {"precision": 0.0, "recall": 0.0, "accuracy": 0.0, "f1": 0.0}
    
    gt_counter = Counter(gt_values)
    model_counter = Counter(model_values)
    
    true_positives = sum((gt_counter & model_counter).values())
    total_model = sum(model_counter.values())
    total_gt = sum(gt_counter.values())
    false_positives = total_model - true_positives
    
    precision = true_positives / total_model if total_model > 0 else 0.0
    recall = true_positives / total_gt if total_gt > 0 else 0.0
    accuracy = true_positives / (total_gt + false_positives) if (total_gt + false_positives) > 0 else 0.0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    
    return {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "accuracy": round(accuracy, 4),
        "f1": round(f1, 4)
    }


def compare_quantity(df_gt: pd.DataFrame, df_model: pd.DataFrame) -> bool:
    """
    Compara resultados de perguntas de quantidade.
    
    Verifica se os valores são exatamente iguais após ordenação.
    
    Args:
        df_gt: DataFrame do ground truth.
        df_model: DataFrame do modelo.
        
    Returns:
        True se os valores são iguais, False caso contrário.
    """
    if df_gt.shape != df_model.shape:
        return False
    
    try:
        gt_sorted = df_gt.sort_index(axis=1).sort_values(by=list(df_gt.columns)).reset_index(drop=True)
        model_sorted = df_model.sort_index(axis=1).sort_values(by=list(df_model.columns)).reset_index(drop=True)
        return gt_sorted.equals(model_sorted)
    except Exception:
        return False


def compare_quantity_by_value(
    df_gt: pd.DataFrame,
    df_model: pd.DataFrame,
    validation_column: str
) -> bool:
    """
    Compara perguntas de quantidade buscando o valor do ground truth em qualquer coluna do modelo.
    
    Pega o valor da coluna especificada no ground truth e verifica se esse valor
    existe em alguma coluna do resultado do modelo. Isso permite que a IA retorne
    o valor correto mesmo com um nome de coluna diferente.
    
    Args:
        df_gt (pd.DataFrame): DataFrame do ground truth.
        df_model (pd.DataFrame): DataFrame do modelo.
        validation_column (str): Nome da coluna no ground truth que contém o valor esperado.
        
    Returns:
        bool: True se o valor do ground truth foi encontrado em alguma coluna do modelo.
    """
    if df_gt.empty or df_model.empty:
        return False
    
    validation_column_normalized = validation_column.strip().lower()
    gt_cols_normalized = {col.lower(): col for col in df_gt.columns}
    
    if validation_column_normalized not in gt_cols_normalized:
        return False
    
    original_col_name = gt_cols_normalized[validation_column_normalized]
    gt_value = df_gt[original_col_name].iloc[0]
    
    try:
        gt_value_numeric = pd.to_numeric(gt_value, errors="coerce")
    except (ValueError, TypeError):
        gt_value_numeric = None
    
    for col in df_model.columns:
        model_value = df_model[col].iloc[0]
        
        if str(gt_value) == str(model_value):
            return True
        
        if gt_value_numeric is not None and pd.notna(gt_value_numeric):
            try:
                model_value_numeric = pd.to_numeric(model_value, errors="coerce")
                if pd.notna(model_value_numeric) and gt_value_numeric == model_value_numeric:
                    return True
            except (ValueError, TypeError):
                pass
    
    return False

