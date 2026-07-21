"""CLI for TStack's explainable decision brain."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from tstack.decision import build_plan_from_files, plan_json, plan_markdown


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="tstack-decide", description="Generate a human-approved remediation plan from scan evidence and learning memory.")
    parser.add_argument("scan", help="TStack JSON scan report")
    parser.add_argument("--memory", default=".tstack/learning-memory.json", help="Local learning-memory path")
    parser.add_argument("--limit", type=int, default=20, help="Maximum ranked actions")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    parser.add_argument("--output", "-o")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        plan = build_plan_from_files(Path(args.scan), Path(args.memory), limit=args.limit)
        content = plan_json(plan) if args.format == "json" else plan_markdown(plan)
        if args.output:
            destination = Path(args.output).expanduser().resolve()
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(content, encoding="utf-8")
            print(f"Written: {destination}")
        else:
            print(content, end="")
        return 0 if plan.verdict == "PASS" else 11
    except (FileNotFoundError, OSError, ValueError, KeyError) as exc:
        print(f"tstack-decide: error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
