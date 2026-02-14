"""Configuration management for TruthGuards."""

import os
from functools import lru_cache
from pathlib import Path

import yaml
from pydantic import BaseModel
from pydantic_settings import BaseSettings


class WeaviateConfig(BaseModel):
    """Weaviate connection configuration."""

    host: str = "localhost"
    port: int = 8080
    grpc_port: int = 50051


class ApiConfig(BaseModel):
    """API server configuration."""

    host: str = "0.0.0.0"
    port: int = 8000


class StreamlitConfig(BaseModel):
    """Streamlit configuration."""

    port: int = 8501


class SearchConfig(BaseModel):
    """Hybrid search configuration."""

    default_limit: int = 5
    alpha: float = 0.5


class Settings(BaseSettings):
    """Application settings loaded from YAML config and environment variables."""

    models: list[str] = []
    weaviate: WeaviateConfig = WeaviateConfig()
    api: ApiConfig = ApiConfig()
    streamlit: StreamlitConfig = StreamlitConfig()
    search: SearchConfig = SearchConfig()

    class Config:
        env_prefix = "TRUTHGUARDS_"


def find_config_file() -> Path | None:
    """Find the config file in common locations."""
    search_paths = [
        Path("config/config.yaml"),
        Path("config.yaml"),
        Path("/app/config/config.yaml"),
        Path.home() / ".truthguards" / "config.yaml",
    ]

    for path in search_paths:
        if path.exists():
            return path

    return None


def load_config_from_yaml(config_path: Path | None = None) -> dict:
    """Load configuration from YAML file."""
    if config_path is None:
        config_path = find_config_file()

    if config_path is None or not config_path.exists():
        return {}

    with open(config_path) as f:
        return yaml.safe_load(f) or {}


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings."""
    config_path_env = os.environ.get("TRUTHGUARDS_CONFIG_PATH")
    config_path = Path(config_path_env) if config_path_env else None

    yaml_config = load_config_from_yaml(config_path)
    return Settings(**yaml_config)
