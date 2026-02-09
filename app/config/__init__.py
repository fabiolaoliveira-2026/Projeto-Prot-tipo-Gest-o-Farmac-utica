"""
Módulo de configurações da aplicação.

Contém constantes de caminhos de diretórios e configurações de tema visual.
"""

from app.config.paths import DATA_DIR, QUESTIONS_FILE, QUESTIONS_SOURCE_FILE, RESULTS_DIR
from app.config.theme import COLORS, PLOTLY_COLORS, custom_css

__all__ = [
    "DATA_DIR",
    "RESULTS_DIR",
    "QUESTIONS_FILE",
    "QUESTIONS_SOURCE_FILE",
    "COLORS",
    "PLOTLY_COLORS",
    "custom_css",
]
