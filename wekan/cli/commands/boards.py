"""
Board management commands for WeKan CLI.
"""

import sys
from typing import Optional

try:
    import typer
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
except ImportError:
    print("CLI dependencies not installed. Install with: pip install python-wekan[cli]")
    sys.exit(1)

from wekan.board import Board
from wekan.wekan_client import WekanClient

from ..config import load_config

app = typer.Typer(help="Board management commands")
console = Console()


@app.callback(invoke_without_command=True)
def boards_main(ctx: typer.Context) -> None:
    """Board management commands. Run 'wekan boards --help' for available commands."""
    if ctx.invoked_subcommand is None:
        console.print("  Board management commands available:")
        console.print("  • [bold]wekan boards list[/bold] - List all boards")
        console.print("  • [bold]wekan boards show <id>[/bold] - Show board details")
        console.print(
            "  • [bold]wekan boards activate <id>[/bold] - Enter interactive board context"
        )
        console.print("  • [bold]wekan boards create <title>[/bold] - Create new board")
        console.print("\n Use 'wekan boards --help' for detailed help")


def get_client() -> WekanClient:
    """Get authenticated WeKan client."""
    config = load_config()

    if not config.base_url or not config.username or not config.password:
        console.print(" Not configured. Run 'wekan config init' to set up.")
        raise typer.Exit(1)

    try:
        return WekanClient(
            base_url=config.base_url, username=config.username, password=config.password
        )
    except Exception as e:
        console.print(f" Failed to connect: {str(e)}")
        raise typer.Exit(1)


def find_board(client: WekanClient, identifier: str) -> Optional[Board]:
    """Find board by ID prefix, name, or local index."""
    try:
        boards = client.list_boards()

        if not boards:
            console.print(" No boards found.")
            return None

        # Try to match by local index (1-based)
        if identifier.isdigit():
            index = int(identifier) - 1  # Convert to 0-based
            if 0 <= index < len(boards):
                return boards[index]

        # Try to match by ID prefix
        id_matches = [b for b in boards if b and hasattr(b, "id") and b.id.startswith(identifier)]
        if len(id_matches) == 1:
            return id_matches[0]
        elif len(id_matches) > 1:
            console.print(f" Multiple boards match ID prefix '{identifier}':")
            for i, board in enumerate(id_matches, 1):
                if board and hasattr(board, "id") and hasattr(board, "title"):
                    console.print(f"  {i}. {board.id[:12]}... - {board.title}")
            return None

        # Try to match by name (case-insensitive)
        name_matches = [
            b for b in boards if b and hasattr(b, "title") and identifier.lower() in b.title.lower()
        ]
        if len(name_matches) == 1:
            return name_matches[0]
        elif len(name_matches) > 1:
            console.print(f" Multiple boards match name '{identifier}':")
            for i, board in enumerate(name_matches, 1):
                if board and hasattr(board, "title") and hasattr(board, "id"):
                    console.print(f"  {i}. {board.title} ({board.id[:8]}...)")
            return None

        console.print(f" No board found matching '{identifier}'")
        console.print(" You can use:")
        console.print("  • Local index (e.g., '1', '2', '3')")
        console.print("  • ID prefix (e.g., 'koHF', 'c9GQ')")
        console.print("  • Part of board name (e.g., 'Templates', 'AI')")
        return None

    except Exception as e:
        console.print(f" Error finding board: {str(e)}")
        return None


@app.command("list")
def list_boards() -> None:
    """List all accessible boards."""
    client = get_client()

    try:
        boards = client.list_boards()

        if not boards:
            console.print(" No boards found.")
            return

        table = Table(title="WeKan Boards")
        table.add_column("#", style="bold yellow", width=3)
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Title", style="magenta")
        table.add_column("Description", style="green")
        table.add_column("Created", style="blue")

        for i, board in enumerate(boards, 1):
            table.add_row(
                str(i),
                board.id[:8] + "...",  # Show short ID
                board.title,
                getattr(board, "description", "") or "No description",
                str(getattr(board, "created_at", "Unknown")),
            )

        console.print(table)
        console.print(
            "\n Use board [bold]index (#)[/bold], [bold]ID prefix[/bold],",
            " or [bold]name[/bold] with other commands",
        )

    except Exception as e:
        console.print(f" Error listing boards: {str(e)}")
        raise typer.Exit(1)


@app.command()
def show(identifier: str) -> None:
    """Show detailed information about a board. Use index (#), ID prefix, or name."""
    client = get_client()

    try:
        board = find_board(client, identifier)
        if not board:
            raise typer.Exit(1)

        # Get board details - check if methods exist first
        try:
            lists = board.get_lists() if hasattr(board, "get_lists") else []
        except Exception:
            lists = []

        try:
            swimlanes = board.list_swimlanes() if hasattr(board, "list_swimlanes") else []
        except Exception:
            swimlanes = []

        panel_content = []
        panel_content.append(f" ID: {board.id}")
        panel_content.append(f" Title: {board.title}")
        panel_content.append(f" Description: {getattr(board, 'description', 'No description')}")
        panel_content.append(f" Lists: {len(lists)}")
        panel_content.append(f" Swimlanes: {len(swimlanes)}")
        panel_content.append(f" Created: {getattr(board, 'created_at', 'Unknown')}")

        console.print(
            Panel.fit(
                "\n".join(panel_content),
                title=f"Board: {board.title}",
                border_style="blue",
            )
        )

        # Show lists if available
        if lists:
            console.print("\n Lists:")
            list_table = Table()
            list_table.add_column("#", style="bold yellow", width=3)
            list_table.add_column("ID", style="cyan", no_wrap=True)
            list_table.add_column("Title", style="magenta")

            for i, lst in enumerate(lists, 1):
                try:
                    cards = lst.get_cards() if hasattr(lst, "get_cards") else []
                    card_count = len(cards)
                except Exception:
                    card_count = "?"

                list_table.add_row(str(i), lst.id[:8] + "...", f"{lst.title} ({card_count} cards)")

            console.print(list_table)

    except Exception as e:
        console.print(f" Error showing board: {str(e)}")
        raise typer.Exit(1)


@app.command()
def activate(identifier: str) -> None:
    """Activate board context for interactive work. Use index (#), ID prefix, or name."""
    from ..board_context import activate_board

    activate_board(identifier)


@app.command()
def create(
    title: str,
    description: Optional[str] = typer.Option(
        None, "--description", "-d", help="Board description"
    ),
    color: str = typer.Option("midnight", "--color", "-c", help="Board color"),
    is_admin: bool = typer.Option(True, "--admin/--no-admin", help="Admin permissions"),
    is_no_comments: bool = typer.Option(False, "--no-comments", help="Disable comments"),
    is_comment_only: bool = typer.Option(False, "--comment-only", help="Comment only mode"),
) -> None:
    """Create a new board."""
    client = get_client()

    try:
        board = client.add_board(
            title=title,
            color=color,
            is_admin=is_admin,
            is_no_comments=is_no_comments,
            is_comment_only=is_comment_only,
        )

        console.print(
            Panel.fit(
                f" Board created successfully\n"
                f" ID: {board.id}\n"
                f" Title: {board.title}\n"
                f" Color: {color}\n"
                f" Created: {board.created_at}",
                title="Board Created",
                border_style="green",
            )
        )

    except Exception as e:
        console.print(f" Error creating board: {str(e)}")
        raise typer.Exit(1)
