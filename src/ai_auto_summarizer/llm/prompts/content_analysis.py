"""Prompt templates for content analysis."""

import json
from pathlib import Path
from typing import Dict, Optional

from .template import PromptTemplate


SYSTEM_PROMPT = """You are an expert content analyzer with deep knowledge across multiple domains.
Your task is to analyze content and provide structured insights that help users understand the key points, topics, and overall context.
Focus on extracting meaningful insights while maintaining accuracy and relevance to the source material."""


CONTENT_STRUCTURE = """Please provide a detailed analysis with:

1. A concise summary capturing the main points and key insights
2. A list of key takeaways or important points
3. High-level categories that this content belongs to (e.g., Technology, Science, Business, etc.)
4. Detailed topics discussed, where for each topic provide:
   - The topic name
   - A description explaining how this topic relates to the content
5. The overall sentiment or tone of the content (if relevant)

Ensure each topic description is specific to how the topic appears in this content."""


# Load the prompt template
_template = PromptTemplate.load('templates/content_analysis.prompt')

def _load_categories() -> Dict[str, str]:
    """Load categories from settings.json."""
    settings_path = Path(__file__).parent.parent.parent / 'settings.json'
    if not settings_path.exists():
        return {}
        
    with open(settings_path) as f:
        settings = json.load(f)
        return settings.get('categories', {})

def _format_categories(categories: Dict[str, str]) -> str:
    """Format categories into a readable list with descriptions."""
    if not categories:
        return "Warning: No categories defined in settings.json"
        
    lines = []
    for name, description in categories.items():
        lines.append(f"- {name}: {description}")
    return "\n".join(lines)

def create_content_analysis_prompt(
    transcript: str,
    title: Optional[str] = None,
    description: Optional[str] = None
) -> str:
    """
    Create a prompt for content analysis.
    
    Args:
        transcript: The main content to analyze
        title: Optional title of the content
        description: Optional description or context
        
    Returns:
        Formatted prompt string
    """
    # Load and format categories
    categories = _load_categories()
    formatted_categories = _format_categories(categories)
    
    # Build metadata section
    metadata_parts = []
    if title:
        metadata_parts.append(f"Title: {title}")
    if description:
        metadata_parts.append(f"Description: {description}")
    metadata = "\n".join(metadata_parts) if metadata_parts else "No additional metadata provided."
    
    # Render the template
    return _template.render(
        transcript=transcript,
        metadata=metadata,
        categories=formatted_categories
    )


# Export the main prompt creation function
CONTENT_ANALYSIS_PROMPT = create_content_analysis_prompt 