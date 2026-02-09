"""
Script de comparação de resultados Text2SQL.

Este módulo compara os resultados de modelos de IA com o ground truth,
calculando métricas de precision, recall, accuracy e F1 para perguntas
de listagem, e validação exata para perguntas de quantidade.

Gera arquivos CSV com métricas por pergunta e resumo agregado para cada modelo.

Este arquivo serve como ponto de entrada para o CLI de comparação,
delegando a lógica para os módulos organizados em subpacotes.
"""

from app.cli.compare import main

if __name__ == "__main__":
    exit(main())
