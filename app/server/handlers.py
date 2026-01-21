"""
Handlers do servidor Shiny.

Este módulo contém todas as funções reativas e de renderização que compõem
a lógica do servidor da aplicação Shiny.
"""

import pandas as pd
import plotly.express as px
from shiny import reactive, render, ui
from shinywidgets import render_widget

from app.config.paths import QUESTIONS_FILE, RESULTS_DIR
from app.config.theme import COLORS, PLOTLY_COLORS
from app.data.loaders import (
    get_comparison_pairs,
    get_question_with_params,
    get_summary_value,
    load_pair_metrics,
    load_pair_result_preview,
    load_pair_sql,
    load_pair_summary,
    load_sql_file,
)
from app.utils.html_exporter import generate_full_html_report
from app.utils.sql_formatter import format_sql


def create_server(input, output, session):
    """
    Cria o servidor da aplicação Shiny.

    Define todas as funções reativas e renderizações necessárias
    para a interatividade da aplicação.

    Args:
        input: Objeto de inputs do Shiny.
        output: Objeto de outputs do Shiny.
        session: Sessão do Shiny.
    """
    available_pairs = get_comparison_pairs()

    @reactive.calc
    def current_pair() -> str | None:
        """Retorna o par de comparação selecionado."""
        pair = input.comparison_pair()
        if not pair or pair == "Nenhum par disponível":
            return None
        return pair

    @reactive.calc
    def current_metrics():
        """Carrega métricas do par selecionado."""
        pair = current_pair()
        if not pair:
            return None
        return load_pair_metrics(pair)

    @reactive.calc
    def current_summary():
        """Carrega resumo do par selecionado."""
        pair = current_pair()
        if not pair:
            return None
        return load_pair_summary(pair)

    @reactive.calc
    def all_pair_metrics():
        """Carrega métricas de todos os pares para o gráfico comparativo."""
        all_metrics = {}
        for pair_info in available_pairs:
            metrics = load_pair_metrics(pair_info["pair_name"])
            if metrics is not None:
                all_metrics[pair_info["pair_name"]] = metrics
        return all_metrics

    @render.text
    def precision_value():
        summary = current_summary()
        val = get_summary_value(summary, "precision_media")
        return f"{val:.2%}" if val is not None else "N/A"

    @render.text
    def recall_value():
        summary = current_summary()
        val = get_summary_value(summary, "recall_media")
        return f"{val:.2%}" if val is not None else "N/A"

    @render.text
    def f1_value():
        summary = current_summary()
        val = get_summary_value(summary, "f1_media")
        return f"{val:.2%}" if val is not None else "N/A"

    @render.text
    def success_rate_value():
        summary = current_summary()
        val = get_summary_value(summary, "taxa_execucao_sucesso")
        return f"{val:.1%}" if val is not None else "N/A"

    @render.ui
    def sidebar_summary():
        summary = current_summary()
        pair = current_pair()

        if summary is None:
            return ui.p("Selecione um par para ver o resumo.")

        listagem_total = get_summary_value(summary, "listagem_total")
        listagem_comp = get_summary_value(summary, "listagem_comparadas")
        qtd_total = get_summary_value(summary, "quantidade_total")
        qtd_acertos = get_summary_value(summary, "quantidade_acertos")

        if pair:
            model, run = pair.split("/", 1) if "/" in pair else (pair, "default")
            gt_run = run
        else:
            model, run, gt_run = "N/A", "N/A", "N/A"

        return ui.div(
            ui.h5("📊 Resumo"),
            ui.p(f"Modelo: {model}", style="font-weight: 500;"),
            ui.p(f"Run: {run}"),
            ui.p(f"GT Run: {gt_run}"),
            ui.hr(),
            ui.p(f"Listagens: {int(listagem_comp or 0)}/{int(listagem_total or 0)} comparadas"),
            ui.p(f"Quantidade: {int(qtd_acertos or 0)}/{int(qtd_total or 0)} acertos")
        )

    @render_widget
    def comparison_chart():
        """Gráfico de barras com métricas médias por pergunta para cada par."""
        all_metrics = all_pair_metrics()
        if not all_metrics:
            return None

        data = []

        for pair_name, metrics in all_metrics.items():
            for _, row in metrics.iterrows():
                question_id = row["id"]
                f1 = row.get("f1", None)
                precision = row.get("precision", None)
                recall = row.get("recall", None)

                if pd.notna(f1):
                    data.append({
                        "Par": pair_name,
                        "Pergunta": f"Q{question_id}",
                        "Métrica": "F1",
                        "Valor": f1
                    })

                if pd.notna(precision):
                    data.append({
                        "Par": pair_name,
                        "Pergunta": f"Q{question_id}",
                        "Métrica": "Precisão",
                        "Valor": precision
                    })

                if pd.notna(recall):
                    data.append({
                        "Par": pair_name,
                        "Pergunta": f"Q{question_id}",
                        "Métrica": "Recall",
                        "Valor": recall
                    })

        if not data:
            return None

        df = pd.DataFrame(data)

        df_f1 = df[df["Métrica"] == "F1"]

        if df_f1.empty:
            return None

        fig = px.bar(
            df_f1,
            x="Pergunta",
            y="Valor",
            color="Par",
            barmode="group",
            title="",
            labels={"Valor": "F1 Score", "Pergunta": ""},
            color_discrete_sequence=PLOTLY_COLORS,
            template="simple_white",
            text_auto=".0%"
        )

        fig.update_traces(
            textposition="outside",
            textfont=dict(family="DM Sans", size=9)
        )

        fig.update_layout(
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
                font=dict(family="DM Sans", size=11),
                title=""
            ),
            margin=dict(l=20, r=20, t=50, b=20),
            height=380,
            font=dict(family="DM Sans"),
            yaxis=dict(range=[0, 1.15]),
            xaxis=dict(tickangle=-45)
        )

        return fig

    @render_widget
    def status_chart():
        metrics = current_metrics()
        if metrics is None:
            return None

        status_counts = metrics["status_modelo"].value_counts()

        fig = px.pie(
            values=status_counts.values,
            names=status_counts.index,
            title="",
            color_discrete_map={
                "sucesso": COLORS["success"],
                "erro": COLORS["error"]
            },
            template="simple_white"
        )
        fig.update_layout(
            margin=dict(l=20, r=20, t=20, b=20),
            height=300,
            font=dict(family="DM Sans"),
            legend=dict(font=dict(family="DM Sans", size=12))
        )
        fig.update_traces(
            textfont=dict(family="DM Sans", size=12),
            marker=dict(line=dict(color="#FFFFFF", width=2))
        )

        return fig

    @render.ui
    def questions_summary_table():
        metrics = current_metrics()
        if metrics is None:
            return ui.p("Nenhum dado disponível.")

        rows = []
        for _, row in metrics.iterrows():
            question_id = int(row["id"])
            question_info = get_question_with_params(question_id)
            questao = question_info["questao"] or row["questao"]
            tipo = row["tipo"]
            status_modelo = row["status_modelo"]

            if status_modelo == "erro":
                resultado = "❌"
                resultado_texto = "Erro"
            elif tipo == "listagem":
                f1 = row.get("f1", 0)
                if pd.notna(f1) and f1 >= 0.8:
                    resultado = "✅"
                    resultado_texto = "Correto"
                elif pd.notna(f1) and f1 >= 0.5:
                    resultado = "⚠️"
                    resultado_texto = "Parcial"
                else:
                    resultado = "❌"
                    resultado_texto = "Incorreto"
            elif tipo == "quantidade":
                match_val = row.get("match", False)
                if match_val is True or str(match_val).lower() == "true":
                    resultado = "✅"
                    resultado_texto = "Correto"
                else:
                    resultado = "❌"
                    resultado_texto = "Incorreto"
            else:
                resultado = "❓"
                resultado_texto = "Desconhecido"

            rows.append({
                "id": question_id,
                "questao": questao,
                "tipo": tipo,
                "resultado": resultado,
                "resultado_texto": resultado_texto
            })

        table_rows = []
        for r in rows:
            table_rows.append(
                ui.tags.tr(
                    ui.tags.td(str(r["id"]), style="text-align: center; font-weight: 500;"),
                    ui.tags.td(r["questao"]),
                    ui.tags.td(r["tipo"], style="text-align: center;"),
                    ui.tags.td(
                        f"{r['resultado']} {r['resultado_texto']}",
                        style="text-align: center; font-weight: 600; white-space: nowrap;"
                    )
                )
            )

        return ui.div(
            ui.tags.table(
                ui.tags.thead(
                    ui.tags.tr(
                        ui.tags.th("ID", style="width: 60px; text-align: center;"),
                        ui.tags.th("Pergunta"),
                        ui.tags.th("Tipo", style="width: 110px; text-align: center;"),
                        ui.tags.th("Resultado", style="width: 130px; text-align: center;")
                    )
                ),
                ui.tags.tbody(*table_rows),
                class_="table table-striped table-hover"
            ),
            style="max-height: 400px; overflow-y: auto; border-radius: 8px; border: 1px solid var(--color-border);"
        )

    @render.data_frame
    def questions_table():
        metrics = current_metrics()
        if metrics is None:
            return pd.DataFrame()

        df = metrics.copy()

        df["questao"] = df.apply(
            lambda row: get_question_with_params(int(row["id"]))["questao"] or row["questao"],
            axis=1
        )

        if input.filter_tipo() != "Todos":
            df = df[df["tipo"] == input.filter_tipo()]

        if input.filter_status() != "Todos":
            df = df[df["status_modelo"] == input.filter_status()]

        display_cols = [
            "id", "questao", "tipo", "status_modelo",
            "linhas_esperadas", "linhas_retornadas", "coluna_usada",
            "precision", "recall", "accuracy", "f1", "match"
        ]

        existing_cols = [col for col in display_cols if col in df.columns]

        return render.DataGrid(
            df[existing_cols],
            selection_mode="row",
            height="500px"
        )

    @reactive.calc
    def get_sql_gt():
        """Obtém SQL do ground truth formatado."""
        pair = current_pair()
        if not pair:
            return None

        run = pair.split("/")[-1] if "/" in pair else "default"
        question_id = int(input.pergunta_id())

        sql_from_file = load_sql_file(run, question_id, is_ground_truth=True)
        if sql_from_file:
            return sql_from_file

        sql_df = load_pair_sql(run, is_ground_truth=True)

        if sql_df is None:
            return None

        if "id" in sql_df.columns:
            row = sql_df[sql_df["id"] == question_id]
        else:
            row = sql_df.iloc[question_id - 1:question_id] if question_id <= len(sql_df) else pd.DataFrame()

        if row.empty:
            return None

        sql_col = "SQL" if "SQL" in row.columns else row.columns[-1]
        return row.iloc[0][sql_col]

    @reactive.calc
    def get_sql_model():
        """Obtém SQL do modelo."""
        pair = current_pair()
        if not pair:
            return None

        question_id = int(input.pergunta_id())

        sql_from_file = load_sql_file(pair, question_id, is_ground_truth=False)
        if sql_from_file:
            return sql_from_file

        sql_df = load_pair_sql(pair, is_ground_truth=False)

        if sql_df is None:
            sql_path = RESULTS_DIR / pair / str(question_id) / f"{question_id}.sql"
            if sql_path.exists():
                return sql_path.read_text()
            return None

        if "id" in sql_df.columns:
            row = sql_df[sql_df["id"] == question_id]
        elif "Questões" in sql_df.columns:
            questions_df = pd.read_csv(QUESTIONS_FILE)
            question_text = questions_df[questions_df["id"] == question_id]["Questões"].values
            if len(question_text) > 0:
                row = sql_df[sql_df["Questões"] == question_text[0]]
            else:
                row = pd.DataFrame()
        else:
            row = sql_df.iloc[question_id - 1:question_id] if question_id <= len(sql_df) else pd.DataFrame()

        if row.empty:
            return None

        sql_col = "SQL" if "SQL" in row.columns else row.columns[-1]
        return row.iloc[0][sql_col]

    @render.ui
    def sql_gt():
        sql = get_sql_gt()
        if sql is None:
            return ui.div("Query não encontrada.", class_="sql-code")

        formatted = format_sql(sql)
        return ui.div(
            ui.tags.pre(formatted, class_="sql-code"),
            style="max-height: 350px; overflow-y: auto;"
        )

    @render.ui
    def sql_model():
        sql = get_sql_model()
        if sql is None:
            return ui.div("Query não encontrada.", class_="sql-code")

        formatted = format_sql(sql)
        return ui.div(
            ui.tags.pre(formatted, class_="sql-code"),
            style="max-height: 350px; overflow-y: auto;"
        )

    @render.ui
    def question_title():
        metrics = current_metrics()
        if metrics is None:
            return ui.div()

        question_id = int(input.pergunta_id())
        row = metrics[metrics["id"] == question_id]

        if row.empty:
            return ui.div()

        question_info = get_question_with_params(question_id)
        questao = question_info["questao"] or row.iloc[0]["questao"]
        intencao = question_info.get("intencao", "")
        tipo_dado = question_info.get("tipo_dado", "")
        parametros = question_info.get("parametros", {})

        elements = [
            ui.h4(f"📝 {questao}", class_="question-title-box")
        ]

        if intencao:
            elements.append(
                ui.p(
                    ui.tags.strong("🎯 Intenção: "),
                    intencao,
                    style="margin: 8px 0; color: #555;"
                )
            )

        if tipo_dado:
            elements.append(
                ui.p(
                    ui.tags.strong("📊 Dados necessários: "),
                    tipo_dado,
                    style="margin: 8px 0; color: #555;"
                )
            )

        if parametros:
            param_descriptions = {
                "X": "Item/Produto/Medicamento",
                "Y": "Período de tempo",
            }

            param_rows = []
            for key, value in parametros.items():
                base_key = key.rstrip("0123456789")
                desc = param_descriptions.get(base_key, "Parâmetro")
                index = key[len(base_key):] if len(key) > len(base_key) else ""
                label = f"{desc} {index}".strip() if index else desc

                param_rows.append(
                    ui.tags.tr(
                        ui.tags.td(
                            ui.tags.code(key),
                            style="padding: 4px 12px 4px 0; font-weight: bold; color: #0066cc;"
                        ),
                        ui.tags.td(
                            label,
                            style="padding: 4px 12px; color: #666;"
                        ),
                        ui.tags.td(
                            ui.tags.code(value, style="background: #f5f5f5; padding: 2px 6px; border-radius: 3px;"),
                            style="padding: 4px 0;"
                        ),
                    )
                )

            elements.append(
                ui.div(
                    ui.p(
                        ui.tags.strong("⚙️ Parâmetros utilizados:"),
                        style="margin: 12px 0 8px 0; color: #333;"
                    ),
                    ui.tags.table(
                        ui.tags.thead(
                            ui.tags.tr(
                                ui.tags.th("Código", style="text-align: left; padding: 4px 12px 4px 0; border-bottom: 1px solid #ddd;"),
                                ui.tags.th("Descrição", style="text-align: left; padding: 4px 12px; border-bottom: 1px solid #ddd;"),
                                ui.tags.th("Valor", style="text-align: left; padding: 4px 0; border-bottom: 1px solid #ddd;"),
                            )
                        ),
                        ui.tags.tbody(*param_rows),
                        style="border-collapse: collapse; margin-left: 20px; font-size: 0.9em;"
                    ),
                    style="margin-top: 8px; padding: 10px; background: #fafafa; border-radius: 6px; border: 1px solid #eee;"
                )
            )

        return ui.div(*elements)

    @render.ui
    def question_metrics():
        metrics = current_metrics()
        if metrics is None:
            return ui.p("Nenhuma métrica disponível.")

        question_id = int(input.pergunta_id())
        row = metrics[metrics["id"] == question_id]

        if row.empty:
            return ui.p("Pergunta não encontrada nas métricas.")

        row = row.iloc[0]
        tipo = row["tipo"]

        cards = [
            ui.div(
                ui.strong("Tipo: "), row["tipo"],
                ui.br(),
                ui.strong("Status GT: "), row["status_gt"],
                ui.br(),
                ui.strong("Status Modelo: "), row["status_modelo"],
                ui.br(),
                ui.strong("Linhas Esperadas: "), str(row["linhas_esperadas"]),
                ui.br(),
                ui.strong("Linhas Retornadas: "), str(row["linhas_retornadas"]),
                style="margin-right: 20px;"
            )
        ]

        if tipo == "listagem":
            cards.append(
                ui.div(
                    ui.strong("Coluna Usada: "), str(row["coluna_usada"]),
                    ui.br(),
                    ui.strong("Precisão: "), f"{row['precision']:.2%}" if pd.notna(row["precision"]) else "N/A",
                    ui.br(),
                    ui.strong("Recall: "), f"{row['recall']:.2%}" if pd.notna(row["recall"]) else "N/A",
                    ui.br(),
                    ui.strong("Accuracy: "), f"{row['accuracy']:.2%}" if pd.notna(row["accuracy"]) else "N/A",
                    ui.br(),
                    ui.strong("F1: "), f"{row['f1']:.2%}" if pd.notna(row["f1"]) else "N/A"
                )
            )
        elif tipo == "quantidade":
            match_val = row["match"]
            match_text = "✅ Acertou" if match_val else "❌ Errou" if pd.notna(match_val) else "N/A"
            cards.append(
                ui.div(
                    ui.strong("Coluna Usada: "), str(row["coluna_usada"]) if pd.notna(row["coluna_usada"]) else "N/A",
                    ui.br(),
                    ui.strong("Resultado: "), match_text,
                    ui.br(),
                    ui.strong("Precisão: "), f"{row['precision']:.2%}" if pd.notna(row["precision"]) else "N/A",
                    ui.br(),
                    ui.strong("Recall: "), f"{row['recall']:.2%}" if pd.notna(row["recall"]) else "N/A",
                    ui.br(),
                    ui.strong("Accuracy: "), f"{row['accuracy']:.2%}" if pd.notna(row["accuracy"]) else "N/A",
                    ui.br(),
                    ui.strong("F1: "), f"{row['f1']:.2%}" if pd.notna(row["f1"]) else "N/A"
                )
            )

        return ui.div(*cards, style="display: flex; gap: 40px;")

    @render.data_frame
    def preview_gt():
        pair = current_pair()
        if not pair:
            return pd.DataFrame({"Mensagem": ["Selecione um par"]})

        question_id = int(input.pergunta_id())
        run = pair.split("/")[-1] if "/" in pair else "default"

        df = load_pair_result_preview(run, question_id, is_ground_truth=True)
        if df is None:
            return pd.DataFrame({"Mensagem": ["Resultado não disponível"]})
        return render.DataGrid(df, height="250px")

    @render.data_frame
    def preview_model():
        pair = current_pair()
        if not pair:
            return pd.DataFrame({"Mensagem": ["Selecione um par"]})

        question_id = int(input.pergunta_id())

        df = load_pair_result_preview(pair, question_id, is_ground_truth=False)
        if df is None:
            return pd.DataFrame({"Mensagem": ["Resultado não disponível"]})
        return render.DataGrid(df, height="250px")

    @render.download(filename=lambda: f"relatorio_text2sql_{current_pair().replace('/', '_') if current_pair() else 'export'}.html")
    def export_html():
        """Gera e retorna o relatório HTML para download."""
        pair = current_pair()
        if not pair:
            yield "<html><body><h1>Erro: Nenhum par selecionado</h1></body></html>"
            return

        html_content = generate_full_html_report(pair)
        yield html_content

