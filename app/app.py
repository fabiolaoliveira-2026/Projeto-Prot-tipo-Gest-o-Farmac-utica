"""
Aplicação Shiny para comparação de resultados Text2SQL.

Esta aplicação permite visualizar e comparar os resultados de diferentes
modelos de IA na tarefa de Text2SQL, exibindo métricas de precision, recall,
accuracy e F1, além de permitir a visualização das queries SQL geradas.

Este arquivo serve como ponto de entrada alternativo da aplicação.
O ponto de entrada principal é app/main.py.
"""

from shiny import App

from app.server.handlers import create_server
from app.ui.layouts import create_app_ui


def create_app() -> App:
    """
    Cria a instância da aplicação Shiny.

    Returns:
        Instância configurada da aplicação Shiny.
    """
    return App(create_app_ui(), create_server)


app = create_app()
