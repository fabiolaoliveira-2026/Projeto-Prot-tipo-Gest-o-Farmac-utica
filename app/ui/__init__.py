"""
Módulo de interface de usuário.

Contém componentes de UI, layouts e construção da interface principal
da aplicação Shiny.
"""

from app.ui.components import (
    create_dashboard_tab,
    create_details_tab,
    create_questions_tab,
    create_sidebar,
)
from app.ui.layouts import create_app_ui

__all__ = [
    "create_sidebar",
    "create_dashboard_tab",
    "create_questions_tab",
    "create_details_tab",
    "create_app_ui",
]

