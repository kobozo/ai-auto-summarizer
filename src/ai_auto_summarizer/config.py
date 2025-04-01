"""Application configuration using Pydantic models."""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Main application configuration loaded from environment variables."""

    the_var: str = Field(..., alias="THE_VAR")

    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
    }


# Create a single instance of the settings
settings = Settings()
