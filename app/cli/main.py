"""
CLI principal unificada para a aplicação Text2SQL.

Este módulo agrega todos os comandos da aplicação em uma única interface de linha de comando.
"""

import subprocess
import sys

import typer

from app.cli.compare.cli import app as compare_app
from app.cli.execute_sql.cli import app as execute_app
from app.cli.generate_queries.cli import app as generate_app
from app.cli.ground_truth.cli import app as ground_truth_app
from app.cli.rag_index.cli import app as rag_app

app = typer.Typer(
    name="text2sql",
    help="CLI unificada para Text2SQL: Geração, Execução, Comparação e RAG.",
    add_completion=False,
)

app.add_typer(generate_app, name="generate", help="Gera queries SQL a partir de perguntas.")
app.add_typer(execute_app, name="execute", help="Executa queries SQL em banco de dados.")
app.add_typer(ground_truth_app, name="ground-truth", help="Gera ground truth parametrizado.")
app.add_typer(compare_app, name="compare", help="Compara resultados com ground truth.")
app.add_typer(rag_app, name="rag", help="Gerencia índice RAG.")


@app.command()
def ui(
    port: int = typer.Option(8000, help="Porta para rodar a aplicação Shiny."),
    host: str = typer.Option("127.0.0.1", help="Host para rodar a aplicação Shiny."),
    reload: bool = typer.Option(False, "--reload", help="Habilita recarregamento automático."),
) -> None:
    """
    Inicia a interface gráfica (Shiny).
    """
    cmd = ["shiny", "run", "app.main:app", "--host", host, "--port", str(port)]
    if reload:
        cmd.append("--reload")

    typer.echo(f"Iniciando UI em http://{host}:{port}")
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        typer.echo(f"Erro ao rodar UI: {e}", err=True)
        raise typer.Exit(1)
    except KeyboardInterrupt:
        typer.echo("\nEncerrando UI...")
        pass


def main():
    """Função principal de entrada do CLI."""
    app()


if __name__ == "__main__":
    main()

