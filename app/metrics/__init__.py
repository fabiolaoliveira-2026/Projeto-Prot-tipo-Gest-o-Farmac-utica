"""
Módulo de cálculo de métricas.

Contém funções para calcular métricas de precision, recall, accuracy e F1
para comparação de resultados Text2SQL.
"""

from app.metrics.calculator import calculate_listing_metrics, compare_quantity
from app.metrics.comparator import compare_runs, get_execution_status

__all__ = [
    "calculate_listing_metrics",
    "compare_quantity",
    "compare_runs",
    "get_execution_status",
]
