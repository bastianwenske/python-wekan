"""
WeKan CLI module.

This module provides a command-line interface for the python-wekan library.
"""

# Optional CLI dependencies - only import if available
try:
    from .main import app, main  # noqa: F401

    __all__ = ["app", "main"]
except ImportError:
    # CLI dependencies not installed
    __all__ = []
