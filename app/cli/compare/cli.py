"""
CLI de comparação de resultados Text2SQL.

Este módulo fornece uma interface de linha de comando para comparar
os resultados de modelos de IA com o ground truth, gerando arquivos
CSV com métricas e resumos. Trabalha com pares de runs.
Também permite exportar relatórios HTML sem necessidade de subir o servidor.
"""

import sys
from datetime import datetime
from pathlib import Path
from typing import Annotated, Optional

import pandas as pd
import typer

from app.cli.config_loader import get_config_value, load_yaml_config
from app.config.paths import COMPARE_CONFIG_FILE, QUESTIONS_FILE, RESULTS_DIR
from app.metrics.comparator import compare_runs
from app.utils.html_exporter import generate_full_html_report

app = typer.Typer(
    name="compare",
    help="Compara resultados de modelos Text2SQL com o ground truth.",
    add_completion=False,
)


def discover_comparison_pairs(results_dir: Path) -> list[dict]:
    """
    Descobre todos os pares de comparação disponíveis.

    Encontra todos os pares ground_truth/run e modelo/run disponíveis.

    Args:
        results_dir: Diretório base de resultados.

    Returns:
        Lista de dicionários com informações dos pares.
    """
    pairs = []
    gt_dir = results_dir / "ground_truth"

    if not gt_dir.exists():
        return pairs

    gt_runs = [d.name for d in gt_dir.iterdir() if d.is_dir() and (d / "resumo_execucao.csv").exists()]

    for model_dir in results_dir.iterdir():
        if not model_dir.is_dir() or model_dir.name == "ground_truth":
            continue

        model_name = model_dir.name

        for run_dir in model_dir.iterdir():
            if not run_dir.is_dir():
                continue

            run_name = run_dir.name

            if run_name in gt_runs:
                pairs.append({
                    "model": model_name,
                    "run": run_name,
                    "gt_path": gt_dir / run_name,
                    "model_path": run_dir,
                    "pair_name": f"{model_name}/{run_name}"
                })

    return pairs


@app.command()
def run(
    config: Annotated[
        Optional[Path],
        typer.Option("--config", "-c", help="Arquivo YAML de configuração.")
    ] = COMPARE_CONFIG_FILE,
    gt_run: Annotated[
        Optional[str],
        typer.Option("--gt", help="Run do ground truth (ex: default).")
    ] = None,
    model_run: Annotated[
        Optional[str],
        typer.Option("--model", "-m", help="Modelo e run (ex: Qwen3-32B-AWQ/default).")
    ] = None,
    questions_file: Annotated[
        Optional[Path],
        typer.Option("--questions", "-q", help="Caminho para o arquivo CSV de perguntas.")
    ] = None,
    results_dir: Annotated[
        Optional[Path],
        typer.Option("--results-dir", "-r", help="Diretório com os resultados.")
    ] = None,
) -> None:
    """
    Compara resultados de um modelo com o ground truth.

    Usa pares de runs: ground_truth/run vs modelo/run.

    Exemplos:
        text2sql-compare compare --gt default --model Qwen3-32B-AWQ/default
    """
    yaml_config: dict = {}
    if config and config.exists():
        try:
            yaml_config = load_yaml_config(config)
            typer.echo(f"Configuração carregada de: {config}")
        except Exception as e:
            typer.echo(f"Erro ao carregar configuração: {e}", err=True)
            raise typer.Exit(1)

    cfg_questions = get_config_value(questions_file, yaml_config, "paths.questions", QUESTIONS_FILE)
    cfg_results_dir = get_config_value(results_dir, yaml_config, "paths.results_dir", RESULTS_DIR)
    cfg_gt_run = get_config_value(gt_run, yaml_config, "comparison.gt_run", None)
    cfg_model_run = get_config_value(model_run, yaml_config, "comparison.model_run", None)

    if isinstance(cfg_questions, str):
        cfg_questions = Path(cfg_questions)
    if isinstance(cfg_results_dir, str):
        cfg_results_dir = Path(cfg_results_dir)

    if not cfg_questions.exists():
        typer.echo(f"Erro: Arquivo de perguntas não encontrado: {cfg_questions}", err=True)
        raise typer.Exit(1)

    questions_df = pd.read_csv(cfg_questions)

    if not cfg_gt_run or not cfg_model_run:
        typer.echo("Erro: Especifique --gt e --model para comparação.", err=True)
        typer.echo("Use 'text2sql-compare list-pairs' para ver pares disponíveis.", err=True)
        raise typer.Exit(1)

    if "/" in cfg_model_run:
        model_name, run_name = cfg_model_run.split("/", 1)
    else:
        typer.echo("Erro: --model deve ser no formato 'modelo/run'", err=True)
        raise typer.Exit(1)

    gt_path = cfg_results_dir / "ground_truth" / cfg_gt_run
    model_path = cfg_results_dir / model_name / run_name

    if not gt_path.exists():
        typer.echo(f"Erro: Ground truth não encontrado: {gt_path}", err=True)
        raise typer.Exit(1)

    if not model_path.exists():
        typer.echo(f"Erro: Resultados do modelo não encontrados: {model_path}", err=True)
        raise typer.Exit(1)

    typer.echo("=" * 60)
    typer.echo("COMPARAÇÃO DE RESULTADOS")
    typer.echo("=" * 60)
    typer.echo(f"Ground Truth: ground_truth/{cfg_gt_run}")
    typer.echo(f"Modelo: {model_name}/{run_name}")
    typer.echo("-" * 60)

    try:
        metricas_df, resumo_df = compare_runs(gt_path, model_path, questions_df)

        output_dir = model_path
        metricas_path = output_dir / "metricas.csv"
        resumo_path = output_dir / "resumo.csv"

        metricas_df.to_csv(metricas_path, index=False)
        resumo_df.to_csv(resumo_path, index=False)

        typer.echo(f"  ✓ Métricas salvas em: {metricas_path}")
        typer.echo(f"  ✓ Resumo salvo em: {resumo_path}")

        f1_media = resumo_df[resumo_df["metrica"] == "f1_media"]["valor"].values[0]
        taxa_sucesso = resumo_df[resumo_df["metrica"] == "taxa_execucao_sucesso"]["valor"].values[0]
        typer.echo(f"  → F1 médio: {f1_media}")
        typer.echo(f"  → Taxa de execução com sucesso: {taxa_sucesso:.1%}")

    except Exception as e:
        typer.echo(f"  ✗ Erro ao processar: {e}", err=True)
        raise typer.Exit(1)

    typer.echo("=" * 60)
    typer.echo("Comparação concluída!")


@app.command()
def list_pairs(
    results_dir: Annotated[
        Optional[Path],
        typer.Option("--results-dir", "-r", help="Diretório com os resultados.")
    ] = RESULTS_DIR,
) -> None:
    """Lista todos os pares de comparação disponíveis."""
    if isinstance(results_dir, str):
        results_dir = Path(results_dir)

    pairs = discover_comparison_pairs(results_dir)

    if not pairs:
        typer.echo("Nenhum par de comparação encontrado.")
        typer.echo("Certifique-se de que existe ground_truth/<run> e <modelo>/<run>.")
        raise typer.Exit(1)

    typer.echo("Pares de comparação disponíveis:")
    typer.echo("-" * 50)

    gt_runs = set()
    for p in pairs:
        gt_runs.add(p["run"])

    typer.echo(f"\nGround Truth runs: {sorted(gt_runs)}")
    typer.echo("\nPares modelo/run:")

    for pair in pairs:
        typer.echo(f"  - {pair['pair_name']} (GT: {pair['run']})")


@app.command()
def config() -> None:
    """Mostra o caminho do arquivo de configuração padrão."""
    typer.echo(f"Arquivo de configuração: {COMPARE_CONFIG_FILE}")
    if COMPARE_CONFIG_FILE.exists():
        typer.echo("Status: ✓ Existe")
    else:
        typer.echo("Status: ✗ Não encontrado")


@app.command()
def export(
    pair: Annotated[
        str,
        typer.Argument(help="Par de comparação no formato 'modelo/run' (ex: Qwen3-32B-AWQ/default).")
    ],
    output: Annotated[
        Optional[Path],
        typer.Option("--output", "-o", help="Caminho do arquivo HTML de saída. Se não informado, salva no diretório do modelo.")
    ] = None,
    results_dir: Annotated[
        Optional[Path],
        typer.Option("--results-dir", "-r", help="Diretório com os resultados.")
    ] = RESULTS_DIR,
) -> None:
    """
    Exporta relatório HTML completo de um par de comparação.

    Gera um arquivo HTML auto-contido com Dashboard, tabela de perguntas
    e detalhes de cada consulta SQL, incluindo comparação com ground truth.

    Exemplos:
        text2sql compare export Qwen3-32B-AWQ/default
        text2sql compare export Qwen3-32B-AWQ/default -o relatorio.html
    """
    if isinstance(results_dir, str):
        results_dir = Path(results_dir)

    if "/" not in pair:
        typer.echo("Erro: Par deve estar no formato 'modelo/run' (ex: Qwen3-32B-AWQ/default)", err=True)
        raise typer.Exit(1)

    model_name, run_name = pair.split("/", 1)
    model_path = results_dir / model_name / run_name
    metricas_path = model_path / "metricas.csv"
    resumo_path = model_path / "resumo.csv"

    if not model_path.exists():
        typer.echo(f"Erro: Diretório do modelo não encontrado: {model_path}", err=True)
        raise typer.Exit(1)

    if not metricas_path.exists() or not resumo_path.exists():
        typer.echo(f"Erro: Métricas não encontradas em {model_path}", err=True)
        typer.echo("Execute 'text2sql compare run' primeiro para gerar as métricas.", err=True)
        raise typer.Exit(1)

    if output is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_pair = pair.replace("/", "_")
        output = model_path / f"relatorio_{safe_pair}_{timestamp}.html"

    typer.echo("=" * 60)
    typer.echo("EXPORTAÇÃO DE RELATÓRIO HTML")
    typer.echo("=" * 60)
    typer.echo(f"Par: {pair}")
    typer.echo(f"Saída: {output}")
    typer.echo("-" * 60)

    try:
        typer.echo("Gerando relatório HTML...")
        html_content = generate_full_html_report(pair)

        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(html_content, encoding="utf-8")

        typer.echo(f"  ✓ Relatório salvo em: {output}")
        typer.echo(f"  → Tamanho: {output.stat().st_size / 1024:.1f} KB")

    except Exception as e:
        typer.echo(f"  ✗ Erro ao gerar relatório: {e}", err=True)
        raise typer.Exit(1)

    typer.echo("=" * 60)
    typer.echo("Exportação concluída!")
    typer.echo(f"Abra o arquivo no navegador: file://{output.absolute()}")


def main() -> int:
    """
    Função principal do CLI de comparação.

    Returns:
        Código de saída (0 para sucesso, 1 para erro).
    """
    try:
        app()
        return 0
    except SystemExit as e:
        return e.code if isinstance(e.code, int) else 1


if __name__ == "__main__":
    sys.exit(main())
