"""
Hierarchical navigation system for WeKan CLI.
"""

import readline
import sys
from enum import Enum
from pathlib import Path
from typing import Optional

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
except ImportError:
    print("CLI dependencies not installed. Install with: pip install python-wekan[cli]")
    sys.exit(1)

from wekan.board import Board
from wekan.card import WekanCard
from wekan.wekan_client import WekanClient
from wekan.wekan_list import WekanList

from .commands.boards import find_board
from .config import load_config


class ContextLevel(Enum):
    """Navigation context levels."""

    ROOT = "root"
    BOARD = "board"
    LIST = "list"
    CARD = "card"


class NavigationContext:
    """Hierarchical navigation context for WeKan CLI."""

    def __init__(self, client: WekanClient):
        self.client = client
        self.console = Console()

        # Navigation state
        self.level = ContextLevel.ROOT
        self.board: Optional[Board] = None
        self.list_obj: Optional[WekanList] = None
        self.card: Optional[WekanCard] = None

        # Navigation history
        self.history: list[str] = []
        self.setup_readline()

    def setup_readline(self) -> None:
        """Setup readline for command history and arrow key navigation."""
        try:
            # Enable history
            readline.set_history_length(1000)

            # Try to load existing history
            history_file = Path.home() / ".wekan_history"
            try:
                readline.read_history_file(str(history_file))
            except FileNotFoundError:
                pass

            # Setup completion (basic)
            readline.set_completer(self.completer)
            readline.parse_and_bind("tab: complete")

        except ImportError:
            # readline not available on this system
            pass

    def save_history(self) -> None:
        """Save command history to file."""
        try:
            history_file = Path.home() / ".wekan_history"
            readline.write_history_file(str(history_file))
        except OSError:
            pass

    def completer(self, text: str, state: int) -> Optional[str]:
        """Basic tab completion."""
        commands = self.get_available_commands()
        matches = [cmd for cmd in commands if cmd.startswith(text)]
        if state < len(matches):
            return matches[state]
        return None

    def get_prompt(self) -> str:
        """Get current navigation prompt (plain text for input())."""
        parts = []

        if self.board:
            board_name = (
                self.board.title[:15] + "..." if len(self.board.title) > 15 else self.board.title
            )
            parts.append(board_name)

        if self.list_obj:
            list_name = (
                self.list_obj.title[:12] + "..."
                if len(self.list_obj.title) > 12
                else self.list_obj.title
            )
            parts.append(list_name)

        if self.card:
            card_name = (
                self.card.title[:10] + "..." if len(self.card.title) > 10 else self.card.title
            )
            parts.append(card_name)

        if not parts:
            return "wekan> "

        return " / ".join(parts) + "> "

    def get_breadcrumb(self) -> str:
        """Get breadcrumb navigation path."""
        parts = ["root"]

        if self.board:
            parts.append(self.board.title)

        if self.list_obj:
            parts.append(self.list_obj.title)

        if self.card:
            parts.append(self.card.title)

        return " -> ".join(parts)

    def get_available_commands(self) -> list[str]:
        """Get available commands for current context."""
        base_commands = ["help", "pwd", "ls", "cd", "exit", "quit"]

        if self.level == ContextLevel.ROOT:
            return base_commands
        elif self.level == ContextLevel.BOARD:
            return base_commands + ["mkdir"]
        elif self.level == ContextLevel.LIST:
            return base_commands + ["touch", "mv", "rm"]
        elif self.level == ContextLevel.CARD:
            return base_commands + ["edit", "mv", "rm"]

        return base_commands

    def activate_board(self, identifier: str) -> bool:
        """Activate/navigate to a board."""
        board = find_board(self.client, identifier)
        if not board:
            return False

        self.board = board
        self.list_obj = None
        self.card = None
        self.level = ContextLevel.BOARD
        return True

    def activate_list(self, identifier: str) -> bool:
        """Activate/navigate to a list within current board."""
        if not self.board:
            self.console.print("[red]No board selected. Navigate to a board first.[/red]")
            return False

        try:
            lists = self.board.get_lists()
            if not lists:
                self.console.print(f"[red]List '{identifier}' not found[/red]")
                return False

            target_list = None
            if identifier.isdigit():
                index = int(identifier) - 1
                if 0 <= index < len(lists):
                    target_list = lists[index]
            else:
                for lst in lists:
                    if lst.id and identifier in lst.id:
                        target_list = lst
                        break
                    if lst.title and identifier.lower() in lst.title.lower():
                        target_list = lst
                        break

            if not target_list:
                self.console.print(f"[red]List '{identifier}' not found[/red]")
                return False

            self.list_obj = target_list
            self.card = None
            self.level = ContextLevel.LIST
            return True

        except Exception as e:
            self.console.print(f"[red]Error finding list: {str(e)}[/red]")
            return False

    def activate_card(self, identifier: str) -> bool:
        """Activate/navigate to a card within current list."""
        if not self.list_obj:
            self.console.print("[red]No list selected. Navigate to a list first.[/red]")
            return False

        try:
            cards = self.list_obj.get_cards()
            if not cards:
                self.console.print(f"[red]Card '{identifier}' not found[/red]")
                return False

            target_card = None
            if identifier.isdigit():
                index = int(identifier) - 1
                if 0 <= index < len(cards):
                    target_card = cards[index]
            else:
                for card in cards:
                    if card.id and identifier in card.id:
                        target_card = card
                        break
                    if card.title and identifier.lower() in card.title.lower():
                        target_card = card
                        break

            if not target_card:
                self.console.print(f"[red]Card '{identifier}' not found[/red]")
                return False

            self.card = target_card
            self.level = ContextLevel.CARD
            return True

        except Exception as e:
            self.console.print(f"[red]Error finding card: {str(e)}[/red]")
            return False

    def handle_cd(self, args: list[str]) -> None:
        """Handle cd (change directory) command."""
        if not args:
            self.console.print("[red]Usage: cd <board|list|card>[/red]")
            return

        target = args[0]

        # Handle special paths
        if target == "..":
            self.go_back()
            return
        elif target == "/":
            self.go_to_root()
            return

        # Try to navigate based on current context
        if self.level == ContextLevel.ROOT:
            if self.activate_board(target):
                board_title = self.board.title if self.board else "Unknown"
                self.console.print(f"[green]Entered board: {board_title}[/green]")
        elif self.level == ContextLevel.BOARD:
            if self.activate_list(target):
                list_title = self.list_obj.title if self.list_obj else "Unknown"
                self.console.print(f"[green]Entered list: {list_title}[/green]")
        elif self.level == ContextLevel.LIST:
            if self.activate_card(target):
                card_title = self.card.title if self.card else "Unknown"
                self.console.print(f"[green]Entered card: {card_title}[/green]")
        elif self.level == ContextLevel.CARD:
            self.console.print("[yellow]Already at deepest level (card)[/yellow]")

    def handle_pwd(self) -> None:
        """Handle pwd (print working directory) command."""
        breadcrumb = self.get_breadcrumb()
        self.console.print(f"Current path: {breadcrumb}")

    def handle_ls(self, args: Optional[list[str]] = None) -> None:
        """Handle ls (list) command."""
        if self.level == ContextLevel.ROOT:
            self.list_boards()
        elif self.level == ContextLevel.BOARD:
            self.list_board_contents()
        elif self.level == ContextLevel.LIST:
            self.list_list_contents()
        elif self.level == ContextLevel.CARD:
            self.show_card_details()

    def go_back(self) -> None:
        """Navigate back one level."""
        if self.level == ContextLevel.CARD:
            self.card = None
            self.level = ContextLevel.LIST
            if self.list_obj:
                self.console.print(f"[green]Back to list: {self.list_obj.title}[/green]")
        elif self.level == ContextLevel.LIST:
            self.list_obj = None
            self.level = ContextLevel.BOARD
            if self.board:
                self.console.print(f"[green]Back to board: {self.board.title}[/green]")
        elif self.level == ContextLevel.BOARD:
            self.board = None
            self.level = ContextLevel.ROOT
            self.console.print("[green]Back to root[/green]")
        else:
            self.console.print("[yellow]Already at root level[/yellow]")

    def go_to_root(self) -> None:
        """Navigate to root level."""
        self.board = None
        self.list_obj = None
        self.card = None
        self.level = ContextLevel.ROOT
        self.console.print("[green]Returned to root[/green]")

    def list_boards(self) -> None:
        """List available boards."""
        try:
            boards = self.client.list_boards()

            if not boards:
                self.console.print("[yellow]No boards found.[/yellow]")
                return

            table = Table(title="Available Boards")
            table.add_column("#", style="bold yellow", width=3)
            table.add_column("ID", style="cyan", no_wrap=True)
            table.add_column("Title", style="magenta")
            table.add_column("Lists", style="green", justify="right")

            for i, board in enumerate(boards, 1):
                try:
                    lists = board.get_lists()
                    list_count = str(len(lists))
                except Exception:
                    list_count = "?"

                table.add_row(
                    str(i),
                    board.id[:8] + "..." if board.id else "",
                    board.title,
                    list_count,
                )

            self.console.print(table)
            self.console.print("\nUse [bold]cd <index|name|id>[/bold] to enter a board")

        except Exception as e:
            self.console.print(f"[red]Error listing boards: {str(e)}[/red]")

    def list_board_contents(self) -> None:
        """List contents of current board."""
        if not self.board:
            return

        try:
            lists = self.board.get_lists()

            if not lists:
                self.console.print("[yellow]No lists in this board.[/yellow]")
                self.console.print("Create lists with: [bold]mkdir <name>[/bold]")
                return

            table = Table(title=f"Lists in '{self.board.title}'")
            table.add_column("#", style="bold yellow", width=3)
            table.add_column("ID", style="cyan", no_wrap=True)
            table.add_column("Title", style="magenta")
            table.add_column("Cards", style="green", justify="right")

            for i, lst in enumerate(lists, 1):
                try:
                    cards = lst.get_cards()
                    card_count = str(len(cards))
                except Exception:
                    card_count = "?"

                table.add_row(str(i), lst.id[:8] + "..." if lst.id else "", lst.title, card_count)

            self.console.print(table)
            self.console.print("\nUse [bold]cd <index|name|id>[/bold] to enter a list")

        except Exception as e:
            self.console.print(f"[red]Error listing board contents: {str(e)}[/red]")

    def list_list_contents(self) -> None:
        """List contents of current list."""
        if not self.list_obj:
            return

        try:
            cards = self.list_obj.get_cards()

            if not cards:
                self.console.print(f"[yellow]No cards in list '{self.list_obj.title}'.[/yellow]")
                self.console.print("Create cards with: [bold]create card <title>[/bold]")
                return

            table = Table(title=f"Cards in '{self.list_obj.title}'")
            table.add_column("#", style="bold yellow", width=3)
            table.add_column("ID", style="cyan", no_wrap=True)
            table.add_column("Title", style="magenta")
            table.add_column("Description", style="green")

            for i, card in enumerate(cards, 1):
                desc = getattr(card, "description", "") or "No description"
                desc = desc[:30] + "..." if len(desc) > 30 else desc
                card_id = card.id[:8] + "..." if card and card.id else ""
                card_title = card.title if card and card.title else "Untitled"

                table.add_row(str(i), card_id, card_title, desc)

            self.console.print(table)
            self.console.print("\nUse [bold]cd <index|name|id>[/bold] to enter a card")

        except Exception as e:
            self.console.print(f"[red]Error listing list contents: {str(e)}[/red]")

    def show_card_details(self) -> None:
        """Show detailed view of current card."""
        if not self.card:
            return

        try:
            # Create detailed card view
            details = []
            details.append(f"ID: {self.card.id if self.card and self.card.id else 'Unknown'}")
            details.append(
                f"Title: {self.card.title if self.card and self.card.title else 'Untitled'}"
            )
            description = (
                getattr(self.card, "description", "No description")
                if self.card
                else "No description"
            )
            details.append(f"Description: {description}")
            created = getattr(self.card, "created_at", "Unknown") if self.card else "Unknown"
            details.append(f"Created: {created}")
            if self.list_obj:
                details.append(f"List: {self.list_obj.title}")
            if self.board:
                details.append(f"Board: {self.board.title}")

            self.console.print(
                Panel.fit(
                    "\n".join(details),
                    title=f"Card: {self.card.title}",
                    border_style="blue",
                )
            )

        except Exception as e:
            self.console.print(f"[red]Error showing card details: {str(e)}[/red]")

    def show_help(self) -> None:
        """Show available commands for current context."""
        help_table = Table(title=f"Available Commands ({self.level.value.title()} Level)")
        help_table.add_column("Command", style="cyan", width=20)
        help_table.add_column("Description", style="white")

        # Universal commands (Linux-style)
        universal_commands = [
            ("pwd", "Show current navigation path"),
            ("ls", "List current level contents"),
            ("cd <target>", "Navigate to target (board/list/card)"),
            ("cd ..", "Go back one level"),
            ("cd /", "Go to root level"),
            ("..", "Go back one level (shortcut)"),
            ("/", "Go to root level (shortcut)"),
            ("help", "Show this help message"),
            ("exit, quit", "Exit WeKan CLI"),
        ]

        # Context-specific commands (Linux filesystem style)
        context_commands: list[tuple[str, str]] = []
        if self.level == ContextLevel.ROOT:
            context_commands = []
        elif self.level == ContextLevel.BOARD:
            context_commands = [
                ("mkdir <name>", "Create new list (like mkdir for directories)"),
            ]
        elif self.level == ContextLevel.LIST:
            context_commands = [
                ("touch <title>", "Create new card (like touch for files)"),
                ("mv <card> <list>", "Move card to another list"),
                ("rm <card>", "Remove/delete card"),
            ]
        elif self.level == ContextLevel.CARD:
            context_commands = [
                ("edit", "Edit card properties"),
                ("mv <list>", "Move this card to another list"),
                ("rm", "Remove/delete this card"),
            ]

        all_commands = universal_commands + context_commands

        for cmd, desc in all_commands:
            help_table.add_row(cmd, desc)

        self.console.print(help_table)

    def run_interactive_session(self) -> None:
        """Run the interactive navigation session."""
        self.console.print()
        self.console.print("[bold green]WeKan Navigation Shell[/bold green]")
        self.console.print("Navigate through boards, lists, and cards like a filesystem.")
        self.console.print(
            "Use [bold]help[/bold] for commands, [bold]up/down arrows[/bold] for history."
        )
        self.console.print()

        # Show initial state
        self.handle_ls()

        while True:
            try:
                # Show breadcrumb
                breadcrumb = self.get_breadcrumb()
                self.console.print(f"\n{breadcrumb}")

                # Get command with history support
                prompt_text = self.get_prompt()
                try:
                    command = input(prompt_text).strip()
                except KeyboardInterrupt:
                    self.console.print("\nExiting WeKan CLI")
                    break
                except EOFError:
                    self.console.print("\nExiting WeKan CLI")
                    break

                if not command:
                    continue

                # Parse command
                parts = command.split()
                cmd = parts[0].lower()
                args = parts[1:] if len(parts) > 1 else []

                # Handle commands
                if cmd in ["exit", "quit", "q"]:
                    self.console.print("Exiting WeKan CLI")
                    break

                elif cmd in ["help", "h"]:
                    self.show_help()

                elif cmd == "pwd":
                    self.handle_pwd()

                elif cmd in ["ls", "list"]:
                    self.handle_ls(args)

                elif cmd == "cd":
                    self.handle_cd(args)

                elif cmd in [".."]:
                    self.go_back()

                elif cmd in ["/"]:
                    self.go_to_root()

                elif cmd == "mkdir" and self.level == ContextLevel.BOARD:
                    self.handle_mkdir(args)

                elif cmd == "touch" and self.level == ContextLevel.LIST:
                    self.handle_touch(args)

                elif cmd == "edit" and self.level == ContextLevel.CARD:
                    self.handle_edit_card()

                elif cmd == "mv":
                    self.handle_mv(args)

                elif cmd == "rm":
                    self.handle_rm(args)

                else:
                    self.console.print(f"[red]Unknown command: {cmd}[/red]")
                    self.console.print("Type [bold]help[/bold] for available commands")

            except Exception as e:
                self.console.print(f"[red]Error: {str(e)}[/red]")

        # Save history on exit
        self.save_history()

    def handle_mkdir(self, args: list[str]) -> None:
        """Handle mkdir command - create new list."""
        if not args:
            self.console.print("[red]Usage: mkdir <list-name>[/red]")
            return

        if self.level != ContextLevel.BOARD:
            self.console.print("[red]mkdir can only be used at board level[/red]")
            return

        if not self.board:
            self.console.print("[red]No board selected[/red]")
            return

        list_name = " ".join(args)
        try:
            self.board.create_list(title=list_name)
            self.console.print(f"[green]Created list '[bold]{list_name}[/bold]'[/green]")
        except Exception as e:
            self.console.print(f"[red]Error creating list: {str(e)}[/red]")

    def handle_touch(self, args: list[str]) -> None:
        """Handle touch command - create new card."""
        if not args:
            self.console.print("[red]Usage: touch <card-title>[/red]")
            return

        if self.level != ContextLevel.LIST:
            self.console.print("[red]touch can only be used at list level[/red]")
            return

        card_title = " ".join(args)
        self.console.print(f"[yellow]Card creation coming soon: '{card_title}'[/yellow]")
        # TODO: Implement actual card creation when API is available

    def handle_mv(self, args: list[str]) -> None:
        """Handle mv command - move card to another list."""
        if self.level == ContextLevel.CARD:
            # Move current card to specified list
            if not args:
                self.console.print("[red]Usage: mv <target-list>[/red]")
                return

            target_identifier = args[0]
            self.move_current_card_to_list(target_identifier)

        elif self.level == ContextLevel.LIST:
            # Move specified card to specified list
            if len(args) < 2:
                self.console.print("[red]Usage: mv <card> <target-list>[/red]")
                return

            card_identifier = args[0]
            target_list_identifier = args[1]
            self.move_card_between_lists(card_identifier, target_list_identifier)
        else:
            self.console.print("[red]mv can only be used at card or list level[/red]")

    def handle_rm(self, args: list[str]) -> None:
        """Handle rm command - remove/delete card."""
        if self.level == ContextLevel.CARD:
            # Delete current card
            self.delete_current_card()

        elif self.level == ContextLevel.LIST:
            # Delete specified card
            if not args:
                self.console.print("[red]Usage: rm <card>[/red]")
                return

            card_identifier = args[0]
            self.delete_card_from_list(card_identifier)
        else:
            self.console.print("[red]rm can only be used at card or list level[/red]")

    def move_current_card_to_list(self, target_identifier: str) -> None:
        """Move current card to target list."""
        if not self.board or not self.card or not self.list_obj:
            self.console.print("[red]Invalid navigation state for card movement[/red]")
            return

        try:
            lists = self.board.get_lists()
            target_list = None

            # Find target list
            if target_identifier.isdigit():
                index = int(target_identifier) - 1
                if 0 <= index < len(lists):
                    target_list = lists[index]
            else:
                for lst in lists:
                    if lst.id and target_identifier in lst.id:
                        target_list = lst
                        break
                    if lst.title and target_identifier.lower() in lst.title.lower():
                        target_list = lst
                        break

            if not target_list:
                self.console.print(f"[red]List '{target_identifier}' not found[/red]")
                # Show available lists
                self.console.print("\nAvailable lists:")
                for i, lst in enumerate(lists, 1):
                    self.console.print(f"  {i}. {lst.title}")
                return

            if target_list.id == self.list_obj.id:
                self.console.print("[yellow]Card is already in this list[/yellow]")
                return

            from rich.prompt import Confirm

            if Confirm.ask(f"Move '{self.card.title}' to '{target_list.title}'?"):
                try:
                    # Move the card using the WeKan API
                    self.card.edit(new_list=target_list)

                    self.console.print(f"[green]Card moved to '{target_list.title}'![/green]")

                    # Update navigation context and go back to list level
                    self.list_obj = target_list
                    self.card = None
                    self.level = ContextLevel.LIST
                    self.console.print(f"[blue]Moved to '{target_list.title}' list[/blue]")

                except Exception as e:
                    self.console.print(f"[red]Failed to move card: {str(e)}[/red]")
            else:
                self.console.print("[yellow]Move cancelled[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error moving card: {str(e)}[/red]")

    def move_card_between_lists(self, card_identifier: str, target_list_identifier: str) -> None:
        """Move specified card to target list."""
        # TODO: Implement card selection and movement from list level
        self.console.print("[yellow]Card movement from list level coming soon[/yellow]")
        self.console.print("For now, navigate to the card first: cd <card>, then use mv <list>")

    def delete_current_card(self) -> None:
        """Delete current card."""
        from rich.prompt import Confirm

        if self.card and Confirm.ask(
            f"[red]Delete card '{self.card.title}'? This cannot be undone![/red]"
        ):
            try:
                # TODO: Implement actual card deletion when API is available
                self.console.print("[yellow]Card deletion API coming soon[/yellow]")
                if self.card:
                    self.console.print(f"[yellow]Would delete: '{self.card.title}'[/yellow]")

                # For now, just navigate back to list level
                self.card = None
                self.level = ContextLevel.LIST
                self.console.print("[blue]Returned to list level[/blue]")

            except Exception as e:
                self.console.print(f"[red]Failed to delete card: {str(e)}[/red]")
        else:
            self.console.print("[yellow]Deletion cancelled[/yellow]")

    def delete_card_from_list(self, card_identifier: str) -> None:
        """Delete specified card from current list."""
        # TODO: Implement card selection and deletion from list level
        self.console.print("[yellow]Card deletion from list level coming soon[/yellow]")
        self.console.print("For now, navigate to the card first: cd <card>, then use rm")

    def handle_edit_card(self) -> None:
        """Handle comprehensive card editing."""
        if not self.card:
            return

        try:
            self.console.print()
            self.console.print(f"✏️  [bold]Comprehensive Card Editor: {self.card.title}[/bold]")
            self.console.print()

            # Show editing menu
            while True:
                self.show_card_edit_menu()
                choice = input("\nSelect field to edit (or 'done' to finish): ").strip().lower()

                if choice in ["done", "d", "exit", "q"]:
                    break
                elif choice == "1":
                    self.edit_card_basic()
                elif choice == "2":
                    self.edit_card_dates()
                elif choice == "3":
                    self.edit_card_members()
                elif choice == "4":
                    self.edit_card_labels()
                elif choice == "5":
                    self.edit_card_description()
                elif choice == "6":
                    self.edit_card_color()
                elif choice == "7":
                    self.show_card_advanced_menu()
                else:
                    self.console.print("[red]Invalid choice. Please try again.[/red]")

                input("\nPress Enter to continue...")

        except KeyboardInterrupt:
            self.console.print("\n[yellow]Edit cancelled[/yellow]")
        except Exception as e:
            self.console.print(f"[red]Error in card editor: {str(e)}[/red]")

    def show_card_edit_menu(self) -> None:
        """Show the card editing menu."""
        self.console.print("╭─────────────────────────────────────────────────────────────╮")
        self.console.print("│                       Card Editor Menu                       │")
        self.console.print("├─────────────────────────────────────────────────────────────┤")
        self.console.print("│ 1. Basic Info (Title)                                      │")
        self.console.print("│ 2. Dates & Times (Start, Due, End, Received)               │")
        self.console.print("│ 3. Members & Roles (Assign, Request, Creator)              │")
        self.console.print("│ 4. Labels & Tags                                           │")
        self.console.print("│ 5. Description                                             │")
        self.console.print("│ 6. Card Color                                              │")
        self.console.print("│ 7. Advanced (Comments, Subtasks, Custom Fields)           │")
        self.console.print("├─────────────────────────────────────────────────────────────┤")
        self.console.print("│ Type 'done' when finished editing                          │")
        self.console.print("╰─────────────────────────────────────────────────────────────╯")

    def edit_card_basic(self) -> None:
        """Edit basic card information."""
        if not self.card:
            return

        self.console.print("\n[bold]Editing Basic Information[/bold]")

        current_title = self.card.title
        self.console.print(f"Current title: [cyan]{current_title}[/cyan]")
        new_title = input("New title (Enter to keep current): ").strip()

        if new_title and new_title != current_title:
            try:
                self.card.edit(title=new_title)
                self.console.print(f"[green]Title updated to: {new_title}[/green]")
                self.card.title = new_title  # Update local object
            except Exception as e:
                self.console.print(f"[red]Failed to update title: {str(e)}[/red]")
        else:
            self.console.print("[dim]No changes made to title[/dim]")

    def edit_card_dates(self) -> None:
        """Edit card dates and times."""
        self.console.print("\n[bold]Editing Dates & Times[/bold]")
        self.console.print(
            "[dim]Format: YYYY-MM-DD HH:MM or YYYY-MM-DD (leave empty to clear)[/dim]"
        )

        # Get current dates
        dates = {
            "received_at": getattr(self.card, "received_at", None),
            "start_at": getattr(self.card, "start_at", None),
            "due_at": getattr(self.card, "due_at", None),
            "end_at": getattr(self.card, "end_at", None),
        }

        date_labels = {
            "received_at": "Received Date",
            "start_at": "Start Date",
            "due_at": "Due Date",
            "end_at": "End Date",
        }

        changes = {}

        for field, label in date_labels.items():
            current = dates[field]
            current_str = str(current) if current else "Not set"
            self.console.print(f"\n{label}: [cyan]{current_str}[/cyan]")

            new_date_str = input(f"New {label.lower()} (YYYY-MM-DD [HH:MM]): ").strip()

            if new_date_str:
                try:
                    # Parse the date
                    from dateutil import parser

                    new_date = parser.parse(new_date_str)
                    changes[field] = new_date.isoformat() if new_date else None
                    self.console.print(f"[green]✓ {label} will be set to: {new_date}[/green]")
                except Exception as e:
                    self.console.print(f"[red]Invalid date format: {str(e)}[/red]")
            elif new_date_str == "":
                # User wants to clear the date
                changes[field] = None
                self.console.print(f"[yellow]✓ {label} will be cleared[/yellow]")

        # Apply changes
        if changes and self.card:
            try:
                self.card.edit(**changes)
                self.console.print(
                    f"[green]Updated {len(changes)} date field(s) successfully![/green]"
                )
            except Exception as e:
                self.console.print(f"[red]Failed to update dates: {str(e)}[/red]")
        else:
            self.console.print("[dim]No date changes made[/dim]")

    def edit_card_members(self) -> None:
        """Edit card members and roles."""
        self.console.print("\n[bold]Editing Members & Roles[/bold]")

        # Get board members for selection
        try:
            board_members = (
                self.board.get_members()
                if self.board and hasattr(self.board, "get_members")
                else []
            )

            if board_members:
                self.console.print("\nAvailable board members:")
                for i, member in enumerate(board_members, 1):
                    username = member.get("username", "Unknown")
                    fullname = member.get("profile", {}).get("fullname", "")
                    self.console.print(f"  {i}. {username} ({fullname})")

            # Current assignments
            current_members = getattr(self.card, "members", [])
            if current_members:
                self.console.print(f"\nCurrent members: {', '.join(current_members)}")

            # Note: Full member management would require more complex UI
            self.console.print("\n[yellow]Member management requires board member IDs.[/yellow]")
            self.console.print(
                "[yellow]This feature will be enhanced in a future version.[/yellow]"
            )

        except Exception as e:
            self.console.print(f"[red]Error accessing board members: {str(e)}[/red]")

    def edit_card_labels(self) -> None:
        """Edit card labels."""
        self.console.print("\n[bold]Editing Labels[/bold]")

        try:
            # Get available labels from the board
            board_labels = (
                self.board.get_labels() if self.board and hasattr(self.board, "get_labels") else []
            )

            if board_labels:
                self.console.print("\nAvailable labels:")
                for i, label in enumerate(board_labels, 1):
                    name = getattr(label, "name", "Unnamed")
                    color = getattr(label, "color", "default")
                    self.console.print(f"  {i}. [bold]{name}[/bold] ({color})")

                # Show current labels
                current_labels = getattr(self.card, "label_ids", [])
                if current_labels:
                    self.console.print(f"\nCurrent label IDs: {current_labels}")

                self.console.print(
                    "\n[yellow]Label assignment requires specific label IDs.[/yellow]"
                )
                self.console.print("[yellow]Enhanced label management coming soon.[/yellow]")
            else:
                self.console.print("[yellow]No labels found on this board.[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error accessing board labels: {str(e)}[/red]")

    def edit_card_description(self) -> None:
        """Edit card description with multi-line support."""
        self.console.print("\n[bold]Editing Description[/bold]")

        current_desc = getattr(self.card, "description", "") if self.card else ""
        self.console.print(f"Current description: [cyan]{current_desc or 'Empty'}[/cyan]")
        self.console.print("[dim]Enter new description (type 'END' on a new line to finish):[/dim]")

        lines = []
        while True:
            line = input()
            if line.strip() == "END":
                break
            lines.append(line)

        new_desc = "\n".join(lines).strip()

        if new_desc != current_desc and self.card:
            try:
                self.card.edit(description=new_desc)
                self.console.print("[green]Description updated successfully![/green]")
                self.card.description = new_desc  # Update local object
            except Exception as e:
                self.console.print(f"[red]Failed to update description: {str(e)}[/red]")
        else:
            self.console.print("[dim]No changes made to description[/dim]")

    def edit_card_color(self) -> None:
        """Edit card color."""
        self.console.print("\n[bold]Editing Card Color[/bold]")

        colors = [
            "white",
            "yellow",
            "orange",
            "red",
            "purple",
            "blue",
            "green",
            "black",
            "sky",
            "pink",
            "lime",
        ]
        current_color = getattr(self.card, "color", "white") if self.card else "white"

        self.console.print(f"Current color: [cyan]{current_color}[/cyan]")
        self.console.print("\nAvailable colors:")
        for i, color in enumerate(colors, 1):
            self.console.print(f"  {i}. {color}")

        choice = input(f"\nSelect color (1-{len(colors)} or color name): ").strip()

        new_color = None
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(colors):
                new_color = colors[idx]
        elif choice.lower() in colors:
            new_color = choice.lower()

        if new_color and new_color != current_color and self.card:
            try:
                self.card.edit(color=new_color)
                self.console.print(f"[green]Card color changed to: {new_color}[/green]")
                # Note: color is handled via the API, not as a direct attribute
            except Exception as e:
                self.console.print(f"[red]Failed to update color: {str(e)}[/red]")
        else:
            self.console.print("[dim]No color changes made[/dim]")

    def show_card_advanced_menu(self) -> None:
        """Show advanced card editing options."""
        self.console.print("\n[bold]Advanced Card Features[/bold]")
        self.console.print()
        self.console.print("1. Comments")
        self.console.print("2. Subtasks/Checklists")
        self.console.print("3. Custom Fields")
        self.console.print("4. Time Tracking")
        self.console.print("5. Attachments")

        choice = input("\nSelect advanced feature (1-5): ").strip()

        if choice == "1":
            self.show_card_comments()
        elif choice == "2":
            self.show_card_checklists()
        elif choice == "3":
            self.show_custom_fields()
        elif choice == "4":
            self.edit_time_tracking()
        elif choice == "5":
            self.console.print("[yellow]Attachment management coming soon[/yellow]")
        else:
            self.console.print("[red]Invalid choice[/red]")

    def show_card_comments(self) -> None:
        """Show and manage card comments."""
        self.console.print("\n[bold]Card Comments[/bold]")

        try:
            comments = (
                self.card.get_comments() if self.card and hasattr(self.card, "get_comments") else []
            )

            if comments:
                for i, comment in enumerate(comments, 1):
                    author = getattr(comment, "author", "Unknown")
                    text = getattr(comment, "text", "")
                    created = getattr(comment, "created_at", "Unknown time")
                    self.console.print(f"\n{i}. [bold]{author}[/bold] ({created})")
                    self.console.print(f"   {text}")
            else:
                self.console.print("[yellow]No comments on this card[/yellow]")

            # Option to add new comment
            new_comment = input("\nAdd new comment (Enter to skip): ").strip()
            if new_comment:
                try:
                    # Note: This would need the actual comment creation API
                    self.console.print(
                        "[yellow]Comment creation API integration coming soon[/yellow]"
                    )
                except Exception as e:
                    self.console.print(f"[red]Failed to add comment: {str(e)}[/red]")

        except Exception as e:
            self.console.print(f"[red]Error accessing comments: {str(e)}[/red]")

    def show_card_checklists(self) -> None:
        """Show and manage card checklists."""
        self.console.print("\n[bold]Card Checklists/Subtasks[/bold]")

        try:
            checklists = (
                self.card.get_checklists()
                if self.card and hasattr(self.card, "get_checklists")
                else []
            )

            if checklists:
                for i, checklist in enumerate(checklists, 1):
                    title = getattr(checklist, "title", "Untitled")
                    items = getattr(checklist, "items", [])
                    self.console.print(f"\n{i}. [bold]{title}[/bold] ({len(items)} items)")

                    for j, item in enumerate(items, 1):
                        item_title = getattr(item, "title", "Untitled item")
                        finished = getattr(item, "is_finished", False)
                        status = "[✓]" if finished else "[ ]"
                        self.console.print(f"   {status} {j}. {item_title}")
            else:
                self.console.print("[yellow]No checklists on this card[/yellow]")

            self.console.print("[yellow]Checklist management API integration coming soon[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error accessing checklists: {str(e)}[/red]")

    def show_custom_fields(self) -> None:
        """Show and manage custom fields."""
        self.console.print("\n[bold]Custom Fields[/bold]")
        self.console.print("[yellow]Custom field management coming soon[/yellow]")

    def edit_time_tracking(self) -> None:
        """Edit time tracking information."""
        self.console.print("\n[bold]Time Tracking[/bold]")

        current_spent = getattr(self.card, "spent_time", 0) or 0 if self.card else 0
        current_overtime = getattr(self.card, "is_overtime", False) if self.card else False

        self.console.print(f"Current spent time: [cyan]{current_spent} hours[/cyan]")
        self.console.print(f"Overtime: [cyan]{current_overtime}[/cyan]")

        new_spent_str = input("New spent time (hours, decimal allowed): ").strip()
        new_overtime_str = input("Is overtime? (y/n): ").strip().lower()

        changes = {}

        if new_spent_str:
            try:
                new_spent = float(new_spent_str)
                changes["spent_time"] = new_spent
            except ValueError:
                self.console.print("[red]Invalid spent time format[/red]")
                return

        if new_overtime_str in ["y", "yes", "true", "1"]:
            changes["is_overtime"] = True
        elif new_overtime_str in ["n", "no", "false", "0"]:
            changes["is_overtime"] = False

        if changes and self.card:
            try:
                self.card.edit(**changes)
                self.console.print("[green]Time tracking updated successfully![/green]")
            except Exception as e:
                self.console.print(f"[red]Failed to update time tracking: {str(e)}[/red]")
        else:
            self.console.print("[dim]No time tracking changes made[/dim]")


def start_navigation() -> None:
    """Start the WeKan navigation shell."""
    config = load_config()

    if not config.base_url or not config.username or not config.password:
        print("Not configured. Run 'wekan config init' to set up.")
        return

    try:
        client = WekanClient(
            base_url=config.base_url, username=config.username, password=config.password
        )

        nav = NavigationContext(client)
        nav.run_interactive_session()

    except Exception as e:
        print(f"Error starting navigation: {str(e)}")
