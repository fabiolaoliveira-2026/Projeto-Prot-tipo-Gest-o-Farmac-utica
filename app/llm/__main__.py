import typer
from rich.console import Console
import yaml
from pathlib import Path
import sys

# Add the project root to the python path
sys.path.append(str(Path(__file__).parent.parent))

from app.llm.evaluate.generator import ModelEvaluator
from app.llm.data.splitter import Splitter
from app.llm.training.cross_validation import CrossValidator
from app.llm.model.transformer import TransformerModel
import pandas as pd
from tqdm import tqdm
import torch

app = typer.Typer()
console = Console()

@app.command()
def split_data(config_path: Path = typer.Argument(..., help="Path to the configuration YAML file.")):
    """
    Splits the dataset into k-folds based on the provided configuration.
    """
    if not config_path.is_file():
        console.print(f"[bold red]Error:[/bold red] Config file not found at {config_path}")
        raise typer.Exit(code=1)

    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    data_config = config.get("data_split", {})
    data_path = data_config.get("data_path")
    output_dir = data_config.get("output_dir")
    k_folds = data_config.get("k_folds")

    if not all([data_path, output_dir, k_folds]):
        console.print("[bold red]Error:[/bold red] Missing data_split configuration in config.yaml")
        raise typer.Exit(code=1)

    try:
        console.print("[bold green]Starting data splitting process...[/bold green]")
        splitter = Splitter(data_path, output_dir, k_folds)
        splitter.split()
        console.print("[bold green]Data splitting finished successfully![/bold green]")

    except Exception as e:
        console.print(f"[bold red]An error occurred during data splitting:[/bold red] {e}")
        raise typer.Exit(code=1)

@app.command()
def cross_validate(config_path: Path = typer.Argument(..., help="Path to the configuration YAML file.")):
    """
    Runs cross-validation by splitting data, training, and evaluating for each fold.
    """
    if not config_path.is_file():
        console.print(f"[bold red]Error:[/bold red] Config file not found at {config_path}")
        raise typer.Exit(code=1)

    try:
        console.print("[bold green]Starting cross-validation process...[/bold green]")
        validator = CrossValidator(str(config_path))
        validator.run()
        console.print("[bold green]Cross-validation finished successfully![/bold green]")

    except Exception as e:
        console.print(f"[bold red]An error occurred during cross-validation:[/bold red] {e}")
        raise typer.Exit(code=1)

@app.command()
def train(config_path: Path = typer.Argument(..., help="Path to the training configuration YAML file.")):
    """
    Trains a model using the provided configuration file.
    """
    if not config_path.is_file():
        console.print(f"[bold red]Error:[/bold red] Config file not found at {config_path}")
        raise typer.Exit(code=1)

    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    console.print("[bold green]Starting training process...[/bold green]")
    console.print(f"Config file: {config_path}")

    try:
        # Lazy import to avoid requiring Unsloth when only running prediction/help
        from app.llm.training.unsloth import UnslothFT
        trainer = UnslothFT()

        console.print("[bold]Loading model...[/bold]")
        model_params = config.get('model', {})
        trainer.load_model(
            model_name=config.get('model_name'),
            **model_params
        )

        console.print("[bold]Preparing dataset...[/bold]")
        dataset_params = config.get('dataset', {})
        dataset_kwargs = {k: v for k, v in dataset_params.items() if k not in {'path', 'prompt_template', 'input_field', 'output_field'}}
        trainer.prepare_dataset(
            dataset_path=dataset_params.get('path'),
            prompt_template=dataset_params.get('prompt_template'),
            input_field=dataset_params.get('input_field'),
            output_field=dataset_params.get('output_field'),
            output_dir=config.get('output_dir'),
            **dataset_kwargs
        )
        console.print("[green]Dataset prepared successfully.[/green]")

        console.print("[bold]Starting fine-tuning...[/bold]")
        train_kwargs = {k: v for k, v in config.items() if k != 'model_name'}
        trainer.fine_tune_model(
            model_name=config.get('model_name'),
            **train_kwargs
        )
        console.print("[bold green]Training finished successfully![/bold green]")

    except Exception as e:
        console.print(f"[bold red]An error occurred during training:[/bold red] {e}")
        raise typer.Exit(code=1)

@app.command()
def evaluate(
    model_path: Path = typer.Argument(..., help="Path to the trained model directory."),
    dataset_path: Path = typer.Argument(..., help="Path to the test dataset JSON file."),
    system_prompt_template: str = typer.Argument(..., help="The system prompt template to use."),
    output_dir: Path = typer.Argument(..., help="Directory to save evaluation results."),
    input_field: str = typer.Option("input", help="The input field name in the dataset."),
    label_field: str = typer.Option("label", help="The ground truth label field name in the dataset."),
):
    """
    Evaluates a trained model using the provided test dataset.
    """
    if not model_path.is_dir():
        console.print(f"[bold red]Error:[/bold red] Model directory not found at {model_path}")
        raise typer.Exit(code=1)

    if not dataset_path.is_file():
        console.print(f"[bold red]Error:[/bold red] Test dataset not found at {dataset_path}")
        raise typer.Exit(code=1)

    console.print("[bold green]Starting evaluation process...[/bold green]")
    console.print(f"Model path: {model_path}")
    console.print(f"Test dataset: {dataset_path}")
    console.print(f"Output directory: {output_dir}")

    try:
        evaluator = ModelEvaluator(str(model_path), str(output_dir))

        console.print("[bold]Running evaluation...[/bold]")
        metrics = evaluator.run_evaluation(dataset_path, system_prompt_template, input_field, label_field)
        
        console.print("[bold green]Evaluation finished successfully![/bold green]")
        console.print(f"Metrics: {metrics}")

    except Exception as e:
        console.print(f"[bold red]An error occurred during evaluation:[/bold red] {e}")
        raise typer.Exit(code=1)

@app.command()
def predict(
    config_path: Path = typer.Argument(..., help="Path to the YAML configuration file for prediction."),
):
    """Run a model over a CSV base and export predictions, using only values from config.yaml.

    The config may contain an optional 'predict' section to override defaults:
      predict:
        model_path: "resultados/modelo_treinado/model"  # or HF model id
        input_path: "dados/cleaned_data.csv"
        output_path: "resultados/predictions.csv"
        prompt_type: "unsloth"  # or "llama"
        max_new_tokens: 64
        temperature: 0.01
        do_sample: false
        device: "cuda"
    """
    # Validate config
    if not config_path.is_file():
        console.print(f"[bold red]Error:[/bold red] Config file not found at {config_path}")
        raise typer.Exit(code=1)

    try:
        with open(config_path, 'r') as f:
            cfg = yaml.safe_load(f)
    except Exception as e:
        console.print(f"[bold red]Error reading config:[/bold red] {e}")
        raise typer.Exit(code=1)

    dataset_cfg = cfg.get("dataset", {}) or {}
    pred_cfg = cfg.get("predict", {}) or {}

    # Resolve model identifier (local dir or HF id)
    model_id = pred_cfg.get("model_path")
    if model_id is None:
        out_dir = cfg.get("output_dir")
        if out_dir:
            candidate = Path(out_dir) / "model"
            if candidate.exists():
                model_id = str(candidate)
    if model_id is None:
        model_id = cfg.get("model_name")
    if model_id is None:
        console.print("[bold red]Error:[/bold red] Could not resolve model path/id. Set predict.model_path, or ensure output_dir/model exists, or provide model_name in config.")
        raise typer.Exit(code=1)

    # Resolve input CSV
    input_path_str = pred_cfg.get("input_path") or dataset_cfg.get("path")
    if not input_path_str:
        console.print("[bold red]Error:[/bold red] Could not resolve input CSV path. Set predict.input_path or dataset.path in config.")
        raise typer.Exit(code=1)
    input_path = Path(input_path_str)
    if not input_path.is_file():
        console.print(f"[bold red]Error:[/bold red] Input CSV not found at {input_path}")
        raise typer.Exit(code=1)

    # Resolve output path
    output_path_str = pred_cfg.get("output_path")
    if not output_path_str:
        out_dir = cfg.get("output_dir")
        if out_dir:
            output_path_str = str(Path(out_dir) / "predictions.csv")
        else:
            output_path_str = "predictions.csv"
    output_path = Path(output_path_str)

    # Load data
    try:
        df = pd.read_csv(input_path)
    except Exception as e:
        console.print(f"[bold red]Error reading input CSV:[/bold red] {e}")
        raise typer.Exit(code=1)

    # Resolve fields and prompts
    input_field = pred_cfg.get("input_field") or dataset_cfg.get("input_field")
    system_prompt = pred_cfg.get("system_prompt", dataset_cfg.get("system_prompt", "")) or ""

    if input_field is None:
        # Try common defaults
        for candidate in ["NOTA_CLINICA_ORIGINAL", "input", "text"]:
            if candidate in df.columns:
                input_field = candidate
                break

    if input_field is None or input_field not in df.columns:
        console.print(f"[bold red]Error:[/bold red] Input field not found in CSV. Configure predict.input_field or dataset.input_field. Available columns: {list(df.columns)}")
        raise typer.Exit(code=1)

    # Prepare model
    device = pred_cfg.get("device") or ("cuda" if torch.cuda.is_available() else "cpu")
    try:
        model = TransformerModel()
        if device.lower() == "cpu":
            load_kwargs = dict(device_map="cpu", dtype=torch.float32, device="cpu")
        else:
            load_kwargs = dict(device_map="cuda", dtype=torch.float16, device="cuda")
        model.load_transformer_model(str(model_id), **load_kwargs)
    except Exception as e:
        console.print(f"[bold red]Error loading model:[/bold red] {e}")
        raise typer.Exit(code=1)

    # Generation settings
    max_new_tokens = int(pred_cfg.get("max_new_tokens", 64))
    temperature = float(pred_cfg.get("temperature", 0.01))
    do_sample = bool(pred_cfg.get("do_sample", False))

    # Generate predictions
    console.print("[bold green]Generating predictions...[/bold green]")
    predictions = []
    gen_cfg = dict(max_new_tokens=max_new_tokens, do_sample=do_sample, temperature=temperature)
    try:
        for _, row in tqdm(df.iterrows(), total=len(df), desc="Predict"):
            prompt = model.generate_prompt(row[input_field], system_prompt)
            generated = model.generate(prompt, gen_cfg)
            generated = generated.replace("<|end_of_text|>", "").strip()
            predictions.append(generated)
    except Exception as e:
        console.print(f"[bold red]Error during generation:[/bold red] {e}")
        raise typer.Exit(code=1)

    # Save predictions
    try:
        df_out = df.copy()
        df_out["prediction"] = predictions
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df_out.to_csv(output_path, index=False)
        console.print(f"[bold green]Predictions saved to[/bold green] {output_path}")
    except Exception as e:
        console.print(f"[bold red]Error saving predictions:[/bold red] {e}")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()