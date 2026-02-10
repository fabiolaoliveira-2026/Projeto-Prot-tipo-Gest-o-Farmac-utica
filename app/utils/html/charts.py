"""
Componentes de gráficos HTML para relatórios Text2SQL.

Este módulo contém funções para criar gráficos de barras e status
como elementos HTML estilizados.
"""

import pandas as pd


def create_metrics_chart_html(metrics: pd.DataFrame) -> str:
    """
    Cria o gráfico de barras de métricas F1 como tabela HTML estilizada.

    Args:
        metrics (pd.DataFrame): DataFrame com as métricas.

    Returns:
        String HTML do gráfico como tabela de barras.
    """
    data = []
    for _, row in metrics.iterrows():
        question_id = int(row["id"])
        f1_val = row.get("f1", None)

        if pd.notna(f1_val):
            data.append({
                "id": question_id,
                "Pergunta": f"Q{question_id}",
                "F1": float(f1_val)
            })

    if not data:
        return "<p>Sem dados de F1 disponíveis</p>"

    df = pd.DataFrame(data)
    df = df.sort_values("id")

    bars_html = []
    for _, row in df.iterrows():
        pergunta = row["Pergunta"]
        f1 = row["F1"]
        width_pct = f1 * 100
        label = f"{f1:.0%}"

        bars_html.append(f"""
        <div class="bar-row">
            <div class="bar-label">{pergunta}</div>
            <div class="bar-container">
                <div class="bar-fill" style="width: {width_pct}%;"></div>
                <span class="bar-value">{label}</span>
            </div>
        </div>
        """)

    return f"""
    <div class="bar-chart">
        {''.join(bars_html)}
    </div>
    """


def create_status_chart_html(metrics: pd.DataFrame) -> str:
    """
    Cria visualização de status como cards HTML.

    Args:
        metrics (pd.DataFrame): DataFrame com as métricas.

    Returns:
        String HTML com cards de status.
    """
    if "status_modelo" not in metrics.columns:
        return "<p>Dados de status não disponíveis</p>"

    status_counts = metrics["status_modelo"].value_counts()
    total = status_counts.sum()

    sucesso = status_counts.get("sucesso", 0)
    erro = status_counts.get("erro", 0)

    sucesso_pct = (sucesso / total * 100) if total > 0 else 0
    erro_pct = (erro / total * 100) if total > 0 else 0

    return f"""
    <div class="status-chart">
        <div class="status-bar">
            <div class="status-fill success" style="width: {sucesso_pct}%;"></div>
            <div class="status-fill error" style="width: {erro_pct}%;"></div>
        </div>
        <div class="status-legend">
            <div class="status-item">
                <span class="status-dot success"></span>
                <span>Sucesso: {sucesso} ({sucesso_pct:.1f}%)</span>
            </div>
            <div class="status-item">
                <span class="status-dot error"></span>
                <span>Erro: {erro} ({erro_pct:.1f}%)</span>
            </div>
        </div>
    </div>
    """

