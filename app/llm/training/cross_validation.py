import yaml
import subprocess
from pathlib import Path
import sys
import pandas as pd
import json
import glob
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px

import base64

from app.llm.data.splitter import Splitter
from app.llm.utils.logger import Logger

class CrossValidator:
    def __init__(self, config_path: str):
        self.config_path = Path(config_path)
        self.logger = Logger(__name__)
        with open(self.config_path, 'r') as f:
            self.config = yaml.safe_load(f)

    def run(self):
        # 1. Split data into folds
        self.logger.info("Splitting data into folds...")
        data_split_config = self.config.get("data_split", {})
        if not data_split_config:
            raise ValueError("`data_split` configuration not found in config file.")

        splitter = Splitter(
            data_path=data_split_config["data_path"],
            output_dir=data_split_config["output_dir"],
            k_folds=data_split_config["k_folds"]
        )
        splitter.split()
        self.logger.info("Data splitting complete.")

        # 2. Run training and evaluation for each fold
        base_output_dir = Path(self.config.get("output_dir", "resultados/modelo_treinado"))
        folds_dir = Path(data_split_config["output_dir"])
        num_folds = data_split_config["k_folds"]
        all_metrics = []

        for fold in range(num_folds):
            self.logger.info(f"Processing fold {fold}/{num_folds - 1}")
            fold_dir = folds_dir / f"fold_{fold}"
            fold_output_dir = base_output_dir / f"fold_{fold}"
            fold_output_dir.mkdir(parents=True, exist_ok=True)

            # Create a temporary config for this fold's training
            fold_config = self.config.copy()
            fold_config["dataset"]["path"] = str(fold_dir / "train.csv")
            fold_config["output_dir"] = str(fold_output_dir)
            
            fold_config_path = self.config_path.parent / f"temp_config_fold_{fold}.yaml"
            with open(fold_config_path, 'w') as f:
                yaml.dump(fold_config, f)

            # Train model
            self.logger.info(f"Training model for fold {fold}...")
            train_command = [
                sys.executable,
                "-m", "app.llm",
                "train",
                str(fold_config_path)
            ]
            subprocess.run(train_command, check=True)
            self.logger.info(f"Training for fold {fold} complete.")

            # Evaluate model
            self.logger.info(f"Evaluating model for fold {fold}...")
            dataset_config = self.config.get("dataset", {})
            evaluate_command = [
                sys.executable,
                "-m", "app.llm",
                "evaluate",
                str(fold_output_dir / "model"),
                str(fold_dir / "test.csv"),
                dataset_config["system_prompt"],
                str(fold_output_dir / "evaluation"),
                "--input-field", dataset_config["input_field"],
                "--label-field", dataset_config["output_field"]
            ]
            subprocess.run(evaluate_command, check=True)
            self.logger.info(f"Evaluation for fold {fold} complete.")

            # Store metrics
            metrics_path = fold_output_dir / "evaluation" / "metrics.json"
            if metrics_path.exists():
                with open(metrics_path, 'r') as f:
                    metrics = json.load(f)
                    all_metrics.append(metrics)

            # Clean up temporary config file
            fold_config_path.unlink()

        self.logger.info("Cross-validation complete.")
        self._generate_report(all_metrics, base_output_dir)

    def _generate_report(self, all_metrics, base_output_dir):
        self.logger.info("Generating cross-validation report...")

        metrics_df = pd.DataFrame(all_metrics)
        metrics_df.index.name = "Fold"

        summary_stats = {
            "mean": metrics_df.mean().to_dict(),
            "std": metrics_df.std().to_dict(),
        }

        report_html = self._generate_html_structure(summary_stats, metrics_df, base_output_dir)

        report_path = base_output_dir / "cross_validation_report.html"
        with open(report_path, 'w') as f:
            f.write(report_html)

        self.logger.info(f"Report saved to {report_path}")

    def _generate_html_structure(self, summary_stats, metrics_df, base_output_dir):
        metrics_summary_html = self._generate_metrics_summary_html(summary_stats)
        metrics_plot_html = self._generate_metrics_plot_html(summary_stats)
        metrics_boxplot_html = self._generate_metrics_boxplot_html(metrics_df)
        fold_details_html = self._generate_fold_details_html(metrics_df, base_output_dir)

        # Build a dynamic, human-friendly report title using the output field if available
        dataset_cfg = self.config.get("dataset", {}) if hasattr(self, "config") else {}
        target_name = str(dataset_cfg.get("output_field", "")).strip()
        report_title = f"Relatório de Cross-Validation — {target_name}" if target_name else "Relatório de Cross-Validation"

        return f"""
        <html>
        <head>
            <meta charset=\"utf-8\" />
            <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
            <title>{report_title}</title>
            <link href=\"https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap\" rel=\"stylesheet\">
            <script src=\"https://cdn.plot.ly/plotly-latest.min.js\"></script>
            <style>
                :root {{
                    --md-primary: #64B5F6;
                    --md-on-primary: #FFFFFF;
                    --md-surface: #FAFAFA;
                    --md-on-surface: #1F2937;
                    --md-card: #FFFFFF;
                    --md-border: #E5E7EB;
                    --md-elev: 0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24);
                }}
                * {{ box-sizing: border-box; }}
                body {{
                    font-family: 'Roboto', system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, Cantarell, Noto Sans, sans-serif;
                    margin: 0; padding: 0; background: var(--md-surface); color: var(--md-on-surface);
                    line-height: 1.5;
                }}
                .header {{
                    background: var(--md-primary); color: var(--md-on-primary);
                    padding: 2.5rem 1rem; text-align: center;
                }}
                h1 {{ font-size: 2rem; font-weight: 700; margin: 0; }}
                .subtitle {{ opacity: 0.9; margin-top: .25rem; font-weight: 400; }}
                .container {{
                    padding: 2rem 1rem; max-width: 1280px; margin: 0 auto;
                }}
                h2 {{ font-size: 1.25rem; font-weight: 600; margin: 2rem 0 1rem; }}
                .card {{ background: var(--md-card); border-radius: 12px; box-shadow: var(--md-elev); padding: 1rem; margin: 1rem 0; }}
                table {{
                    width: 100%; border-collapse: collapse; background: var(--md-card);
                    border-radius: 12px; overflow: hidden; box-shadow: var(--md-elev);
                }}
                thead th {{ background: #F3F4F6; color: #374151; text-align: left; font-weight: 600; padding: 12px 14px; border-bottom: 1px solid var(--md-border); }}
                tbody td {{ padding: 12px 14px; border-bottom: 1px solid var(--md-border); }}
                tbody tr:last-child td {{ border-bottom: 0; }}
                .grid-container {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 1rem; }}
                .cm-grid {{ grid-template-columns: repeat(2, 1fr); }}
                @media (max-width: 900px) {{ .cm-grid {{ grid-template-columns: 1fr; }} }}
                .plot {{ background: var(--md-card); border-radius: 12px; box-shadow: var(--md-elev); padding: .5rem; }}
                img {{ max-width: 100%; height: auto; border-radius: 8px; display: block; }}
                .section {{ margin-top: 1.5rem; }}
            </style>
        </head>
        <body>
            <div class=\"header\">
                <h1>{report_title}</h1>
                <div class=\"subtitle\">Resumo visual e estatístico do desempenho do modelo por validação cruzada</div>
            </div>
            <div class=\"container\">
                <div class=\"section\">{metrics_summary_html}</div>
                <div class=\"section\">{metrics_plot_html}</div>
                <div class=\"section\">{metrics_boxplot_html}</div>
                <div class=\"section\">{fold_details_html}</div>
            </div>
        </body>
        </html>
        """

    def _get_palette(self):
        # Use Plotly's built-in D3 qualitative palette for consistent colors across charts
        return px.colors.qualitative.D3

    def _generate_metrics_summary_html(self, summary_stats):
        html = """
        <h2>Resumo Geral das Métricas</h2>
        <div class="card">
        <table>
            <thead>
                <tr><th>Métrica</th><th>Média</th><th>Desvio Padrão</th></tr>
            </thead>
            <tbody>
        """
        for metric, value in summary_stats['mean'].items():
            std_dev = summary_stats['std'][metric]
            html += f"<tr><td>{metric.capitalize()}</td><td>{value:.4f}</td><td>{std_dev:.4f}</td></tr>"
        html += """
            </tbody>
        </table>
        </div>
        """
        return html

    def _generate_metrics_plot_html(self, summary_stats):
        # Prepare data
        metrics = list(summary_stats['mean'].keys())
        values = list(summary_stats['mean'].values())
        y_max = max(values) if values else 1
        y_top = 1 if y_max <= 0 else y_max * 1.15

        palette = self._get_palette()
        colors = [palette[i % len(palette)] for i in range(len(metrics))]

        fig = go.Figure(data=[
            go.Bar(
                x=metrics,
                y=values,
                marker_color=colors,
                texttemplate='%{y:.4f}',
                textposition='outside',
                hovertemplate='%{x}<br>Média: %{y:.4f}<extra></extra>'
            )
        ])
        fig.update_layout(
            title_text='<b>Médias das Métricas</b>',
            xaxis_title='Métricas',
            yaxis_title='Pontuações',
            template='plotly_white',
            font=dict(family='Roboto', size=14, color='#1F2937'),
            uniformtext_minsize=10,
            uniformtext_mode='hide',
            margin=dict(t=60, r=20, l=40, b=40),
            bargap=0.25,
            showlegend=False,
        )
        # Add headroom for outside labels
        fig.update_yaxes(range=[0, y_top], gridcolor='#E5E7EB', zeroline=False)
        fig.update_xaxes(gridcolor='#F3F4F6')

        return f'''
        <h2>Visualização das Métricas</h2>
        <div class="plot">
            {fig.to_html(full_html=False, include_plotlyjs='cdn')}
        </div>
        '''

    def _generate_metrics_boxplot_html(self, metrics_df):
        fig = go.Figure()
        palette = self._get_palette()
        for metric in metrics_df.columns:
            fig.add_trace(go.Box(y=metrics_df[metric], name=metric.capitalize(), boxmean='sd'))
        
        fig.update_layout(
            title_text='<b>Distribuição das Métricas por Fold</b>',
            yaxis_title='Pontuações',
            template='plotly_white',
            font=dict(family='Roboto', size=14, color='#1F2937'),
            margin=dict(t=60, r=20, l=40, b=40),
            showlegend=True,
            colorway=palette,
        )
        fig.update_yaxes(gridcolor='#E5E7EB', zeroline=False)
        fig.update_xaxes(gridcolor='#F3F4F6')
        return f'''
        <div class="plot">
            {fig.to_html(full_html=False, include_plotlyjs='cdn')}
        </div>
        '''

    def _generate_fold_details_html(self, metrics_df, base_output_dir):
        html = """
        <h2>Métricas por Fold</h2>
        <div class="card">
        """
        html += metrics_df.to_html(classes='sortable', float_format=lambda x: f'{x:.4f}')
        html += """
        </div>
        <h2>Matrizes de Confusão por Fold</h2>
        <div class="grid-container cm-grid">
        """
        for fold in range(len(metrics_df)):
            fold_eval_dir = base_output_dir / f"fold_{fold}" / "evaluation"
            cm_path = fold_eval_dir / "confusion_matrix.png"
            if cm_path.exists():
                img_base64 = self._embed_image_base64(cm_path)
                html += f'''
                <div class="plot">
                    <h3>Fold {fold}</h3>
                    <img src="data:image/png;base64,{img_base64}" alt="Matriz de confusão do Fold {fold}">
                </div>
                '''
        html += "</div>"
        return html

    def _embed_image_base64(self, image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode('utf-8')