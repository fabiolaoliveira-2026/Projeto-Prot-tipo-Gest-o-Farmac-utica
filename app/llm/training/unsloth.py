import os
import torch
from typing import Dict, Any, Optional, Tuple
from unsloth import FastLanguageModel
from trl import SFTTrainer, SFTConfig
from datasets import Dataset

from app.llm.model.unsloth import UnslothModel


class UnslothFT:
    def __init__(self):
        self.model = UnslothModel()
        self.dataset = None
        self.output_dir = None

    def load_model(self, model_name: str, **kwargs: Any) -> None:
        self.model.load_model(model_name, **kwargs)

    def prepare_dataset(self, dataset_path: str, prompt_template: str, input_field: str, output_field: str, output_dir: str, **kwargs: Any) -> Dataset:
        self.dataset = self.model.prepare_dataset(dataset_path, prompt_template, input_field, output_field, output_dir=output_dir, **kwargs) 
        self.output_dir = output_dir

    def fine_tune_model(
            self,
            model_name: str,
            **kwargs: Any
    ) -> None:
        # Load model and tokenizer if not already loaded
        model_config = kwargs.get("model", {})
        if self.model.tokenizer is None or self.model.model is None:
            self.model.load_model(model_name, **model_config)

        if not self.dataset:
            raise ValueError("Dataset not prepared. Call prepare_dataset first.")

        # Configure model for PEFT
        self.model.get_peft_model(**kwargs.get("fine_tuning", {}))

        # Get training configuration
        training_config = kwargs.get("training", {})


        # Get data configuration
        data_config = kwargs.get("dataset_config") or kwargs.get("dataset", {})

        sft_config = SFTConfig(
            # TrainingArguments fields
            per_device_train_batch_size=training_config.get("per_device_train_batch_size", 2),
            gradient_accumulation_steps=training_config.get("gradient_accumulation_steps", 4),
            warmup_steps=training_config.get("warmup_steps", 5),
            num_train_epochs=training_config.get("num_train_epochs", 1),
            max_steps=training_config.get("max_steps", 120),
            learning_rate=training_config.get("learning_rate", 2e-4),
            fp16=training_config.get("fp16", True),
            bf16=training_config.get("bf16", False),
            logging_steps=training_config.get("logging_steps", 1),
            optim=training_config.get("optim", "adamw_8bit"),
            weight_decay=training_config.get("weight_decay", 0.01),
            lr_scheduler_type=training_config.get("lr_scheduler_type", "linear"),
            seed=training_config.get("seed", 3407),
            output_dir=self.output_dir,
            report_to=training_config.get("report_to", "none"),
            # SFT-specific fields
            dataset_text_field="text",
            max_length=kwargs.get("model", {}).get("max_seq_length", 2048),
            packing=data_config.get("packing", False),
            dataset_num_proc=data_config.get("dataset_num_proc", 2),
        )

        # Create trainer
        trainer = SFTTrainer(
            model=self.model.model,
            processing_class=self.model.tokenizer,
            train_dataset=self.dataset,
            args=sft_config,
        )

        # Train the model
        try:
            trainer_stats = trainer.train()
        except Exception as e:
            raise RuntimeError(f"Failed to fine-tune model: {str(e)}")

        # Prepare model for inference
        self.model.prepare_model_for_inference()


        model_save_dir = os.path.join(self.output_dir, "model")
        os.makedirs(model_save_dir, exist_ok=True)

        self.model.model.save_pretrained(model_save_dir)
        self.model.tokenizer.save_pretrained(model_save_dir)

        with open(os.path.join(model_save_dir, "config.json"), "w") as f:
            import json
            json.dump(kwargs, f, indent=2)