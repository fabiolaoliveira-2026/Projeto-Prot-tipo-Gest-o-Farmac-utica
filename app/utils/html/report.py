"""
Gerador de relatório HTML completo para Text2SQL.

Este módulo contém a função principal que gera o relatório HTML
auto-contido com todas as seções: Dashboard, Perguntas e Detalhes.
"""

from datetime import datetime

import pandas as pd

from app.config.paths import RESULTS_DIR

from .charts import create_metrics_chart_html, create_status_chart_html
from .components import generate_summary_html
from .styles import HTML_STYLES
from .tables import (
    generate_all_details_html,
    generate_questions_full_table_html,
    generate_questions_summary_table_html,
)


def generate_full_html_report(pair_name: str) -> str:
    """
    Gera relatório HTML completo e auto-contido com todas as páginas.

    Inclui Dashboard, Perguntas e Detalhes de cada pergunta com SQL,
    diff e métricas individuais.

    Args:
        pair_name (str): Nome do par de comparação no formato "modelo/run".

    Returns:
        String HTML completa do relatório.
    """
    metrics_path = RESULTS_DIR / pair_name / "metricas.csv"
    metrics = pd.read_csv(metrics_path) if metrics_path.exists() else None

    summary_path = RESULTS_DIR / pair_name / "resumo.csv"
    summary = pd.read_csv(summary_path) if summary_path.exists() else None

    if metrics is None or summary is None:
        return f"<html><body><h1>Erro: Dados não encontrados para {pair_name}</h1><p>Path: {metrics_path}</p></body></html>"

    model, run = pair_name.split("/", 1) if "/" in pair_name else (pair_name, "default")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    summary_html = generate_summary_html(summary, pair_name)
    metrics_chart = create_metrics_chart_html(metrics)
    status_chart = create_status_chart_html(metrics)
    questions_summary_table = generate_questions_summary_table_html(metrics)
    questions_full_table = generate_questions_full_table_html(metrics)
    all_details = generate_all_details_html(pair_name, metrics)

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Relatório Text2SQL - {model}</title>
    <style>
{HTML_STYLES}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📊 Relatório Completo Text2SQL</h1>
            <p>Modelo: {model} | Run: {run} | Gerado em: {timestamp}</p>
        </header>
        
        <nav class="toc">
            <h3>📑 Índice</h3>
            <ul>
                <li><a href="#dashboard">📊 Dashboard</a></li>
                <li><a href="#perguntas">📋 Perguntas</a></li>
                <li><a href="#detalhes">🔍 Detalhes</a></li>
            </ul>
        </nav>
        
        <section class="page-section" id="dashboard">
            <h2>📊 Dashboard</h2>
            
            {summary_html}
            
            <div class="charts-grid">
                <div class="card">
                    <div class="card-header">📈 F1 Score por Pergunta</div>
                    <div class="card-body">{metrics_chart}</div>
                </div>
                <div class="card">
                    <div class="card-header">🎯 Taxa de Execução</div>
                    <div class="card-body">{status_chart}</div>
                </div>
            </div>
            
            {questions_summary_table}
        </section>
        
        {questions_full_table}
        
        {all_details}
        
        <footer>
            <p>Relatório gerado automaticamente pelo Text2SQL Comparador</p>
            <p>© {datetime.now().year} - Todos os direitos reservados</p>
        </footer>
    </div>
</body>
</html>
    """

    return html

