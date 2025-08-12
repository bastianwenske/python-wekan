"""
Authentication commands for WeKan CLI.
"""

import sys
from typing import Optional

try:
    import typer
    from rich.console import Console
    from rich.panel import Panel
    from rich.prompt import Prompt
except ImportError:
    print("CLI dependencies not installed. Install with: pip install python-wekan[cli]")
    sys.exit(1)

from wekan.wekan_client import WekanClient

from ..config import load_config

app = typer.Typer(help="Authentication commands")
console = Console()


@app.callback(invoke_without_command=True)
def auth_main(ctx: typer.Context) -> None:
    """Authentication commands. Run 'wekan auth --help' for available commands."""
    if ctx.invoked_subcommand is None:
        console.print("  Authentication commands available:")
        console.print("  • [bold]wekan auth login[/bold] - Login to WeKan server")
        console.print("  • [bold]wekan auth whoami[/bold] - Show current user")
        console.print("  • [bold]wekan auth logout[/bold] - Logout information")
        console.print("\n Use 'wekan auth --help' for detailed help")


@app.command()
def login(
    username: Optional[str] = typer.Option(None, "--username", "-u", help="WeKan username"),
    password: Optional[str] = typer.Option(None, "--password", "-p", help="WeKan password"),
    server: Optional[str] = typer.Option(None, "--server", "-s", help="WeKan server URL"),
) -> None:
    """Login to WeKan server."""
    config = load_config()

    # Use provided values or fall back to config
    base_url = server or config.base_url
    user = username or config.username
    pwd = password or config.password

    if not base_url:
        base_url = Prompt.ask("WeKan server URL")

    if not user:
        user = Prompt.ask("Username")

    if not pwd:
        pwd = Prompt.ask("Password", password=True)

    # Ensure all values are strings
    if not base_url or not user or not pwd:
        console.print(" All configuration values are required.")
        raise typer.Exit(1)

    try:
        if not base_url or not user or not pwd:
            console.print(" All configuration values are required.")
            raise typer.Exit(1)

        client = WekanClient(base_url=str(base_url), username=str(user), password=str(pwd))
        boards = client.list_boards()  # Test connection

        console.print(
            Panel.fit(
                f" Successfully logged in to WeKan\n"
                f" Server: {base_url}\n"
                f" User: {user}\n"
                f" Boards: {len(boards)}",
                title="Login Successful",
                border_style="green",
            )
        )

    except Exception as e:
        console.print(
            Panel.fit(
                f" Login failed\n Error: {str(e)}",
                title="Login Error",
                border_style="red",
            )
        )
        raise typer.Exit(1)


@app.command()
def whoami() -> None:
    """Show current user information."""
    config = load_config()

    if not config.base_url or not config.username:
        console.print(" Not logged in. Run 'wekan auth login' first.")
        raise typer.Exit(1)

    try:
        if not config.base_url or not config.username or not config.password:
            console.print(" Not logged in. Run 'wekan auth login' first.")
            raise typer.Exit(1)

        WekanClient(
            base_url=str(config.base_url),
            username=str(config.username),
            password=str(config.password),
        )

        console.print(
            Panel.fit(
                f" User: {config.username}\n Server: {config.base_url}\n Connected: ",
                title="Current User",
                border_style="blue",
            )
        )

    except Exception as e:
        console.print(f" Error checking user info: {str(e)}")
        raise typer.Exit(1)


@app.command()
def logout() -> None:
    """Logout from WeKan (clears stored credentials)."""
    console.print("  WeKan CLI uses configuration files for authentication.")
    console.print("To 'logout', remove or modify your .wekan configuration file.")
    console.print(" Configuration locations:")
    console.print("   • Current directory: ./.wekan")
    console.print("   • Home directory: ~/.wekan")
