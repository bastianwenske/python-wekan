# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

This project uses **uv** for modern Python package management. See the Makefile for comprehensive commands.

### Quick Start
- **Setup development**: `make setup` or `make quickstart`
- **Install dependencies**: `make install` (production) or `make install-dev` (development)
- **Run tests**: `make test` or `make test-all`
- **Code quality**: `make lint` and `make format`
- **CLI development**: `make cli` or `make cli-config`

### Dependencies & Environment
- **Package manager**: `uv` (modern, fast pip replacement)
- **Virtual environment**: `.venv` (managed by uv)
- **Lock file**: `uv.lock` (replaces requirements.txt)
- **Dependencies defined**: `pyproject.toml`

### Testing
- **Unit tests**: `make test`
- **With coverage**: `make test-cov`
- **CLI tests**: `make test-cli`
- **Integration tests**: `make test-integration`
- **All tests**: `make test-all`

### CLI Development
The CLI is integrated into the main project:
- **Install CLI**: `uv sync --extra cli` or `make install-dev`
- **Test CLI**: `uv run wekan --help` or `make cli-help`
- **Run CLI**: `uv run wekan navigate` or `make cli`
- **Configure**: `uv run wekan config init` or `make cli-config`
- **Status check**: `uv run wekan status` or `make cli-status`

### Pre-commit Hooks
- **Install hooks**: `make install-dev` (automatic) or `uv run pre-commit install`
- **Run hooks**: `make pre-commit`
- **Format code**: `make format`

## Architecture Overview

### Core Library Structure (`/wekan/`)
This is a Python client library for the WeKan REST API with object-oriented design:

#### Key Components
- **WekanClient** (`wekan_client.py`): Main entry point, handles authentication and token management
- **Base class** (`base.py`): Common functionality for all WeKan objects
- **Object hierarchy**: WekanClient → Board → List/Swimlane → Card → Comments/Checklists

#### Object Relationships
```
WekanClient
├── Board (board.py)
│   ├── WekanList (wekan_list.py)
│   │   └── Card (card.py)
│   ├── Swimlane (swimlane.py)
│   │   └── Card (card.py)
│   ├── Integration (integration.py)
│   ├── CustomField (customfield.py)
│   └── Label (label.py)
├── User (user.py)
└── Card components:
    ├── CardComment (card_comment.py)
    ├── CardChecklist (card_checklist.py)
    └── CardChecklistItem (card_checklist_item.py)
```

#### Authentication & Usage
- Uses username/password to obtain API tokens
- Tokens are automatically renewed when expired
- Environment variables: `WEKAN_USERNAME`, `WEKAN_PASSWORD`
- Base URL required for WeKan instance

### CLI Application (`/wekan/cli/`)
Integrated command-line interface built on top of the core library:
- Optional installation via `pip install python-wekan[cli]`
- Uses typer and rich for modern CLI experience
- Configuration via `.wekan` files or environment variables
- Entry point: `wekan` command

## Development Notes

### Dependencies
- **Core**: `requests`, `python-dateutil`, `certifi`, `urllib3`
- **CLI**: `typer`, `rich`, `pydantic` (optional)
- **Dev**: `pytest`, `pytest-cov`, `black`, `isort`, `mypy`, `ruff`, `pre-commit`
- **Package management**: `uv` with `pyproject.toml` and `uv.lock`

### Code Style
- Python 3.9+ required
- Type hints enabled (see `py.typed` marker)
- Pyright configuration in `pyproject.toml`

### Project Structure
- Main library: `/wekan/` - Core WeKan API client
- CLI tool: `/wekan/cli/` - Integrated command-line interface
- Tests: `/tests/` - Library and CLI tests
- Single `pyproject.toml` with optional CLI dependencies
