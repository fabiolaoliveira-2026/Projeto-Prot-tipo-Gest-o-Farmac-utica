

"""Prompt template utilities for building model-ready prompts across supported formats.

This module provides simple helpers to compose prompts for different chat or instruction templates.
"""

class PromptGenerator:
    """Factory for building prompts using a selectable template.

    The generator composes prompts for supported formats such as LLaMA-style chat and Unsloth-style
    instruction templates.

    Args:
        prompt_type (str): Template key used to select the prompt format (e.g., "llama", "unsloth").
    """
    def __init__(self, prompt_type: str = "llama"):
        self.prompt_type = prompt_type


    @staticmethod
    def _llama_generate(user, system=""):
        prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>

            {system}<|eot_id|>
            <|start_header_id|>user<|end_header_id|>

            {user}<|eot_id|>
            <|start_header_id|>assistant<|end_header_id|>"""
        return prompt

    @staticmethod
    def _unsloth_generate(user, system=""):
        prompt = f"{system}.\n\n### Input:\n{user}\n\n### Response:\n"
        return prompt

    def generate(self, user, system=""):
        """Generate a prompt according to the configured template type.

        Args:
            user (str): User input text.
            system (str): Optional system instruction.

        Returns:
            str: The composed prompt text.

        Raises:
            Exception: If the selected prompt_type is not supported.
        """
        if self.prompt_type == "llama":
            return self._llama_generate(user, system)
        elif self.prompt_type == "unsloth":
            return self._unsloth_generate(user, system)
        else:
            raise Exception(f"Prompt type {self.prompt_type} is not supported.")