"""Evaluation pipeline to generate model predictions and compute metrics over a dataset.

This module provides utilities to load a generation model, create prompts, run inference, and
store predictions and evaluation artifacts.
"""

import os

import json
import pandas as pd
from tqdm import tqdm
from datasets import load_dataset, Dataset
from app.llm.model.transformer import TransformerModel
from app.llm.evaluate.evaluate import Evaluate

class ModelEvaluator:
    def __init__(self, model_path: str, output_dir: str):
        self.model = TransformerModel()
        self.model.load_transformer_model(model_path)
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def load_test_dataset(self, dataset_path: str):
        
        if not os.path.exists(dataset_path):
            raise FileNotFoundError(f"Test dataset not found at {dataset_path}")

        # Load CSV and convert to Dataset
        df = pd.read_csv(dataset_path)
        return df

    @staticmethod
    def create_pred(value1, value2):
        if value1.lower() == "ni" and value2.lower() != "ni":
            return True
        if value1.lower() != "ni" and value2.lower() != "ni" and value1.lower() != value2.lower():
            return False
        if value2.lower() != "ni":
            return True
        if value2.lower() == "ni":
            return False

    def run_evaluation(self, dataset_path, system_prompt,  input_field: str, label_field: str):

        df = self.load_test_dataset(dataset_path)

        # Generate predictions
        predictions = []

        for _, row in tqdm(df.iterrows(), desc="Evaluating predictions"):
            prompt = self.model.generate_prompt(row[input_field], system_prompt)
            generated_text = self.model.generate(prompt, dict(max_new_tokens=64, do_sample=False, temperature=0.01))
            generated_text = generated_text.replace("<|end_of_text|>", "").strip()
            predictions.append(generated_text)

        df["prediction"] = predictions
        df["norm_prediction"] = df.apply(lambda x: self.create_pred(x[label_field], x["prediction"]), axis=1)

        # Extract labels and predictions
        y_true = df[label_field]
        y_pred =df["norm_prediction"]

        y_true = y_true.apply(lambda x: True if x.lower() != "ni" else False)

        # Perform evaluation
        evaluator = Evaluate(y_true, y_pred)
        metrics = evaluator.calculate_metrics()

        # Save results
        results_df = df[[input_field, label_field, "prediction"]]
        results_df.to_csv(os.path.join(self.output_dir, "predictions.csv"), index=False)

        # Save metrics
        with open(os.path.join(self.output_dir, "metrics.json"), "w") as f:
            f.write(json.dumps(metrics))

        evaluator.plot_metrics(f"{label_field} results", filepath=os.path.join(self.output_dir, "metrics.png"), add_hline=True)

        # Save confusion matrix plot
        evaluator.plot_confusion_matrix(
            title="Confusion Matrix",
            filepath=os.path.join(self.output_dir, "confusion_matrix.png")
        )

        return metrics