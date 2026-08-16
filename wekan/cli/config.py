"""Configuration management for WeKan CLI."""

import os
from pathlib import Path
from typing import Optional

try:
    from pydantic import BaseModel, ConfigDict, Field, field_validator
except ImportError as e:
    raise ImportError(
        "CLI dependencies not installed. Install with: pip install python-wekan[cli]"
    ) from e


class WekanConfig(BaseModel):
    """WeKan CLI configuration model."""

    base_url: Optional[str] = Field(default="http://localhost:3000", description="WeKan server URL")
    username: Optional[str] = Field(default=None, description="WeKan username")
    password: Optional[str] = Field(default=None, description="WeKan password")
    token: Optional[str] = Field(default=None, description="WeKan API token")
    timeout: int = Field(default=30000, description="Request timeout in milliseconds")

    model_config = ConfigDict(env_prefix="WEKAN_")

    @field_validator("base_url")
    @classmethod
    def validate_base_url(cls, v) -> str:
        """Validate and normalize base URL."""
        if v and v.endswith("/"):
            v = v.rstrip("/")
        if v == "":
            raise ValueError("WEKAN_BASE_URL is required")
        return v


def find_config_file() -> Optional[Path]:
    """Find WeKan configuration file."""
    # Check current directory
    current_dir_config = Path(".wekan")
    if current_dir_config.exists():
        return current_dir_config

    # Check home directory
    home_dir_config = Path.home() / ".wekan"
    if home_dir_config.exists():
        return home_dir_config

    return None


def load_config(config_file: Optional[Path] = None) -> WekanConfig:
    """Load WeKan configuration."""
    if config_file is None:
        config_file = find_config_file()

    # Load from environment variables first
    env_config = {}
    for key in ["BASE_URL", "USERNAME", "PASSWORD", "TOKEN", "TIMEOUT"]:
        env_key = f"WEKAN_{key}"
        if env_key in os.environ:
            env_config[key.lower()] = os.environ[env_key]

    # Load from config file if it exists
    file_config = {}
    if config_file and config_file.exists():
        with open(config_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip().replace("WEKAN_", "").lower()
                    value = value.strip().strip("\"'")
                    file_config[key] = value

    # Environment variables take precedence over file config
    config_data = {**file_config, **env_config}

    return WekanConfig(**config_data)


def save_config(config: WekanConfig, config_file: Optional[Path] = None) -> None:
    """Save WeKan configuration to file."""
    if config_file is None:
        config_file = Path(".wekan")

    with open(config_file, "w") as f:
        f.write(f"WEKAN_BASE_URL={config.base_url}\n")
        if config.username:
            f.write(f"WEKAN_USERNAME={config.username}\n")
        if config.password:
            f.write(f"WEKAN_PASSWORD={config.password}\n")
        if config.token:
            f.write(f"WEKAN_TOKEN={config.token}\n")
        f.write(f"WEKAN_TIMEOUT={config.timeout}\n")
