"""
Aplicação principal Shiny para comparação de resultados Text2SQL.

Este módulo contém a função de criação da aplicação Shiny e o ponto de entrada
principal para execução da aplicação.
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

