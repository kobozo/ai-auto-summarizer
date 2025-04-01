"""Pydantic models for content summaries."""

from typing import Optional
from pydantic import BaseModel, Field


class Topic(BaseModel):
    """Model representing a topic with its description."""
    
    name: str = Field(
        description="Name of the topic"
    )
    description: str = Field(
        description="AI-generated description explaining how this topic relates to the content"
    )
    categories: list[str] = Field(
        default_factory=list,
        description="High-level categories that the content belongs to (e.g., 'Technology', 'Science', 'Business')"
    )


class ContentSummary(BaseModel):
    """Model representing a summary of content."""
    
    summary: str = Field(
        description="A concise summary of the content that captures the main points and key insights"
    )
    key_points: list[str] = Field(
        default_factory=list,
        description="List of key points or takeaways from the content"
    )
    topics: list[Topic] = Field(
        default_factory=list,
        description="Detailed topics discussed in the content, each with an AI-generated description"
    )