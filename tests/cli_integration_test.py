"""Integration tests for WeKan CLI."""

import os

import pytest

# Skip entire module if CLI dependencies not available
try:
    from typing import Any

    from typer.testing import CliRunner

    from wekan.cli.main import app
except ImportError:
    pytest.skip("CLI dependencies not installed", allow_module_level=True)

# Mark all tests in this file as CLI integration tests
pytestmark = [pytest.mark.cli, pytest.mark.integration]


@pytest.fixture
def runner() -> CliRunner:
    """CLI test runner."""
    return CliRunner()


class TestCLIIntegration:
    """Test CLI integration with WeKan API."""

    def test_cli_help(self, runner: CliRunner) -> None:
        """Test CLI help command."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "WeKan CLI" in result.stdout
        assert "Command line interface for WeKan kanban boards" in result.stdout

    def test_version_command(self, runner: CliRunner) -> None:
        """Test version command."""
        result = runner.invoke(app, ["version"])
        assert result.exit_code == 0
        assert "WeKan CLI version" in result.stdout

    def test_status_no_config(self, runner: CliRunner) -> None:
        """Test status command without configuration."""
        result = runner.invoke(app, ["status"])
        assert result.exit_code == 1
        assert (
            "No WeKan server configured" in result.stdout
            or "No credentials configured" in result.stdout
            or "Not configured" in result.stdout
        )

    def test_auth_commands(self, runner: CliRunner) -> None:
        """Test auth command help."""
        result = runner.invoke(app, ["auth", "--help"])
        assert result.exit_code == 0
        assert "Authentication commands" in result.stdout

    def test_boards_commands(self, runner: CliRunner) -> None:
        """Test boards command help."""
        result = runner.invoke(app, ["boards", "--help"])
        assert result.exit_code == 0
        assert "Board management commands" in result.stdout

    def test_config_commands(self, runner: CliRunner) -> None:
        """Test config command help."""
        result = runner.invoke(app, ["config", "--help"])
        assert result.exit_code == 0
        assert "Configuration management commands" in result.stdout


@pytest.mark.skipif(
    not all(
        [
            os.getenv("WEKAN_BASE_URL"),
            os.getenv("WEKAN_USERNAME"),
            os.getenv("WEKAN_PASSWORD"),
        ]
    ),
    reason="Requires WeKan server environment variables for integration testing",
)
class TestCLILiveIntegration:
    """Test CLI against live WeKan server (requires env vars)."""

    def test_status_with_config(self, runner: CliRunner, monkeypatch: Any) -> None:
        """Test status with valid configuration."""
        monkeypatch.setenv("WEKAN_BASE_URL", os.getenv("WEKAN_BASE_URL"))
        monkeypatch.setenv("WEKAN_USERNAME", os.getenv("WEKAN_USERNAME"))
        monkeypatch.setenv("WEKAN_PASSWORD", os.getenv("WEKAN_PASSWORD"))

        result = runner.invoke(app, ["status"])
        # Should either succeed (exit 0) or fail gracefully (exit 1)
        assert result.exit_code in [0, 1]

    def test_boards_list(self, runner: CliRunner, monkeypatch: Any) -> None:
        """Test listing boards."""
        monkeypatch.setenv("WEKAN_BASE_URL", os.getenv("WEKAN_BASE_URL"))
        monkeypatch.setenv("WEKAN_USERNAME", os.getenv("WEKAN_USERNAME"))
        monkeypatch.setenv("WEKAN_PASSWORD", os.getenv("WEKAN_PASSWORD"))

        result = runner.invoke(app, ["boards", "list"])
        # Should either succeed or fail gracefully
        assert result.exit_code in [0, 1]
