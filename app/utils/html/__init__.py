"""
Módulo de exportação de relatórios HTML para Text2SQL.

Este pacote contém funcionalidades para gerar relatórios HTML auto-contidos
com dashboards, tabelas e detalhes de comparação de queries SQL.
"""

from .report import generate_full_html_report

__all__ = ["generate_full_html_report"]

