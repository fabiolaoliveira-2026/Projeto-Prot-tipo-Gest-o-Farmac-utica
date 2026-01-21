"""Model utilities for Unsloth-based fine-tuning, PEFT configuration, and dataset preparation.

This module integrates Unsloth's FastLanguageModel to load models and tokenizers, configure LoRA/PEFT adapters,
and prepare text datasets for supervised fine-tuning.
"""

import os
from datasets import Dataset
import torch
import pandas as pd
from typing import Any
from pathlib import Path

from unsloth import FastLanguageModel
from sklearn.model_selection import train_test_split

from app.llm.utils.logger import Logger


class UnslothModel:
    """Utilities to load Unsloth models, configure PEFT, and prepare fine-tuning datasets.

    This class wraps FastLanguageModel to manage model/tokenizer loading, adapter setup, and dataset formatting.
    """
    def __init__(self):
        self.tokenizer = None
        self.model = None
        self.device = "cuda"

        self.logger = Logger(__name__)

    def load_model(
            self,
            model_name: str,
            **kwargs: Any
    ) -> None:
        if not model_name:
            raise ValueError("Model name not specified")

        max_seq_length = kwargs.get("max_seq_length", 2048)

        dtype_str = kwargs.get("dtype", "fp16")
        if dtype_str == "fp16":
            dtype = torch.float16
        elif dtype_str == "bf16":
            dtype = torch.bfloat16
        else:
            dtype = None

        load_in_4bit = kwargs.get("load_in_4bit", False)

        token = kwargs.get("token")
        if token is None:
            token = os.environ.get("LLM_TOKEN")

        try:
            model, tokenizer = FastLanguageModel.from_pretrained(
                model_name=model_name,
                max_seq_length=max_seq_length,
                dtype=dtype,
                load_in_4bit=load_in_4bit,
                token=token
            )
            self.model, self.tokenizer = model, tokenizer
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
        except Exception as e:
            raise RuntimeError(f"Failed to load model {model_name}: {str(e)}")

    def get_peft_model(
            self,
            **kwargs: Any
    ) -> None:
        if not self.model:
            raise Exception("Model is not loaded")

        try:
            self.model = FastLanguageModel.get_peft_model(
                self.model,
                r=kwargs.get("r", 16),
                target_modules=kwargs.get("target_modules", [
                    "q_proj", "k_proj", "v_proj", "o_proj",
                    "gate_proj", "up_proj", "down_proj",
                ]),
                lora_alpha=kwargs.get("lora_alpha", 16),
                lora_dropout=kwargs.get("lora_dropout", 0),
                bias=kwargs.get("bias", "none"),
                use_gradient_checkpointing=kwargs.get("use_gradient_checkpointing", "unsloth"),
                random_state=kwargs.get("random_state", 3407),
                use_rslora=kwargs.get("use_rslora", False),
                loftq_config=kwargs.get("loftq_config", None),
            )
        except Exception as e:
            raise RuntimeError(f"Failed to configure PEFT model: {str(e)}")

    def prepare_model_for_inference(self) -> None:
        if not self.model:
            raise Exception("Model is not loaded")
        self.model = FastLanguageModel.for_inference(self.model)

    @staticmethod
    def _read_data(data_path, input_field, output_field, **kwargs):
        path = Path(data_path)
        if not path.exists():
            raise FileNotFoundError(f"Data file not found: {data_path}")

        if path.suffix == ".csv":
            df = pd.read_csv(data_path, sep=kwargs.get("sep", ","))
        elif path.suffix == ".json":
            df = pd.read_json(data_path)
        elif path.suffix == ".xlsx":
            df = pd.read_excel(data_path)
        elif path.suffix == ".parquet":
            df = pd.read_parquet(data_path)
        else:
            raise ValueError(f"Unsupported data file format: {path.suffix}")

        if input_field not in df.columns:
            raise ValueError(f"Input field '{input_field}' not found in data")
        
        if output_field not in df.columns:
            raise ValueError(f"Output field '{output_field}' not found in data")
        return df


    def prepare_dataset(
        self,
        data_path: str,
        prompt_template: str,
        input_field: str,
        output_field: str,
        **kwargs: Any
    ) -> Dataset:
        """
        Prepare a dataset for fine-tuning.
        
        Args:
            data_path (str): Path to the data file (CSV).
            prompt_template (str): Prompt template to use for formatting examples.
            input_field (str): Field in the data to use as input.
            output_field (str): Field in the data to use as output.
            config (Dict[str, Any]): Configuration dictionary.
            tokenizer (PreTrainedTokenizer): Tokenizer to use for formatting examples.
        
        Returns:
            Tuple[Dataset, pd.DataFrame]: The prepared dataset and test dataframe.
        
        Raises:
            FileNotFoundError: If the data file does not exist.
            ValueError: If the data file is not valid.
        """

        if not self.tokenizer:
            raise ValueError("Tokenizer not loaded. Call load_model first.")
        
        
        df = self._read_data(data_path, input_field, output_field, **kwargs)

        extra_data_path = kwargs.get("extra_path")
        if extra_data_path:
            self.logger.info(f"Loading extra data from {extra_data_path}")
            extra_df = self._read_data(extra_data_path, input_field, output_field, **kwargs)
            df = pd.concat([df, extra_df], ignore_index=True)
        
        
        # Create a formatting function for the dataset
        def formatting_prompts_func(examples):
            inputs = examples[input_field]
            outputs = examples[output_field]
            texts = []
            
            for input_text, output_text in zip(inputs, outputs):
                # Format the prompt and add EOS token
                text = prompt_template.format(input_text, output_text) + self.tokenizer.eos_token
                texts.append(text)
            
            return {"text": texts}
        
        # Convert to Dataset and apply formatting
        dataset_df = Dataset.from_pandas(df)
        dataset_df = dataset_df.map(formatting_prompts_func, batched=True)
        
        return dataset_df