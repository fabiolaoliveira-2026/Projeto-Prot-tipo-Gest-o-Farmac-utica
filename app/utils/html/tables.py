"""
Componentes de tabelas HTML para relatórios Text2SQL.

Este módulo contém funções para gerar tabelas HTML de resumo
e tabelas completas de perguntas.
"""

import pandas as pd


def generate_questions_summary_table_html(metrics: pd.DataFrame) -> str:
    """
    Gera tabela HTML de resumo por pergunta (versão compacta do Dashboard).

    Args:
        metrics (pd.DataFrame): DataFrame com as métricas.

    Returns:
        String HTML da tabela.
    """
    from app.data.loaders import get_question_with_params

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
    from app.data.loaders import get_question_with_params

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
    from app.data.loaders import get_question_with_params, load_pair_result_preview, load_sql_file
    from app.utils.html.components import dataframe_to_html
    from app.utils.sql_formatter import format_sql

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

    gt_preview_html = dataframe_to_html(gt_preview) if gt_preview is not None else "<p>Preview não disponível</p>"
    model_preview_html = dataframe_to_html(model_preview) if model_preview is not None else "<p>Preview não disponível</p>"

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
                <pre class="sql-code">{sql_gt_formatted}</pre>
            </div>
            <div class="sql-box">
                <h4>🤖 SQL Modelo</h4>
                <pre class="sql-code">{sql_model_formatted}</pre>
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
