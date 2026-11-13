"""Backward-compatible entry point for document inspection."""

from .cli import main


if __name__ == "__main__":
    raise SystemExit(main(["inspect-document"]))
