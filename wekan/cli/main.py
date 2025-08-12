"""Main CLI application entry point."""

import sys

try:
    import typer
    from rich.console import Console
    from rich.panel import Panel
except ImportError as e:
    raise ImportError(
        "CLI dependencies not installed. Install with: pip install python-wekan[cli]"
    ) from e

from wekan.wekan_client import WekanClient

from .commands import auth, boards, config
from .config import load_config

app = typer.Typer(
    name="wekan",
    help="WeKan CLI - Command line interface for WeKan kanban boards",
    add_completion=False,
    pretty_exceptions_enable=False,
)

console = Console()

# Add command groups
app.add_typer(auth.app, name="auth", help="Authentication commands")
app.add_typer(boards.app, name="boards", help="Board management commands")
app.add_typer(config.app, name="config", help="Configuration management commands")


@app.callback(invoke_without_command=True)  # type: ignore[misc]
def main_callback(ctx: typer.Context) -> None:
    """Wekan CLI - Command line interface for Wekan kanban boards."""
    if ctx.invoked_subcommand is None:
        console.print()
        console.print(
            "[bold blue]WeKan CLI[/bold blue] - Command line interface for WeKan kanban boards"
        )
        console.print()
        console.print("[bold]Common commands:[/bold]")
        console.print("  • [bold cyan]wekan status[/bold cyan] - Show connection status")
        console.print(
            "  • [bold cyan]wekan navigate[/bold cyan] - Start navigation shell (recommended!)"
        )
        console.print("  • [bold cyan]wekan config init[/bold cyan] - Initialize configuration")
        console.print("  • [bold cyan]wekan boards list[/bold cyan] - List all boards")
        console.print()
        console.print("[bold]Available command groups:[/bold]")
        console.print("  • [bold green]auth[/bold green]    - Authentication commands")
        console.print("  • [bold green]boards[/bold green]  - Board management commands")
        console.print("  • [bold green]config[/bold green]  - Configuration management commands")
        console.print()
        console.print(
            "Use [bold]wekan --help[/bold] for detailed help or ",
            "[bold]wekan <command> --help[/bold] for command-specific help",
        )
        console.print()


@app.command()  # type: ignore[misc]
def status() -> None:
    """Show WeKan connection status."""
    try:
        config = load_config()
        if not config.base_url:
            console.print("No WeKan server configured. Run 'wekan config init' to set up.")
            raise typer.Exit(1)

        if not config.username or not config.password:
            console.print("No credentials configured. Run 'wekan config init' to set up.")
            raise typer.Exit(1)

        # Test connection
        client = WekanClient(
            base_url=config.base_url, username=config.username, password=config.password
        )

        # Try to get user info to verify connection
        try:
            boards = client.list_boards()
            console.print(
                Panel.fit(
                    f"Connected to WeKan server\n"
                    f"Server: {config.base_url}\n"
                    f"User: {config.username}\n"
                    f"Boards: {len(boards)}",
                    title="WeKan Status",
                    border_style="green",
                )
            )
        except Exception as e:
            console.print(
                Panel.fit(
                    f"Failed to connect to WeKan server\n"
                    f"Server: {config.base_url}\n"
                    f"User: {config.username}\n"
                    f"Error: {str(e)}",
                    title="WeKan Status",
                    border_style="red",
                )
            )
            raise typer.Exit(1)

    except Exception as e:
        console.print(f"Error: {str(e)}")
        raise typer.Exit(1)


@app.command()  # type: ignore[misc]
def navigate() -> None:
    """Start interactive navigation shell (filesystem-like cd/ls interface)."""
    from .navigation import start_navigation

    start_navigation()


@app.command()  # type: ignore[misc]
def version() -> None:
    """Show version information."""
    import wekan

    console.print(f"WeKan CLI version: {getattr(wekan, '__version__', 'unknown')}")


def main() -> None:
    """Main entry point for the CLI."""
    try:
        app()
    except NameError:
        # CLI dependencies not available
        print("CLI dependencies not installed. Install with: pip install python-wekan[cli]")
        sys.exit(1)


if __name__ == "__main__":
    main()
