"""
Layouts principais da aplicação.

Este módulo contém a função que monta o layout completo da interface,
combinando sidebar, tabs e estilos CSS.
"""

from shiny import ui

from app.config.theme import custom_css
from app.data.loaders import get_comparison_pairs
from app.ui.components import (
    create_dashboard_tab,
    create_details_tab,
    create_questions_tab,
    create_sidebar,
)


def create_app_ui() -> ui.TagChild:
    """
    Cria a interface principal da aplicação.

    Monta o layout completo combinando sidebar, tabs de navegação e estilos CSS.

    Returns:
        Interface completa da aplicação Shiny.
    """
    available_pairs = get_comparison_pairs()

    return ui.page_sidebar(
        create_sidebar(available_pairs),
        ui.navset_card_tab(
            create_dashboard_tab(),
            create_questions_tab(),
            create_details_tab()
        ),
        custom_css,
        title="Text2SQL Comparador",
        fillable=True
    )
