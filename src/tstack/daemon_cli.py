"""Foreground runtime daemon entry point."""

from __future__ import annotations

import sys

from tstack.cli import main


def daemon_main() -> int:
    return main(["daemon", "run", *sys.argv[1:]])


if __name__ == "__main__":
    raise SystemExit(daemon_main())
