"""
Interactive board context for WeKan CLI.
"""

import sys

try:
    from rich.columns import Columns
    from rich.console import Console
    from rich.panel import Panel
    from rich.prompt import Prompt
    from rich.table import Table
except ImportError:
    print("CLI dependencies not installed. Install with: pip install python-wekan[cli]")
    sys.exit(1)

from wekan.wekan_client import WekanClient

from .commands.boards import find_board
from .config import load_config


class BoardContext:
    """Interactive board context for focused work."""

    def __init__(self, client: WekanClient, board) -> None:
        self.client = client
        self.board = board
        self.console = Console()
        self.lists: list = []
        self.cards: list = []

    def show_board(self) -> None:
        """Display the complete KANBAN board layout."""
        try:
            # Get board data
            lists = []
            try:
                lists = self.board.get_lists() if hasattr(self.board, "get_lists") else []
            except Exception as e:
                self.console.print(f"[yellow]  Could not load board lists: {str(e)}[/yellow]")
                lists = []

            if not lists:
                self.console.print()
                self.console.print(
                    Panel.fit(
                        "[yellow] This board has no lists yet.[/yellow]\n"
                        " Create lists with: [bold]list create <name>[/bold]\n"
                        ' Try: [bold cyan]list create "To Do"[/bold cyan]',
                        title="Empty Board",
                        border_style="yellow",
                    )
                )
                return

            # Create KANBAN visualization
            columns_data = []

            for i, lst in enumerate(lists, 1):
                # Get cards for this list
                cards = []
                try:
                    cards = lst.get_cards() if hasattr(lst, "get_cards") else []
                except Exception:  # nosec B110
                    # Ignore errors when fetching cards for display
                    pass

                # Create list column

                # Create cards table
                cards_content = []
                if cards:
                    for j, card in enumerate(cards[:10], 1):  # Show max 10 cards
                        card_title = card.title[:30] + "..." if len(card.title) > 30 else card.title
                        cards_content.append(f"[cyan]{j}.[/cyan] {card_title}")

                    if len(cards) > 10:
                        cards_content.append(f"[dim]... and {len(cards) - 10} more[/dim]")
                else:
                    cards_content.append("[dim]No cards[/dim]")

                # Create column panel
                column_content = "\n".join(cards_content)
                column_panel = Panel(
                    column_content,
                    title=f"#{i} {lst.title}",
                    title_align="left",
                    border_style="blue",
                    width=25,
                    height=15,
                )

                columns_data.append(column_panel)

            # Display board header
            board_info = (
                f" [bold blue]{self.board.title}[/bold blue] | "
                f"Lists: {len(lists)} | "
                f"ID: {self.board.id[:8]}..."
            )
            self.console.print(Panel.fit(board_info, title="Active Board", border_style="green"))

            # Display KANBAN columns
            if len(columns_data) <= 4:
                # Show all columns in one row
                self.console.print(Columns(columns_data, equal=True, expand=True))
            else:
                # Split into multiple rows
                for i in range(0, len(columns_data), 4):
                    row_columns = columns_data[i : i + 4]
                    self.console.print(Columns(row_columns, equal=True, expand=True))

        except Exception as e:
            self.console.print(f"[red] Error displaying board: {str(e)}[/red]")

    def run_interactive_session(self) -> None:
        """Run interactive board session."""
        self.console.print(
            "\n [bold green]Entered board context:[/bold green]",
            f"[bold blue]{self.board.title}[/bold blue]",
        )
        self.console.print(
            "Type [bold]help[/bold] for available commands, ",
            "[bold]exit[/bold] to leave board context",
        )

        # Show initial board view
        self.show_board()

        while True:
            try:
                # Custom prompt with board name
                board_name = (
                    self.board.title[:15] + "..."
                    if len(self.board.title) > 15
                    else self.board.title
                )
                prompt_text = f"[bold blue]{board_name}>[/bold blue] "

                command = Prompt.ask(prompt_text).strip()

                if not command:
                    continue

                # Parse command
                parts = command.split()
                cmd = parts[0].lower()
                args = parts[1:] if len(parts) > 1 else []

                # Handle commands
                if cmd in ["exit", "quit", "q"]:
                    self.console.print(" Exiting board context")
                    break

                elif cmd in ["help", "h"]:
                    self.show_help()

                elif cmd in ["show", "view", "board"]:
                    self.show_board()

                elif cmd == "info":
                    self.show_board_info()

                elif cmd == "lists":
                    self.handle_lists_command(args)

                elif cmd == "cards":
                    self.handle_cards_command(args)

                elif cmd == "list":
                    self.handle_list_command(args)

                elif cmd == "card":
                    self.handle_card_command(args)

                else:
                    self.console.print(f"[red] Unknown command: {cmd}[/red]")
                    self.console.print("Type [bold]help[/bold] for available commands")

            except KeyboardInterrupt:
                self.console.print("\n Exiting board context")
                break
            except EOFError:
                self.console.print("\n Exiting board context")
                break
            except Exception as e:
                self.console.print(f"[red] Error: {str(e)}[/red]")

    def show_help(self) -> None:
        """Show available commands in board context."""
        help_table = Table(title="Board Context Commands", show_header=True)
        help_table.add_column("Command", style="cyan", width=20)
        help_table.add_column("Description", style="white")

        commands = [
            ("show, view, board", "Display the KANBAN board layout"),
            ("info", "Show detailed board information"),
            ("lists", "List all board lists"),
            ("list create <name>", "Create a new list"),
            ("list show <id>", "Show list details"),
            ("cards <list-id>", "Show cards in a list"),
            ("card create <list> <title>", "Create a new card"),
            ("card show <list> <card>", "Show card details"),
            ("help, h", "Show this help message"),
            ("exit, quit, q", "Exit board context"),
        ]

        for cmd, desc in commands:
            help_table.add_row(cmd, desc)

        self.console.print(help_table)

    def show_board_info(self) -> None:
        """Show detailed board information."""
        try:
            lists = self.board.get_lists() if hasattr(self.board, "get_lists") else []
            swimlanes = self.board.list_swimlanes() if hasattr(self.board, "list_swimlanes") else []

            # Count total cards
            total_cards = 0
            for lst in lists:
                try:
                    cards = lst.get_cards() if hasattr(lst, "get_cards") else []
                    total_cards += len(cards)
                except Exception:  # nosec B110
                    # Ignore errors when counting cards
                    pass

            info_content = [
                f" ID: {self.board.id}",
                f" Title: {self.board.title}",
                f" Description: {getattr(self.board, 'description', 'No description')}",
                f" Lists: {len(lists)}",
                f" Total Cards: {total_cards}",
                f" Swimlanes: {len(swimlanes)}",
                f" Created: {getattr(self.board, 'created_at', 'Unknown')}",
            ]

            self.console.print(
                Panel.fit(
                    "\n".join(info_content),
                    title="Board Information",
                    border_style="blue",
                )
            )

        except Exception as e:
            self.console.print(f"[red] Error getting board info: {str(e)}[/red]")

    def handle_lists_command(self, args: list[str]) -> None:
        """Handle lists command."""
        try:
            lists = self.board.get_lists() if hasattr(self.board, "get_lists") else []

            if not lists:
                self.console.print("[yellow] No lists found in this board[/yellow]")
                return

            table = Table(title="Board Lists")
            table.add_column("#", style="bold yellow", width=3)
            table.add_column("ID", style="cyan", no_wrap=True)
            table.add_column("Title", style="magenta")
            table.add_column("Cards", style="green", justify="right")

            for i, lst in enumerate(lists, 1):
                try:
                    cards = lst.get_cards() if hasattr(lst, "get_cards") else []
                    card_count = str(len(cards))
                except Exception:
                    card_count = "?"

                table.add_row(str(i), lst.id[:8] + "...", lst.title, card_count)

            self.console.print(table)

        except Exception as e:
            self.console.print(f"[red] Error listing lists: {str(e)}[/red]")

    def handle_cards_command(self, args: list[str]) -> None:
        """Handle cards command."""
        if not args:
            self.console.print("[red] Usage: cards <list-id>[/red]")
            return

        try:
            lists = self.board.get_lists() if hasattr(self.board, "get_lists") else []
            target_list = None

            # Find list by index or ID
            list_id = args[0]
            if list_id.isdigit():
                index = int(list_id) - 1
                if 0 <= index < len(lists):
                    target_list = lists[index]
            else:
                for lst in lists:
                    if lst.id.startswith(list_id) or list_id.lower() in lst.title.lower():
                        target_list = lst
                        break

            if not target_list:
                self.console.print(f"[red] List '{list_id}' not found[/red]")
                return

            cards = target_list.get_cards() if hasattr(target_list, "get_cards") else []

            if not cards:
                self.console.print(f"[yellow] No cards in list '{target_list.title}'[/yellow]")
                return

            table = Table(title=f"Cards in '{target_list.title}'")
            table.add_column("#", style="bold yellow", width=3)
            table.add_column("ID", style="cyan", no_wrap=True)
            table.add_column("Title", style="magenta")
            table.add_column("Description", style="green")

            for i, card in enumerate(cards, 1):
                desc = getattr(card, "description", "") or "No description"
                desc = desc[:50] + "..." if len(desc) > 50 else desc

                table.add_row(str(i), card.id[:8] + "...", card.title, desc)

            self.console.print(table)

        except Exception as e:
            self.console.print(f"[red] Error listing cards: {str(e)}[/red]")

    def handle_list_command(self, args: list[str]) -> None:
        """Handle list commands (create, show, etc)."""
        if not args:
            self.console.print("[red] Usage: list <create|show> ...[/red]")
            return

        subcommand = args[0].lower()

        if subcommand == "create":
            if len(args) < 2:
                self.console.print("[red] Usage: list create <name>[/red]")
                return

            list_name = " ".join(args[1:])
            try:
                self.board.create_list(title=list_name)
                self.console.print(f"[green] Created list '[bold]{list_name}[/bold]'[/green]")
                self.show_board()  # Refresh board view
            except Exception as e:
                self.console.print(f"[red] Error creating list: {str(e)}[/red]")

        elif subcommand == "show":
            if len(args) < 2:
                self.console.print("[red] Usage: list show <id>[/red]")
                return

            # Implementation for showing list details
            self.console.print("[yellow]  List details feature coming soon[/yellow]")

        else:
            self.console.print(f"[red] Unknown list command: {subcommand}[/red]")

    def handle_card_command(self, args: list[str]) -> None:
        """Handle card commands (create, show, etc)."""
        if not args:
            self.console.print("[red] Usage: card <create|show> ...[/red]")
            return

        subcommand = args[0].lower()

        if subcommand == "create":
            if len(args) < 3:
                self.console.print("[red] Usage: card create <list-id> <title>[/red]")
                return

            # Implementation for creating cards
            self.console.print("[yellow]  Card creation feature coming soon[/yellow]")

        elif subcommand == "show":
            # Implementation for showing card details
            self.console.print("[yellow]  Card details feature coming soon[/yellow]")

        else:
            self.console.print(f"[red] Unknown card command: {subcommand}[/red]")


def activate_board(identifier: str) -> None:
    """Activate board context for interactive work.

    Args:
        identifier: Board identifier (ID prefix, name, or index)
    """
    config = load_config()

    if not config.base_url or not config.username or not config.password:
        print(" Not configured. Run 'wekan config init' to set up.")
        return

    try:
        client = WekanClient(
            base_url=config.base_url, username=config.username, password=config.password
        )

        board = find_board(client, identifier)
        if not board:
            return

        # Start interactive board session
        context = BoardContext(client, board)
        context.run_interactive_session()

    except Exception as e:
        print(f" Error activating board: {str(e)}")
