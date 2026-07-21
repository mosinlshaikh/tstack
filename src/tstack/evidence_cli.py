"""CLI for TStack release evidence bundles."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from tstack.evidence_bundle import build_evidence_bundle, bundle_json, verification_json, verify_evidence_bundle


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="tstack-evidence", description="Create and verify tamper-evident TStack evidence bundles.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    create = subparsers.add_parser("create", help="Create evidence-bundle.json and its Merkle root")
    create.add_argument("path", nargs="?", default="dist")
    create.add_argument("--repository", required=True)
    create.add_argument("--commit", required=True)
    create.add_argument("--output", "-o")

    verify = subparsers.add_parser("verify", help="Verify every evidence file and the Merkle root")
    verify.add_argument("path", nargs="?", default="dist")
    verify.add_argument("--bundle")
    verify.add_argument("--output", "-o")
    return parser


def _write(content: str, destination: str | None) -> None:
    if destination is None:
        print(content, end="")
        return
    path = Path(destination).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    # Keep stdout reserved for JSON so callers can parse it deterministically.
    print(f"Written: {path}", file=sys.stderr)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        root = Path(args.path).expanduser().resolve()
        if args.command == "create":
            target = args.output or str(root / "evidence-bundle.json")
            _write(bundle_json(build_evidence_bundle(root, repository=args.repository, commit=args.commit)), target)
            return 0
        result = verify_evidence_bundle(root, Path(args.bundle) if args.bundle else None)
        _write(verification_json(result), args.output)
        return 0 if result.valid else 10
    except (FileNotFoundError, OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"tstack-evidence: error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
