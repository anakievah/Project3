#!/usr/bin/env python3
from __future__ import annotations

from .engine import run, welcome


def main() -> None:
    """Console entry point for the primitive DB project."""
    welcome()
    run()


if __name__ == "__main__":
    main()
