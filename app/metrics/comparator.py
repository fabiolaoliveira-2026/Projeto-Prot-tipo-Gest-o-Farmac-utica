"""
Funções de comparação de modelos Text2SQL.

Este módulo contém a lógica principal de comparação entre modelos e o ground truth,
gerando DataFrames com métricas detalhadas e resumos agregados.
"""

from pathlib import Path

import pandas as pd

from app.data.loaders import load_result_csv
from app.metrics.calculator import calculate_listing_metrics, compare_quantity, compare_quantity_by_value
from app.utils.dataframe import find_common_column


def get_execution_status(resumo_df: pd.DataFrame, question_id: int) -> tuple[str, float | None]:
    """
    Obtém o status de execução de uma pergunta.

    Detecta automaticamente se o arquivo usa indexação 0-based ou 1-based
    e ajusta a busca adequadamente.

    Args:
        resumo_df: DataFrame com resumo de execução.
        question_id: ID da pergunta (1-indexed).

    Returns:
        Tupla com (status, linhas_retornadas).
    """
    min_id = resumo_df["pergunta_id"].min()

    if min_id == 0:
        lookup_id = question_id - 1
    else:
        lookup_id = question_id

    row = resumo_df[resumo_df["pergunta_id"] == lookup_id]

    if row.empty:
        return "não executado", None

    status = row.iloc[0]["status"]
    linhas = row.iloc[0]["linhas_retornadas"]
    return status, linhas


def compare_runs(
    gt_path: Path,
    model_path: Path,
    questions_df: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Compara resultados de uma run do modelo com uma run do ground truth.

    Args:
        gt_path: Caminho para o diretório da run do ground truth.
        model_path: Caminho para o diretório da run do modelo.
        questions_df: DataFrame com as perguntas.

    Returns:
        Tupla com (metricas_df, resumo_df).
    """
    gt_resumo_path = gt_path / "resumo_execucao.csv"
    model_resumo_path = model_path / "resumo_execucao.csv"

    gt_resumo = pd.read_csv(gt_resumo_path)
    model_resumo = pd.read_csv(model_resumo_path)

    metrics_rows = []

    for _, question in questions_df.iterrows():
        question_id = int(question["id"])
        questao = question["Questões"]
        tipo = question["Tipo"]
        colunas_validacao = question["Colunas Validação"]

        status_gt, linhas_gt = get_execution_status(gt_resumo, question_id)
        status_modelo, linhas_modelo = get_execution_status(model_resumo, question_id)

        row = {
            "id": question_id,
            "questao": questao,
            "tipo": tipo,
            "status_gt": status_gt,
            "status_modelo": status_modelo,
            "linhas_esperadas": linhas_gt,
            "linhas_retornadas": linhas_modelo,
            "coluna_usada": None,
            "precision": None,
            "recall": None,
            "accuracy": None,
            "f1": None,
            "match": None
        }

        if status_gt != "sucesso" or status_modelo != "sucesso":
            metrics_rows.append(row)
            continue

        gt_result_path = gt_path / str(question_id) / "resultado.csv"
        model_result_path = model_path / str(question_id) / "resultado.csv"

        df_gt = load_result_csv(gt_result_path)
        df_model = load_result_csv(model_result_path)

        if df_gt is None or df_model is None:
            metrics_rows.append(row)
            continue

        if tipo == "listagem":
            common_col = find_common_column(df_gt, df_model, colunas_validacao)
            row["coluna_usada"] = common_col

            if common_col:
                gt_values = df_gt[common_col].dropna().astype(str).tolist()
                model_values = df_model[common_col].dropna().astype(str).tolist()

                metrics = calculate_listing_metrics(gt_values, model_values)
                row["precision"] = metrics["precision"]
                row["recall"] = metrics["recall"]
                row["accuracy"] = metrics["accuracy"]
                row["f1"] = metrics["f1"]

        elif tipo == "quantidade":
            if colunas_validacao and pd.notna(colunas_validacao):
                validation_col = colunas_validacao.split(",")[0].strip()
                row["coluna_usada"] = validation_col
                row["match"] = compare_quantity_by_value(df_gt, df_model, validation_col)
            else:
                row["match"] = compare_quantity(df_gt, df_model)

            metric_value = 1.0 if row["match"] else 0.0
            row["precision"] = metric_value
            row["recall"] = metric_value
            row["accuracy"] = metric_value
            row["f1"] = metric_value

        metrics_rows.append(row)

    metricas_df = pd.DataFrame(metrics_rows)

    listing_metrics = metricas_df[metricas_df["tipo"] == "listagem"]
    quantity_metrics = metricas_df[metricas_df["tipo"] == "quantidade"]

    all_precision = metricas_df["precision"].dropna()
    all_recall = metricas_df["recall"].dropna()
    all_accuracy = metricas_df["accuracy"].dropna()
    all_f1 = metricas_df["f1"].dropna()

    resumo_data = {
        "metrica": [
            "precision_media",
            "recall_media",
            "accuracy_media",
            "f1_media",
            "listagem_total",
            "listagem_comparadas",
            "quantidade_total",
            "quantidade_acertos",
            "taxa_execucao_sucesso"
        ],
        "valor": [
            round(all_precision.mean(), 4) if len(all_precision) > 0 else None,
            round(all_recall.mean(), 4) if len(all_recall) > 0 else None,
            round(all_accuracy.mean(), 4) if len(all_accuracy) > 0 else None,
            round(all_f1.mean(), 4) if len(all_f1) > 0 else None,
            len(listing_metrics),
            listing_metrics["precision"].notna().sum(),
            len(quantity_metrics),
            quantity_metrics["match"].sum() if not quantity_metrics["match"].isna().all() else 0,
            (metricas_df["status_modelo"] == "sucesso").sum() / len(metricas_df)
        ]
    }

    resumo_df = pd.DataFrame(resumo_data)

    return metricas_df, resumo_df
