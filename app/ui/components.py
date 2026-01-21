"""
Componentes de UI reutilizáveis.

Este módulo contém funções que criam componentes individuais da interface,
como sidebar, tabs e cards para a aplicação Shiny.
"""

from shiny import ui
from shinywidgets import output_widget


def create_sidebar(available_pairs: list[dict]) -> ui.TagChild:
    """
    Cria o componente sidebar da aplicação.

    Args:
        available_pairs: Lista de pares de comparação disponíveis.

    Returns:
        Componente sidebar do Shiny.
    """
    pair_choices = [p["pair_name"] for p in available_pairs] if available_pairs else ["Nenhum par disponível"]

    return ui.sidebar(
        ui.h4("⚙️ Configurações"),
        ui.input_select(
            "comparison_pair",
            "Selecione o Par:",
            choices=pair_choices,
            selected=pair_choices[0] if pair_choices else None
        ),
        ui.hr(),
        ui.p("Compare resultados de modelos Text2SQL com o ground truth."),
        ui.hr(),
        ui.output_ui("sidebar_summary"),
        ui.hr(),
        ui.h5("📤 Exportar"),
        ui.download_button(
            "export_html",
            "Exportar HTML",
            class_="btn btn-primary w-100"
        ),
        width=280
    )


def create_dashboard_tab() -> ui.TagChild:
    """
    Cria a tab do Dashboard com métricas principais.

    Returns:
        Componente nav_panel do dashboard.
    """
    return ui.nav_panel(
        "📊 Dashboard",
        ui.div(
            ui.layout_columns(
                ui.div(
                    ui.value_box(
                        "Precisão Média",
                        ui.output_text("precision_value"),
                        theme=None
                    ),
                    class_="value-box-precision"
                ),
                ui.div(
                    ui.value_box(
                        "Recall Médio",
                        ui.output_text("recall_value"),
                        theme=None
                    ),
                    class_="value-box-recall"
                ),
                ui.div(
                    ui.value_box(
                        "F1 Médio",
                        ui.output_text("f1_value"),
                        theme=None
                    ),
                    class_="value-box-f1"
                ),
                ui.div(
                    ui.value_box(
                        "Taxa de Sucesso",
                        ui.output_text("success_rate_value"),
                        theme=None
                    ),
                    class_="value-box-success-rate"
                ),
                col_widths=[3, 3, 3, 3],
                class_="mb-4"
            ),
            ui.layout_columns(
                ui.card(
                    ui.card_header("Métricas Médias por Pergunta"),
                    ui.card_body(output_widget("comparison_chart"))
                ),
                ui.card(
                    ui.card_header("Taxa de Execução"),
                    ui.card_body(output_widget("status_chart"))
                ),
                col_widths=[8, 4],
                class_="mb-3"
            ),
            ui.card(
                ui.card_header("📋 Resumo por Pergunta"),
                ui.card_body(ui.output_ui("questions_summary_table"))
            ),
            class_="p-3"
        )
    )


def create_questions_tab() -> ui.TagChild:
    """
    Cria a tab de Perguntas com filtros e tabela.

    Returns:
        Componente nav_panel das perguntas.
    """
    return ui.nav_panel(
        "📋 Perguntas",
        ui.div(
            ui.layout_columns(
                ui.input_select(
                    "filter_tipo",
                    "Filtrar por Tipo:",
                    choices=["Todos", "listagem", "quantidade"],
                    selected="Todos"
                ),
                ui.input_select(
                    "filter_status",
                    "Filtrar por Status:",
                    choices=["Todos", "sucesso", "erro"],
                    selected="Todos"
                ),
                col_widths=[6, 6],
                class_="mb-4"
            ),
            ui.output_data_frame("questions_table"),
            class_="p-3"
        )
    )


def create_details_tab() -> ui.TagChild:
    """
    Cria a tab de Detalhes com SQL e métricas.

    Returns:
        Componente nav_panel dos detalhes.
    """
    return ui.nav_panel(
        "🔍 Detalhes",
        ui.div(
            ui.div(
                ui.input_select(
                    "pergunta_id",
                    "Selecione a Pergunta:",
                    choices=list(range(1, 21)),
                    selected=1
                ),
                class_="mb-3"
            ),
            ui.output_ui("question_title"),
            ui.layout_columns(
                ui.card(
                    ui.card_header("🎯 SQL Ground Truth"),
                    ui.card_body(ui.output_ui("sql_gt"))
                ),
                ui.card(
                    ui.card_header("🤖 SQL Modelo"),
                    ui.card_body(ui.output_ui("sql_model"))
                ),
                col_widths=[6, 6],
                class_="mb-4"
            ),
            ui.card(
                ui.card_header("📈 Métricas da Pergunta"),
                ui.card_body(ui.output_ui("question_metrics")),
                class_="mb-4"
            ),
            ui.layout_columns(
                ui.card(
                    ui.card_header("👁️ Preview Ground Truth (10 primeiras linhas)"),
                    ui.card_body(ui.output_data_frame("preview_gt"))
                ),
                ui.card(
                    ui.card_header("👁️ Preview Modelo (10 primeiras linhas)"),
                    ui.card_body(ui.output_data_frame("preview_model"))
                ),
                col_widths=[6, 6]
            ),
            class_="p-3"
        )
    )


