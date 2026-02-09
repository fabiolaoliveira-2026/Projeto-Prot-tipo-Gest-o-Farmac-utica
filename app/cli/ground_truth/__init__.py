"""
Submódulo CLI para geração de ground truth com parâmetros.

Fornece uma interface de linha de comando para gerar variações do ground truth
substituindo placeholders X1, Y1, etc. por valores configurados em YAML.
"""

from .cli import main

__all__ = ["main"]

