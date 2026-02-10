"""
Módulo de exportação de relatórios para HTML auto-contido.

Este módulo gera um arquivo HTML único e auto-contido com todos os estilos,
gráficos e dados embutidos, permitindo visualização offline do relatório
de comparação Text2SQL. Inclui todas as seções: Dashboard, Perguntas e Detalhes.
"""

from datetime import datetime

import pandas as pd

from app.config.theme import COLORS
from app.config.paths import RESULTS_DIR
from app.data.loaders import (
    get_question_with_params,
    get_summary_value,
    load_pair_metrics,
    load_pair_result_preview,
    load_pair_summary,
    load_sql_file,
)
from app.utils.sql_formatter import format_sql


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
        f1 = float(f1_val) if pd.notna(f1_val) else 0.0

        data.append({
            "id": question_id,
            "Pergunta": f"Q{question_id}",
            "F1": f1
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


def generate_summary_html(summary: pd.DataFrame, pair_name: str) -> str:
    """
    Gera HTML do resumo de métricas.

    Args:
        summary (pd.DataFrame): DataFrame de resumo.
        pair_name (str): Nome do par de comparação.

    Returns:
        String HTML do resumo.
    """
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


def generate_questions_summary_table_html(metrics: pd.DataFrame) -> str:
    """
    Gera tabela HTML de resumo por pergunta (versão compacta do Dashboard).

    Args:
        metrics (pd.DataFrame): DataFrame com as métricas.

    Returns:
        String HTML da tabela.
    """
    rows = []
    for _, row in metrics.iterrows():
        question_id = int(row["id"])
        question_info = get_question_with_params(question_id)
        questao = question_info["questao"] or row["questao"]
        tipo = row["tipo"]
        status_modelo = row["status_modelo"]

        if status_modelo == "erro":
            resultado = "❌ Erro"
            resultado_class = "error"
        elif tipo == "listagem":
            f1 = row.get("f1", 0)
            if pd.notna(f1) and f1 >= 0.8:
                resultado = "✅ Correto"
                resultado_class = "success"
            elif pd.notna(f1) and f1 >= 0.5:
                resultado = "⚠️ Parcial"
                resultado_class = "warning"
            else:
                resultado = "❌ Incorreto"
                resultado_class = "error"
        elif tipo == "quantidade":
            match_val = row.get("match", False)
            if match_val is True or str(match_val).lower() == "true":
                resultado = "✅ Correto"
                resultado_class = "success"
            else:
                resultado = "❌ Incorreto"
                resultado_class = "error"
        else:
            resultado = "❓ Desconhecido"
            resultado_class = ""

        rows.append(f"""
        <tr>
            <td class="center">{question_id}</td>
            <td>{questao[:80]}{'...' if len(questao) > 80 else ''}</td>
            <td class="center">{tipo}</td>
            <td class="center {resultado_class}">{resultado}</td>
        </tr>
        """)

    return f"""
    <div class="card">
        <div class="card-header">📋 Resumo por Pergunta</div>
        <div class="card-body">
            <table class="data-table">
                <thead>
                    <tr>
                        <th class="center" style="width: 60px;">ID</th>
                        <th>Pergunta</th>
                        <th class="center" style="width: 100px;">Tipo</th>
                        <th class="center" style="width: 120px;">Resultado</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join(rows)}
                </tbody>
            </table>
        </div>
    </div>
    """


def generate_questions_full_table_html(metrics: pd.DataFrame) -> str:
    """
    Gera tabela HTML completa de perguntas (página Perguntas).

    Args:
        metrics (pd.DataFrame): DataFrame com as métricas.

    Returns:
        String HTML da tabela completa.
    """
    rows = []
    for _, row in metrics.iterrows():
        question_id = int(row["id"])
        question_info = get_question_with_params(question_id)
        questao = question_info["questao"] or row["questao"]
        tipo = row["tipo"]
        status_modelo = row["status_modelo"]
        linhas_esperadas = row.get("linhas_esperadas", "N/A")
        linhas_retornadas = row.get("linhas_retornadas", "N/A")

        precision = row.get("precision", None)
        recall = row.get("recall", None)
        accuracy = row.get("accuracy", None)
        f1_val = row.get("f1", None)
        match_val = row.get("match", None)

        precision_str = f"{precision:.2%}" if pd.notna(precision) else "N/A"
        recall_str = f"{recall:.2%}" if pd.notna(recall) else "N/A"
        accuracy_str = f"{accuracy:.2%}" if pd.notna(accuracy) else "N/A"
        f1_str = f"{f1_val:.2%}" if pd.notna(f1_val) else "N/A"

        if tipo == "quantidade":
            if match_val is True or str(match_val).lower() == "true":
                match_str = "✅ Sim"
            elif match_val is False or str(match_val).lower() == "false":
                match_str = "❌ Não"
            else:
                match_str = "N/A"
        else:
            match_str = "-"

        status_class = "success" if status_modelo == "sucesso" else "error"

        rows.append(f"""
        <tr>
            <td class="center">{question_id}</td>
            <td>{questao}</td>
            <td class="center">{tipo}</td>
            <td class="center {status_class}">{status_modelo}</td>
            <td class="center">{linhas_esperadas}</td>
            <td class="center">{linhas_retornadas}</td>
            <td class="center">{precision_str}</td>
            <td class="center">{recall_str}</td>
            <td class="center">{accuracy_str}</td>
            <td class="center">{f1_str}</td>
            <td class="center">{match_str}</td>
        </tr>
        """)

    return f"""
    <section class="page-section" id="perguntas">
        <h2>📋 Perguntas - Tabela Completa</h2>
        <div class="table-container">
            <table class="data-table full-width">
                <thead>
                    <tr>
                        <th class="center" style="width: 50px;">ID</th>
                        <th>Pergunta</th>
                        <th class="center" style="width: 90px;">Tipo</th>
                        <th class="center" style="width: 80px;">Status</th>
                        <th class="center" style="width: 80px;">Linhas Esp.</th>
                        <th class="center" style="width: 80px;">Linhas Ret.</th>
                        <th class="center" style="width: 80px;">Precisão</th>
                        <th class="center" style="width: 70px;">Recall</th>
                        <th class="center" style="width: 80px;">Accuracy</th>
                        <th class="center" style="width: 60px;">F1</th>
                        <th class="center" style="width: 70px;">Match</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join(rows)}
                </tbody>
            </table>
        </div>
    </section>
    """


def generate_question_detail_html(
    question_id: int,
    pair_name: str,
    metrics: pd.DataFrame
) -> str:
    """
    Gera HTML detalhado de uma pergunta específica.

    Args:
        question_id (int): ID da pergunta.
        pair_name (str): Nome do par de comparação.
        metrics (pd.DataFrame): DataFrame com as métricas.

    Returns:
        String HTML com detalhes da pergunta.
    """
    row = metrics[metrics["id"] == question_id]
    if row.empty:
        return ""

    row = row.iloc[0]
    question_info = get_question_with_params(question_id)
    questao = question_info["questao"] or row["questao"]
    intencao = question_info.get("intencao", "")
    tipo_dado = question_info.get("tipo_dado", "")
    parametros = question_info.get("parametros", {})
    tipo = row["tipo"]

    run = pair_name.split("/")[-1] if "/" in pair_name else "default"
    sql_gt = load_sql_file(run, question_id, is_ground_truth=True)
    sql_model = load_sql_file(pair_name, question_id, is_ground_truth=False)

    sql_gt_formatted = format_sql(sql_gt) if sql_gt else "SQL não encontrado"
    sql_model_formatted = format_sql(sql_model) if sql_model else "SQL não encontrado"

    sql_gt_html = format_expandable_html(sql_gt_formatted, f"sql-gt-{question_id}") if sql_gt else '<pre class="sql-code">SQL não encontrado</pre>'
    sql_model_html = format_expandable_html(sql_model_formatted, f"sql-model-{question_id}") if sql_model else '<pre class="sql-code">SQL não encontrado</pre>'

    params_html = ""
    if parametros:
        param_rows = []
        for key, value in parametros.items():
            param_rows.append(f"<li><code>{key}</code>: <strong>{value}</strong></li>")
        params_html = f"""
        <div class="params-box">
            <strong>⚙️ Parâmetros:</strong>
            <ul>{''.join(param_rows)}</ul>
        </div>
        """

    precision = row.get("precision", None)
    recall = row.get("recall", None)
    accuracy = row.get("accuracy", None)
    f1_val = row.get("f1", None)
    match_val = row.get("match", None)

    metrics_items = [
        f"<li><strong>Tipo:</strong> {tipo}</li>",
        f"<li><strong>Status GT:</strong> {row['status_gt']}</li>",
        f"<li><strong>Status Modelo:</strong> {row['status_modelo']}</li>",
        f"<li><strong>Linhas Esperadas:</strong> {row['linhas_esperadas']}</li>",
        f"<li><strong>Linhas Retornadas:</strong> {row['linhas_retornadas']}</li>",
    ]

    if pd.notna(precision):
        metrics_items.append(f"<li><strong>Precisão:</strong> {precision:.2%}</li>")
    if pd.notna(recall):
        metrics_items.append(f"<li><strong>Recall:</strong> {recall:.2%}</li>")
    if pd.notna(accuracy):
        metrics_items.append(f"<li><strong>Accuracy:</strong> {accuracy:.2%}</li>")
    if pd.notna(f1_val):
        metrics_items.append(f"<li><strong>F1:</strong> {f1_val:.2%}</li>")
    if tipo == "quantidade" and pd.notna(match_val):
        match_text = "✅ Acertou" if match_val else "❌ Errou"
        metrics_items.append(f"<li><strong>Match:</strong> {match_text}</li>")

    gt_preview = load_pair_result_preview(run, question_id, is_ground_truth=True)
    model_preview = load_pair_result_preview(pair_name, question_id, is_ground_truth=False)

    if gt_preview is not None:
        gt_preview_html = dataframe_to_html(gt_preview)
    else:
        gt_error = load_error_file(run, question_id, is_ground_truth=True)
        if gt_error:
            gt_preview_html = format_error_html(gt_error, f"gt-{question_id}")
        else:
            gt_preview_html = "<p>Preview não disponível</p>"

    if model_preview is not None:
        model_preview_html = dataframe_to_html(model_preview)
    else:
        model_error = load_error_file(pair_name, question_id, is_ground_truth=False)
        if model_error:
            model_preview_html = format_error_html(model_error, f"model-{question_id}")
        else:
            model_preview_html = "<p>Preview não disponível</p>"

    return f"""
    <div class="question-detail" id="q{question_id}">
        <h3>Pergunta {question_id}: {questao}</h3>
        
        {f'<p class="intencao"><strong>🎯 Intenção:</strong> {intencao}</p>' if intencao else ''}
        {f'<p class="tipo-dado"><strong>📊 Dados necessários:</strong> {tipo_dado}</p>' if tipo_dado else ''}
        {params_html}
        
        <div class="metrics-box">
            <h4>📈 Métricas</h4>
            <ul class="metrics-list">
                {''.join(metrics_items)}
            </ul>
        </div>
        
        <div class="sql-comparison">
            <div class="sql-box">
                <h4>🎯 SQL Ground Truth</h4>
                {sql_gt_html}
            </div>
            <div class="sql-box">
                <h4>🤖 SQL Modelo</h4>
                {sql_model_html}
            </div>
        </div>
        
        <div class="preview-comparison">
            <div class="preview-box">
                <h4>👁️ Preview Ground Truth (10 primeiras linhas)</h4>
                {gt_preview_html}
            </div>
            <div class="preview-box">
                <h4>👁️ Preview Modelo (10 primeiras linhas)</h4>
                {model_preview_html}
            </div>
        </div>
    </div>
    """


MAX_ERROR_LENGTH = 500
MAX_SQL_LENGTH = 1000


def format_expandable_html(content: str, content_id: str, css_class: str = "sql-code") -> str:
    """
    Formata conteúdo para HTML com botão de expandir se for grande.

    Args:
        content: Texto do conteúdo.
        content_id: ID único para o elemento.
        css_class: Classe CSS para o pre.

    Returns:
        HTML formatado.
    """
    max_len = MAX_ERROR_LENGTH if "error" in css_class else MAX_SQL_LENGTH

    escaped = (
        content.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )

    if len(content) <= max_len:
        return f'<pre class="{css_class}">{escaped}</pre>'

    truncated = escaped[:max_len]
    btn_class = "expand-btn-error" if "error" in css_class else "expand-btn-sql"
    return f'''<pre class="{css_class}" id="{content_id}-short">{truncated}...</pre>
        <pre class="{css_class}" id="{content_id}-full" style="display:none;">{escaped}</pre>
        <button class="expand-btn {btn_class}" onclick="toggleExpand('{content_id}')">Ver mais</button>'''


def format_error_html(error: str, error_id: str) -> str:
    """
    Formata erro para HTML com botão de expandir se for grande.

    Args:
        error: Texto do erro.
        error_id: ID único para o elemento.

    Returns:
        HTML formatado do erro.
    """
    escaped_error = (
        error.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )

    if len(error) <= MAX_ERROR_LENGTH:
        return f'<div class="error-box"><pre>{escaped_error}</pre></div>'

    truncated = escaped_error[:MAX_ERROR_LENGTH]
    return f'''<div class="error-box">
        <pre id="{error_id}-short">{truncated}...</pre>
        <pre id="{error_id}-full" style="display:none;">{escaped_error}</pre>
        <button class="expand-btn" onclick="toggleError('{error_id}')">Ver mais</button>
    </div>'''


def load_error_file(pair_name: str, question_id: int, is_ground_truth: bool = False) -> str | None:
    """
    Carrega o arquivo de erro de uma pergunta.

    Args:
        pair_name: Nome do par no formato "modelo/run" ou "run" para GT.
        question_id: ID da pergunta.
        is_ground_truth: Se True, carrega do ground_truth.

    Returns:
        Conteúdo do erro ou None se não existir.
    """
    if is_ground_truth:
        run = pair_name.split("/")[-1] if "/" in pair_name else pair_name
        path = RESULTS_DIR / "ground_truth" / run / str(question_id) / "erro.txt"
    else:
        path = RESULTS_DIR / pair_name / str(question_id) / "erro.txt"

    if path.exists():
        try:
            return path.read_text(encoding="utf-8")
        except Exception:
            return None
    return None


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


def generate_all_details_html(pair_name: str, metrics: pd.DataFrame) -> str:
    """
    Gera HTML de detalhes para todas as perguntas.

    Args:
        pair_name (str): Nome do par de comparação.
        metrics (pd.DataFrame): DataFrame com as métricas.

    Returns:
        String HTML com todos os detalhes.
    """
    details = []
    for question_id in sorted(metrics["id"].unique()):
        detail_html = generate_question_detail_html(int(question_id), pair_name, metrics)
        if detail_html:
            details.append(detail_html)

    return f"""
    <section class="page-section" id="detalhes">
        <h2>🔍 Detalhes por Pergunta</h2>
        {''.join(details)}
    </section>
    """


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
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
        
        :root {{
            --color-precision: #1E40AF;
            --color-recall: #047857;
            --color-f1: #0E7490;
            --color-success-rate: #B45309;
            --color-background: #F8FAFC;
            --color-card-bg: #FFFFFF;
            --color-text: #1E293B;
            --color-text-muted: #64748B;
            --color-border: #E2E8F0;
            --color-success: #059669;
            --color-error: #DC2626;
            --color-warning: #D97706;
        }}
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'DM Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background-color: var(--color-background);
            color: var(--color-text);
            line-height: 1.6;
            padding: 2rem;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        
        header {{
            background: linear-gradient(135deg, var(--color-precision) 0%, #3B82F6 100%);
            color: white;
            padding: 2rem;
            border-radius: 16px;
            margin-bottom: 2rem;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }}
        
        header h1 {{
            font-size: 2rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
        }}
        
        header p {{
            opacity: 0.9;
            font-size: 0.95rem;
        }}
        
        nav.toc {{
            background: var(--color-card-bg);
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 2rem;
            border: 1px solid var(--color-border);
        }}
        
        nav.toc h3 {{
            margin-bottom: 1rem;
            font-size: 1rem;
        }}
        
        nav.toc ul {{
            list-style: none;
            display: flex;
            flex-wrap: wrap;
            gap: 1rem;
        }}
        
        nav.toc a {{
            color: var(--color-precision);
            text-decoration: none;
            padding: 0.5rem 1rem;
            background: var(--color-background);
            border-radius: 8px;
            transition: all 0.2s;
        }}
        
        nav.toc a:hover {{
            background: var(--color-precision);
            color: white;
        }}
        
        .summary-section {{
            background: var(--color-card-bg);
            border-radius: 16px;
            padding: 2rem;
            margin-bottom: 2rem;
            border: 1px solid var(--color-border);
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
        }}
        
        .summary-section h2 {{
            font-size: 1.25rem;
            font-weight: 600;
            margin-bottom: 1rem;
            color: var(--color-text);
        }}
        
        .summary-section p {{
            margin-bottom: 0.5rem;
            color: var(--color-text-muted);
        }}
        
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1.5rem;
            margin-top: 1.5rem;
        }}
        
        .metric-card {{
            padding: 1.5rem;
            border-radius: 12px;
            color: white;
        }}
        
        .metric-card.precision {{ background: var(--color-precision); }}
        .metric-card.recall {{ background: var(--color-recall); }}
        .metric-card.f1 {{ background: var(--color-f1); }}
        .metric-card.success-rate {{ background: var(--color-success-rate); }}
        
        .metric-title {{
            font-size: 0.875rem;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            opacity: 0.9;
            margin-bottom: 0.5rem;
        }}
        
        .metric-value {{
            font-size: 2rem;
            font-weight: 700;
            letter-spacing: -0.02em;
        }}
        
        .charts-grid {{
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 2rem;
            margin-bottom: 2rem;
        }}
        
        @media (max-width: 900px) {{
            .charts-grid {{ grid-template-columns: 1fr; }}
        }}
        
        /* Bar Chart Styles */
        .bar-chart {{
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
            padding: 1rem 0;
        }}
        
        .bar-row {{
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }}
        
        .bar-label {{
            width: 40px;
            font-size: 0.8rem;
            font-weight: 500;
            color: var(--color-text-muted);
            text-align: right;
        }}
        
        .bar-container {{
            flex: 1;
            height: 24px;
            background: var(--color-background);
            border-radius: 4px;
            position: relative;
            overflow: hidden;
        }}
        
        .bar-fill {{
            height: 100%;
            background: var(--color-precision);
            border-radius: 4px;
            transition: width 0.3s ease;
            min-width: 2px;
        }}
        
        .bar-value {{
            position: absolute;
            right: 8px;
            top: 50%;
            transform: translateY(-50%);
            font-size: 0.75rem;
            font-weight: 600;
            color: var(--color-text);
        }}
        
        /* Status Chart Styles */
        .status-chart {{
            padding: 1rem;
        }}
        
        .status-bar {{
            display: flex;
            height: 40px;
            border-radius: 8px;
            overflow: hidden;
            margin-bottom: 1rem;
        }}
        
        .status-fill {{
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: 600;
            font-size: 0.9rem;
            transition: width 0.3s ease;
        }}
        
        .status-fill.success {{
            background: var(--color-success);
        }}
        
        .status-fill.error {{
            background: var(--color-error);
        }}
        
        .status-legend {{
            display: flex;
            gap: 2rem;
            justify-content: center;
        }}
        
        .status-item {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 0.9rem;
        }}
        
        .status-dot {{
            width: 12px;
            height: 12px;
            border-radius: 50%;
        }}
        
        .status-dot.success {{
            background: var(--color-success);
        }}
        
        .status-dot.error {{
            background: var(--color-error);
        }}
        
        .card {{
            background: var(--color-card-bg);
            border-radius: 16px;
            border: 1px solid var(--color-border);
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
            margin-bottom: 2rem;
            overflow: hidden;
        }}
        
        .card-header {{
            background: var(--color-background);
            padding: 1rem 1.5rem;
            font-weight: 600;
            border-bottom: 1px solid var(--color-border);
        }}
        
        .card-body {{
            padding: 1.5rem;
        }}
        
        .page-section {{
            background: var(--color-card-bg);
            border-radius: 16px;
            padding: 2rem;
            border: 1px solid var(--color-border);
            margin-bottom: 2rem;
            page-break-inside: avoid;
        }}
        
        .page-section h2 {{
            font-size: 1.5rem;
            font-weight: 600;
            margin-bottom: 1.5rem;
            padding-bottom: 1rem;
            border-bottom: 2px solid var(--color-border);
        }}
        
        .table-container {{
            overflow-x: auto;
        }}
        
        .data-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.875rem;
        }}
        
        .data-table th {{
            background: var(--color-background);
            color: var(--color-text);
            font-weight: 600;
            text-transform: uppercase;
            font-size: 0.75rem;
            letter-spacing: 0.05em;
            padding: 0.875rem 0.75rem;
            text-align: left;
            border-bottom: 2px solid var(--color-border);
            white-space: nowrap;
        }}
        
        .data-table td {{
            padding: 0.75rem;
            border-bottom: 1px solid var(--color-border);
            color: var(--color-text);
        }}
        
        .data-table tr:nth-child(odd) {{
            background: rgba(248, 250, 252, 0.5);
        }}
        
        .data-table tr:hover {{
            background: rgba(30, 64, 175, 0.04);
        }}
        
        .center {{ text-align: center; }}
        .success {{ color: var(--color-success); font-weight: 600; }}
        .error {{ color: var(--color-error); font-weight: 600; }}
        .warning {{ color: var(--color-warning); font-weight: 600; }}

        .error-box {{
            background: #FEF2F2;
            border: 1px solid #FECACA;
            border-radius: 8px;
            padding: 1rem;
            color: #991B1B;
        }}

        .error-box pre {{
            margin: 0;
            white-space: pre-wrap;
            word-wrap: break-word;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.85rem;
        }}

        .expand-btn {{
            margin-top: 0.5rem;
            padding: 0.25rem 0.75rem;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 0.8rem;
        }}

        .expand-btn-error {{
            background: #DC2626;
        }}

        .expand-btn-error:hover {{
            background: #B91C1C;
        }}

        .expand-btn-sql {{
            background: var(--color-precision);
        }}

        .expand-btn-sql:hover {{
            background: #1E3A8A;
        }}
        
        .question-detail {{
            background: var(--color-background);
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 2rem;
            border: 1px solid var(--color-border);
            page-break-inside: avoid;
        }}
        
        .question-detail h3 {{
            font-size: 1.1rem;
            color: var(--color-precision);
            margin-bottom: 1rem;
            padding-bottom: 0.75rem;
            border-bottom: 1px solid var(--color-border);
        }}
        
        .question-detail .intencao,
        .question-detail .tipo-dado {{
            color: var(--color-text-muted);
            margin-bottom: 0.5rem;
            font-size: 0.9rem;
        }}
        
        .params-box {{
            background: var(--color-card-bg);
            padding: 1rem;
            border-radius: 8px;
            margin: 1rem 0;
            border: 1px solid var(--color-border);
        }}
        
        .params-box ul {{
            list-style: none;
            margin-top: 0.5rem;
        }}
        
        .params-box li {{
            margin: 0.25rem 0;
        }}
        
        .params-box code {{
            background: var(--color-background);
            padding: 2px 6px;
            border-radius: 4px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.85em;
        }}
        
        .metrics-box {{
            background: var(--color-card-bg);
            padding: 1rem;
            border-radius: 8px;
            margin: 1rem 0;
            border: 1px solid var(--color-border);
        }}
        
        .metrics-box h4 {{
            margin-bottom: 0.75rem;
            font-size: 0.95rem;
        }}
        
        .metrics-list {{
            list-style: none;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 0.5rem;
        }}
        
        .metrics-list li {{
            font-size: 0.9rem;
        }}
        
        .sql-comparison {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1rem;
            margin: 1rem 0;
        }}
        
        @media (max-width: 900px) {{
            .sql-comparison {{ grid-template-columns: 1fr; }}
        }}
        
        .sql-box {{
            background: var(--color-card-bg);
            border-radius: 8px;
            border: 1px solid var(--color-border);
            overflow: hidden;
        }}
        
        .sql-box h4 {{
            background: var(--color-background);
            padding: 0.75rem 1rem;
            font-size: 0.9rem;
            border-bottom: 1px solid var(--color-border);
        }}
        
        .sql-code {{
            font-family: 'JetBrains Mono', monospace;
            font-size: 12px;
            line-height: 1.5;
            padding: 1rem;
            margin: 0;
            overflow-x: auto;
            white-space: pre-wrap;
            word-wrap: break-word;
            background: var(--color-card-bg);
        }}
        
        .preview-comparison {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1rem;
            margin-top: 1rem;
        }}
        
        @media (max-width: 900px) {{
            .preview-comparison {{ grid-template-columns: 1fr; }}
        }}
        
        .preview-box {{
            background: var(--color-card-bg);
            border-radius: 8px;
            border: 1px solid var(--color-border);
            overflow: hidden;
        }}
        
        .preview-box h4 {{
            background: var(--color-background);
            padding: 0.75rem 1rem;
            font-size: 0.85rem;
            border-bottom: 1px solid var(--color-border);
        }}
        
        .preview-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.8rem;
        }}
        
        .preview-table th {{
            background: var(--color-background);
            padding: 0.5rem;
            text-align: left;
            font-weight: 600;
            font-size: 0.75rem;
            border-bottom: 1px solid var(--color-border);
        }}
        
        .preview-table td {{
            padding: 0.5rem;
            border-bottom: 1px solid var(--color-border);
            max-width: 200px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }}
        
        footer {{
            text-align: center;
            color: var(--color-text-muted);
            font-size: 0.875rem;
            padding: 2rem 0;
            border-top: 1px solid var(--color-border);
            margin-top: 2rem;
        }}
        
        @media print {{
            body {{ padding: 0; }}
            .page-section, .question-detail {{ break-inside: avoid; }}
            nav.toc {{ display: none; }}
        }}
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
    <script>
        function toggleExpand(id) {{
            const shortEl = document.getElementById(id + '-short');
            const fullEl = document.getElementById(id + '-full');
            const btn = event.target;
            if (fullEl.style.display === 'none') {{
                shortEl.style.display = 'none';
                fullEl.style.display = 'block';
                btn.textContent = 'Ver menos';
            }} else {{
                shortEl.style.display = 'block';
                fullEl.style.display = 'none';
                btn.textContent = 'Ver mais';
            }}
        }}
        function toggleError(id) {{ toggleExpand(id); }}
    </script>
</body>
</html>
    """

    return html
