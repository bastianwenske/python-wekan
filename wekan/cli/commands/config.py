"""Configuration management commands for WeKan CLI."""

import sys
from pathlib import Path
from typing import Optional

try:
    import typer
    from rich.console import Console
    from rich.panel import Panel
    from rich.prompt import Confirm, Prompt
except ImportError:
    print("CLI dependencies not installed. Install with: pip install python-wekan[cli]")
    sys.exit(1)

from ..config import WekanConfig, find_config_file, load_config, save_config

app = typer.Typer(help="Configuration management commands")
console = Console()


@app.command()
def init(
    server: Optional[str] = typer.Argument(None, help="WeKan server URL"),
    username: Optional[str] = typer.Argument(None, help="WeKan username"),
    password: Optional[str] = typer.Argument(None, help="WeKan password"),
    config_file: Optional[str] = typer.Option(None, "--file", "-f", help="Config file path"),
) -> None:
    """Initialize WeKan CLI configuration."""
    # Check if config already exists
    existing_config_file = find_config_file()
    if existing_config_file and not config_file:
        overwrite = Confirm.ask(
            f"Configuration already exists at {existing_config_file}. Overwrite?"
        )
        if not overwrite:
            console.print(" Configuration initialization cancelled.")
            return

    # Get configuration values
    if not server:
        server = Prompt.ask("WeKan server URL", default="http://localhost:3000")

    if not username:
        username = Prompt.ask("Username")

    if not password:
        password = Prompt.ask("Password", password=True)

    # Ensure all values are strings
    if not server or not username or not password:
        console.print(" All configuration values are required.")
        raise typer.Exit(1)

    # Create config
    config = WekanConfig(base_url=server, username=username, password=password)

    # Determine config file path
    config_path = Path(config_file) if config_file else Path(".wekan")

    try:
        # Test the configuration
        from wekan.wekan_client import WekanClient

        if not config.base_url or not config.username or not config.password:
            console.print(" All configuration values are required.")
            raise typer.Exit(1)

        client = WekanClient(
            base_url=str(config.base_url),
            username=str(config.username),
            password=str(config.password),
        )
        boards = client.list_boards()  # Test connection

        # Save configuration
        save_config(config, config_path)

        console.print(
            Panel.fit(
                f" Configuration saved successfully\n"
                f" File: {config_path.absolute()}\n"
                f" Server: {config.base_url}\n"
                f" User: {config.username}\n"
                f" Boards found: {len(boards)}",
                title="Configuration Initialized",
                border_style="green",
            )
        )

    except Exception as e:
        console.print(
            Panel.fit(
                f" Configuration test failed\n"
                f" Error: {str(e)}\n"
                f" The configuration will still be saved, but connection failed.",
                title="Configuration Warning",
                border_style="yellow",
            )
        )

        save_anyway = Confirm.ask("Save configuration anyway?")
        if save_anyway:
            save_config(config, config_path)
            console.print(f" Configuration saved to {config_path.absolute()}")
        else:
            console.print(" Configuration not saved.")


@app.command()
def show() -> None:
    """Show current configuration."""
    config = load_config()
    config_file = find_config_file()

    panel_content = []
    panel_content.append(f" Config file: {config_file or 'Not found (using defaults/env vars)'}")
    panel_content.append(f" Server: {config.base_url or 'Not configured'}")
    panel_content.append(f" Username: {config.username or 'Not configured'}")
    panel_content.append(f" Password: {'***' if config.password else 'Not configured'}")
    panel_content.append(f" Timeout: {config.timeout}ms")

    console.print(
        Panel.fit(
            "\n".join(panel_content),
            title="WeKan CLI Configuration",
            border_style="blue",
        )
    )


@app.command()
def set(
    server: Optional[str] = typer.Option(None, "--server", "-s", help="WeKan server URL"),
    username: Optional[str] = typer.Option(None, "--username", "-u", help="WeKan username"),
    password: Optional[str] = typer.Option(None, "--password", "-p", help="WeKan password"),
    timeout: Optional[int] = typer.Option(None, "--timeout", "-t", help="Request timeout (ms)"),
    config_file: Optional[str] = typer.Option(None, "--file", "-f", help="Config file path"),
) -> None:
    """Set configuration values."""
    # Load existing config
    config = load_config()

    # Update provided values
    updated = False
    if server is not None:
        config.base_url = server
        updated = True

    if username is not None:
        config.username = username
        updated = True

    if password is not None:
        config.password = password
        updated = True

    if timeout is not None:
        config.timeout = timeout
        updated = True

    if not updated:
        console.print(" No configuration values provided to update.")
        console.print(" Use --server, --username, --password, or --timeout options.")
        return

    # Determine config file path
    config_path = Path(config_file) if config_file else (find_config_file() or Path(".wekan"))

    try:
        save_config(config, config_path)
        console.print(
            Panel.fit(
                f" Configuration updated successfully\n File: {config_path.absolute()}",
                title="Configuration Updated",
                border_style="green",
            )
        )

    except Exception as e:
        console.print(f" Error saving configuration: {str(e)}")
        raise typer.Exit(1)
