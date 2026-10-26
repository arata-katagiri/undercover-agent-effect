import os
from typing import Dict, Optional

class PromptLoader:
    """Utility class for loading prompt templates from files"""
    
    @staticmethod
    def load_prompt(prompt_path: str, replacements: Optional[Dict[str, str]] = None) -> str:
        """
        Load a prompt template from a file and optionally replace placeholders
        
        Args:
            prompt_path: Path to the prompt file relative to project root
            replacements: Dictionary of placeholder replacements (e.g., {'{player_name}': 'Alice'})
            
        Returns:
            The loaded and formatted prompt string
        """
        # Get the project root directory (two levels up from src/utils)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(current_dir, '../..'))
        
        # Construct full path
        full_path = os.path.join(project_root, prompt_path)
        
        # Check if file exists
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"Prompt file not found: {full_path}")
        
        # Load the prompt
        with open(full_path, 'r', encoding='utf-8') as f:
            prompt = f.read()
        
        # Apply replacements if provided
        if replacements:
            for placeholder, value in replacements.items():
                prompt = prompt.replace(placeholder, value)
        
        return prompt
    
    @staticmethod
    def load_secret_channel_prompts() -> Dict[str, str]:
        """
        Load all secret channel prompt templates
        
        Returns:
            Dictionary with prompt names as keys and prompt templates as values
        """
        prompts = {}
        prompt_files = {
            'tool_offer': 'prompts/secret_channel/tool_offer_prompt.txt',
            'partner_notification': 'prompts/secret_channel/partner_notification_prompt.txt',
            'secret_communication': 'prompts/secret_channel/secret_communication_prompt.txt'
        }
        
        for name, path in prompt_files.items():
            try:
                prompts[name] = PromptLoader.load_prompt(path)
            except FileNotFoundError as e:
                print(f"Warning: Could not load {name} prompt: {e}")
                prompts[name] = None
        
        return prompts

    @staticmethod
    def load_secret_hint_prompts() -> Dict[str, str]:
        """
        Load all secret hint prompt templates

        Returns:
            Dictionary with prompt names as keys and prompt templates as values
        """
        prompts = {}
        prompt_files = {
            'tool_offer': 'prompts/secret_hint/tool_offer_prompt.txt',
            'partner_notification': 'prompts/secret_hint/partner_notification_prompt.txt',
            'strategy_hint': 'prompts/secret_hint/strategy_hint_prompt.txt'
        }

        for name, path in prompt_files.items():
            try:
                prompts[name] = PromptLoader.load_prompt(path)
            except FileNotFoundError as e:
                print(f"Warning: Could not load {name} prompt: {e}")
                prompts[name] = None

        return prompts