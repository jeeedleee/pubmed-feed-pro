"""Configuration management for PubMed Papers Feed."""

import os
from pathlib import Path
from typing import List, Optional

import yaml
from pydantic import BaseModel, Field


class LLMConfig(BaseModel):
    """LLM configuration."""

    base_url: str = Field(default="https://api.openai.com/v1")
    api_key: str = Field(default="")
    model: str = Field(default="gpt-4")


class PubMedConfig(BaseModel):
    """PubMed search configuration."""

    search_days: int = Field(default=7, ge=1, le=365)
    max_results: int = Field(default=100, ge=1, le=100)
    schedule: Optional[str] = Field(default=None)


class TemplatesConfig(BaseModel):
    """Content templates configuration."""

    xiaohongshu_long: str = Field(default="")
    xiaohongshu_short: str = Field(default="")
    wechat_long: str = Field(default="")
    wechat_short: str = Field(default="")


class AppConfig(BaseModel):
    """Application configuration."""

    llm: LLMConfig = Field(default_factory=LLMConfig)
    pubmed: PubMedConfig = Field(default_factory=PubMedConfig)
    interests: List[str] = Field(default_factory=list)
    templates: TemplatesConfig = Field(default_factory=TemplatesConfig)


class ConfigManager:
    """Manage application configuration."""

    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = Path(config_path)
        self._config: Optional[AppConfig] = None

    def load(self) -> AppConfig:
        """Load configuration from file."""
        if not self.config_path.exists():
            # Create default config from example
            example_path = Path("config.yaml.example")
            if example_path.exists():
                config_data = yaml.safe_load(example_path.read_text(encoding="utf-8"))
            else:
                config_data = {}
        else:
            config_data = yaml.safe_load(self.config_path.read_text(encoding="utf-8"))

        self._config = AppConfig(**config_data)
        return self._config

    def save(self, config: AppConfig) -> None:
        """Save configuration to file."""
        config_dict = config.model_dump()
        with open(self.config_path, "w", encoding="utf-8") as f:
            yaml.dump(config_dict, f, allow_unicode=True, sort_keys=False)
        self._config = config

    def get_config(self) -> AppConfig:
        """Get current configuration, loading if necessary."""
        if self._config is None:
            return self.load()
        return self._config


# Global config manager instance
config_manager = ConfigManager()


def get_config() -> AppConfig:
    """Get application configuration."""
    return config_manager.get_config()
