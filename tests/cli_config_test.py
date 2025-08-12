"""Unit tests for CLI configuration management."""

import tempfile
from pathlib import Path

import pytest

# Skip entire module if CLI dependencies not available
try:
    from wekan.cli.config import WekanConfig, load_config
except ImportError:
    pytest.skip("CLI dependencies not installed", allow_module_level=True)

# Mark all tests in this file as CLI unit tests
pytestmark = [pytest.mark.cli, pytest.mark.unit]


class TestWekanConfig:
    """Test WekanConfig model."""

    def test_default_config(self):
        """Test default configuration values."""
        config = WekanConfig()
        assert config.base_url == "http://localhost:3000"
        assert config.username is None
        assert config.password is None
        assert config.token is None
        assert config.timeout == 30000

    def test_config_with_values(self):
        """Test configuration with provided values."""
        config = WekanConfig(
            base_url="https://wekan.example.com",
            username="testuser",
            password="testpass",  # pragma: allowlist secret
            timeout=60000,
        )
        assert config.base_url == "https://wekan.example.com"
        assert config.username == "testuser"
        assert config.password == "testpass"
        assert config.timeout == 60000

    def test_base_url_validation(self):
        """Test base URL validation."""
        # Should strip trailing slash
        config = WekanConfig(base_url="https://wekan.example.com/")
        assert config.base_url == "https://wekan.example.com"

        # Should raise error for empty URL
        with pytest.raises(ValueError, match="WEKAN_BASE_URL is required"):
            WekanConfig(base_url="")


class TestLoadConfig:
    """Test config loading functionality."""

    def test_load_config_from_file(self):
        """Test loading configuration from file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
            f.write("WEKAN_BASE_URL=https://test.wekan.com\n")
            f.write("WEKAN_USERNAME=testuser\n")
            f.write("WEKAN_PASSWORD=testpass\n")
            f.write("WEKAN_TIMEOUT=45000\n")
            temp_file = Path(f.name)

        try:
            config = load_config(temp_file)
            assert config.base_url == "https://test.wekan.com"
            assert config.username == "testuser"
            assert config.password == "testpass"
            assert config.timeout == 45000
        finally:
            temp_file.unlink()

    def test_load_config_no_file(self):
        """Test loading configuration when no file exists."""
        # Should use defaults
        config = load_config(Path("/nonexistent/file"))
        assert config.base_url == "http://localhost:3000"
        assert config.username is None

    def test_load_config_env_variables(self, monkeypatch):
        """Test loading configuration from environment variables."""
        monkeypatch.setenv("WEKAN_BASE_URL", "https://env.wekan.com")
        monkeypatch.setenv("WEKAN_USERNAME", "envuser")
        monkeypatch.setenv("WEKAN_PASSWORD", "envpass")
        monkeypatch.setenv("WEKAN_TIMEOUT", "75000")

        config = load_config()
        assert config.base_url == "https://env.wekan.com"
        assert config.username == "envuser"
        assert config.password == "envpass"
        assert config.timeout == 75000
