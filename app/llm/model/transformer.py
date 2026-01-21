"""Utilities to load and run causal language models for prompt-based text generation.

This module wraps Hugging Face Transformers to load tokenizers and models, build prompts, and generate text
on CUDA or CPU.
"""

import re
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from transformers import set_seed

class TransformerModel:
    """High-level wrapper around a causal LM and tokenizer for prompt-based generation.

    This class manages tokenizer and model loading, builds prompts using the tokenizer's chat template,
    and runs text generation.
    """
    def __init__(self):
        self.tokenizer = None
        self.model = None
        self.device = "cuda"

    @staticmethod
    def _load_tokenizer(model_name, **kwargs):
        """Load a tokenizer from a pretrained identifier or local path.

        Args:
            model_name (str): Model identifier on the Hub or a local directory path.
            **kwargs: Optional keyword arguments. Recognized keys include:
                - token: Authentication token for accessing private models.

        Returns:
            transformers.PreTrainedTokenizer: The loaded tokenizer instance.
        """
        tokenizer = AutoTokenizer.from_pretrained(model_name, token=kwargs.get("token"))
        return tokenizer

    @staticmethod
    def _load_model(model_name, **kwargs):
        """Load a causal language model from a pretrained identifier or local path.

        Args:
            model_name (str): Model identifier on the Hub or a local directory path.
            **kwargs: Optional keyword arguments. Recognized keys include:
                - token: Authentication token for private models.
                - dtype: torch dtype for weights (default: torch.float16).
                - device_map: Device mapping, e.g., 'cuda' or 'auto'.

        Returns:
            transformers.PreTrainedModel: The loaded causal language model.
        """
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            token=kwargs.get("token"),
            torch_dtype=kwargs.get("dtype", torch.float16),
            device_map=kwargs.get("device_map", "cuda"),
            trust_remote_code=True
        )
        return model

    def _parse_thinking_content(self, output_ids):
        """Parse thinking and content from model output with thinking mode enabled.

        Args:
            output_ids (list): List of token IDs from model generation.

        Returns:
            dict: Dictionary with 'thinking' and 'content' keys containing the parsed text.
        """
        # Method 1: Try Qwen-specific token (151668 for </think>)
        try:
            index = len(output_ids) - output_ids[::-1].index(151668)
            thinking_content = self.tokenizer.decode(output_ids[:index], skip_special_tokens=True).strip()
            final_content = self.tokenizer.decode(output_ids[index:], skip_special_tokens=True).strip()
            return {"thinking": thinking_content, "content": final_content}
        except (ValueError, AttributeError):
            pass

        # Method 2: Try to find thinking tags in the decoded text
        full_text = self.tokenizer.decode(output_ids, skip_special_tokens=False)
        
        # Pattern for <think>...</think> or similar variations
        think_patterns = [
            r'<think>(.*?)</think>(.*)',
            r'<thinking>(.*?)</thinking>(.*)',
            r'\[THINKING\](.*?)\[/THINKING\](.*)',
        ]
        
        for pattern in think_patterns:
            match = re.search(pattern, full_text, re.DOTALL | re.IGNORECASE)
            if match:
                thinking_content = match.group(1).strip()
                final_content = match.group(2).strip()
                # Clean up any remaining special tokens
                final_content = re.sub(r'<[^>]+>', '', final_content).strip()
                return {"thinking": thinking_content, "content": final_content}
        
        # Method 3: If no thinking tags found, return everything as content
        clean_text = self.tokenizer.decode(output_ids, skip_special_tokens=True).strip()
        return {"thinking": "", "content": clean_text}

    def load_transformer_model(self, model_name, **kwargs):
        """Load tokenizer and model, and set the target device.

        Args:
            model_name (str): Model identifier on the Hub or a local directory path.
            **kwargs: Optional settings. Recognized keys include:
                - token: Authentication token for private models.
                - dtype: torch dtype for weights (default: torch.float16).
                - device_map: Device mapping, e.g., 'cuda' or 'auto'.
                - device: Target device string used for inputs (default: 'cuda').
        """
        self.tokenizer = self._load_tokenizer(model_name, **kwargs)
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        self.model = self._load_model(model_name, **kwargs)
        self.device = kwargs.get("device", "cuda")

    def _generate_tokens(self, prompt, **kwargs):
        """Tokenize a prompt and move tensors to the configured device.

        Args:
            prompt (str): The full text prompt to tokenize.
            **kwargs: Optional settings. Recognized keys include:
                - truncation (bool): Whether to enable tokenizer truncation.

        Returns:
            dict: Tokenized input tensors suitable for model.generate.

        Raises:
            Exception: If the tokenizer is not loaded.
        """
        if not self.tokenizer:
            raise Exception("Model is not loaded")
        inputs = self.tokenizer(prompt, return_tensors="pt", truncation=kwargs.get("truncation", False))
        inputs = inputs.to(self.device)
        return inputs

    def _generate_text(self, inputs, enable_thinking=False, **kwargs):
        """Generate text using the loaded model and provided tokenized inputs.

        Args:
            inputs (dict): Tokenized input tensors from the tokenizer.
            enable_thinking (bool): If True, return raw output_ids for thinking parsing.
            **kwargs: Keyword args forwarded to model.generate (e.g., max_new_tokens, temperature).

        Returns:
            str or list: The decoded generated text segment after the input prompt, or raw output_ids if enable_thinking is True.

        Raises:
            Exception: If the model is not loaded.
        """
        if not self.model:
            raise Exception("Model is not loaded")
        outputs = self.model.generate(**inputs,
                                      pad_token_id=self.tokenizer.eos_token_id,
                                      **kwargs)
        output_ids = outputs[0][len(inputs["input_ids"][0]):].tolist()
        
        if enable_thinking:
            return output_ids
        
        result = self.tokenizer.decode(output_ids)
        return result

    def generate_prompt(self, user, system="", enable_thinking=False):
        """Build a model prompt using the tokenizer's chat template.

        Args:
            user (str): User input text.
            system (str): Optional system instruction.
            enable_thinking (bool): Whether to enable thinking mode for models that support it.

        Returns:
            str: The composed prompt text.

        Raises:
            Exception: If the tokenizer is not loaded.
        """
        if not self.tokenizer:
            raise Exception("Tokenizer is not loaded")

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": user})

        try:
            prompt = self.tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True,
                enable_thinking=enable_thinking
            )
        except TypeError:
            # Fallback for tokenizers that don't support enable_thinking
            prompt = self.tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True
            )
        return prompt


    def generate(self, prompt, model_config, enable_thinking=False, **kwargs):
        """Generate text from a prompt using configured generation parameters.

        Args:
            prompt (str): The fully formatted prompt sent to the model.
            model_config (dict): Generation parameters forwarded to model.generate (e.g., max_new_tokens).
            enable_thinking (bool): If True, parse and return thinking content separately.
            **kwargs: Optional tokenizer settings used when creating inputs (e.g., truncation).

        Returns:
            str or dict: The decoded generated text, or a dict with 'thinking' and 'content' keys if enable_thinking is True.
        """
        inputs = self._generate_tokens(prompt, **kwargs)
        
        # Extract enable_thinking from model_config if present
        config_copy = model_config.copy()
        thinking_enabled = enable_thinking or config_copy.pop("enable_thinking", False)
        
        if thinking_enabled:
            output_ids = self._generate_text(inputs, enable_thinking=True, **config_copy)
            return self._parse_thinking_content(output_ids)
        
        return self._generate_text(inputs, enable_thinking=False, **config_copy)