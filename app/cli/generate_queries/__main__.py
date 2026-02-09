"""
Ponto de entrada para execução do módulo como script.

Permite executar o módulo diretamente com:
    python -m app.cli.generate_queries
"""

import sys

from .cli import main

if __name__ == "__main__":
    sys.exit(main())

