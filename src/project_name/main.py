"""Flask application endpoints for Supernova 2025 R2I API."""

from __future__ import annotations

from project_name.config import settings


def demo_function() -> str:
    """Demo function that returns the_var from settings."""
    return settings.the_var

