"""Standalone CLI for TStack's local learning memory."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from tstack.learning import apply_feedback, learn_findings, load_memory, recommendations, recommendations_json, save_memory


def _memory(project: str) -> Path:
    return Path(project).expanduser().resolve() / ".tstack" / "learning-memory.json"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="tstack-learn", description="Learn recurring engineering patterns from TStack scan evidence and human feedback.")
    sub = parser.add_subparsers(dest="command", required=True)

    item = sub.add_parser("ingest", help="Learn from a TStack JSON scan report")
    item.add_argument("report")
    item.add_argument("--project", default=".")

    item = sub.add_parser("feedback", help="Record a human decision for a learned finding")
    item.add_argument("rule_id")
    item.add_argument("--path")
    item.add_argument("--outcome", required=True, choices=("accepted", "rejected", "resolved"))
    item.add_argument("--project", default=".")

    item = sub.add_parser("recommend", help="Rank recurring findings using local memory")
    item.add_argument("--project", default=".")
    item.add_argument("--minimum-occurrences", type=int, default=2)
    item.add_argument("--output", "-o")

    args = parser.parse_args(argv)
    try:
        memory_path = _memory(args.project)
        memory = load_memory(memory_path)
        if args.command == "ingest":
            payload = json.loads(Path(args.report).expanduser().resolve().read_text(encoding="utf-8"))
            findings = payload.get("findings")
            if not isinstance(findings, list):
                raise ValueError("scan report requires a findings array")
            learn_findings(memory, findings)
            save_memory(memory_path, memory)
            print(f"Learned {len(findings)} findings into {memory_path}")
            return 0
        if args.command == "feedback":
            apply_feedback(memory, rule_id=args.rule_id, path=args.path, outcome=args.outcome)
            save_memory(memory_path, memory)
            print(f"Recorded {args.outcome}: {args.rule_id}")
            return 0
        content = recommendations_json(recommendations(memory, minimum_occurrences=args.minimum_occurrences))
        if args.output:
            destination = Path(args.output).expanduser().resolve()
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(content, encoding="utf-8")
            print(f"Written: {destination}")
        else:
            print(content, end="")
        return 0
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"tstack-learn: error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
