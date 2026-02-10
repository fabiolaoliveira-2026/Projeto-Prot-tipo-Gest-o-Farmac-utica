"""
Componentes HTML auxiliares para relatórios Text2SQL.

Este módulo contém funções para criar componentes HTML reutilizáveis
como resumos, métricas e conversão de DataFrames.
"""

import pandas as pd


def generate_summary_html(summary: pd.DataFrame, pair_name: str) -> str:
    """
    Gera HTML do resumo de métricas.

    Args:
        summary (pd.DataFrame): DataFrame de resumo.
        pair_name (str): Nome do par de comparação.

    Returns:
        String HTML do resumo.
    """
    from app.data.loaders import get_summary_value

    precision = get_summary_value(summary, "precision_media")
    recall = get_summary_value(summary, "recall_media")
    f1 = get_summary_value(summary, "f1_media")
    success_rate = get_summary_value(summary, "taxa_execucao_sucesso")

    precision_str = f"{precision:.2%}" if precision is not None else "N/A"
    recall_str = f"{recall:.2%}" if recall is not None else "N/A"
    f1_str = f"{f1:.2%}" if f1 is not None else "N/A"
    success_str = f"{success_rate:.1%}" if success_rate is not None else "N/A"

    model, run = pair_name.split("/", 1) if "/" in pair_name else (pair_name, "default")

    return f"""
    <div class="summary-section">
        <h2>📊 Resumo de Métricas</h2>
        <p><strong>Modelo:</strong> {model}</p>
        <p><strong>Run:</strong> {run}</p>
        
        <div class="metrics-grid">
            <div class="metric-card precision">
                <div class="metric-title">Precisão Média</div>
                <div class="metric-value">{precision_str}</div>
            </div>
            <div class="metric-card recall">
                <div class="metric-title">Recall Médio</div>
                <div class="metric-value">{recall_str}</div>
            </div>
            <div class="metric-card f1">
                <div class="metric-title">F1 Médio</div>
                <div class="metric-value">{f1_str}</div>
            </div>
            <div class="metric-card success-rate">
                <div class="metric-title">Taxa de Sucesso</div>
                <div class="metric-value">{success_str}</div>
            </div>
        </div>
    </div>
    """


def dataframe_to_html(df: pd.DataFrame) -> str:
    """
    Converte um DataFrame para tabela HTML formatada.

    Args:
        df (pd.DataFrame): DataFrame a ser convertido.

    Returns:
        String HTML da tabela.
    """
    if df is None or df.empty:
        return "<p>Sem dados</p>"

    headers = "".join([f"<th>{col}</th>" for col in df.columns])
    rows = []
    for _, row in df.iterrows():
        cells = "".join([f"<td>{val}</td>" for val in row.values])
        rows.append(f"<tr>{cells}</tr>")

    return f"""
    <table class="preview-table">
        <thead><tr>{headers}</tr></thead>
        <tbody>{''.join(rows)}</tbody>
    </table>
    """
