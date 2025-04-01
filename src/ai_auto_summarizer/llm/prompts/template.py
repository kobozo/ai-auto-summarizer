"""Template manager for prompt files."""

import os
from pathlib import Path
from string import Template
from typing import Any, Dict


class PromptTemplate:
    """Manages loading and rendering of .prompt template files."""

    def __init__(self, template_path: str):
        """
        Initialize prompt template from a .prompt file.
        
        Args:
            template_path: Path to the .prompt file, relative to the prompts directory
        """
        self.template_path = Path(__file__).parent / template_path
        if not self.template_path.exists():
            raise FileNotFoundError(f"Prompt template not found: {template_path}")
            
        with open(self.template_path, 'r') as f:
            self.template = Template(f.read())
            
    def render(self, **kwargs: Any) -> str:
        """
        Render the prompt template with the provided variables.
        
        Args:
            **kwargs: Variables to substitute in the template
            
        Returns:
            Rendered prompt string
        """
        try:
            return self.template.safe_substitute(**kwargs)
        except KeyError as e:
            raise ValueError(f"Missing required template variable: {e}")
            
    @classmethod
    def load(cls, template_path: str) -> 'PromptTemplate':
        """
        Load a prompt template from a .prompt file.
        
        Args:
            template_path: Path to the .prompt file, relative to the prompts directory
            
        Returns:
            PromptTemplate instance
        """
        return cls(template_path) 