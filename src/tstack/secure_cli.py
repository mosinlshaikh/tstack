"""CLI for cryptographically authorized TStack execution paths."""
from __future__ import annotations

import argparse
import base64
import json
from dataclasses import asdict
from pathlib import Path

from tstack.sandbox import load_sandbox_policy
from tstack.secure_execution import execute_signed_file_plan, execute_signed_sandbox


def _public_key(path: Path) -> bytes:
    raw = path.expanduser().resolve().read_bytes()
    if len(raw) == 32:
        return raw
    try:
        decoded = base64.b64decode(raw.strip(), validate=True)
    except ValueError as exc:
        raise ValueError("public key must be 32 raw bytes or base64") from exc
    if len(decoded) != 32:
        raise ValueError("Ed25519 public key must decode to 32 bytes")
    return decoded


def _emit(receipt, output: str | None) -> None:
    text = json.dumps(asdict(receipt), indent=2, sort_keys=True) + "\n"
    if output:
        target = Path(output).expanduser().resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
    else:
        print(text, end="")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="tstack-secure", description="Signed, exact-payload TStack execution")
    sub = parser.add_subparsers(dest="command", required=True)

    sandbox = sub.add_parser("sandbox-run", help="Run an exact signed process.run request")
    sandbox.add_argument("policy")
    sandbox.add_argument("request")
    sandbox.add_argument("approval")
    sandbox.add_argument("public_key")
    sandbox.add_argument("store")
    sandbox.add_argument("--cwd")
    sandbox.add_argument("--write", action="store_true")
    sandbox.add_argument("--network", action="store_true")
    sandbox.add_argument("--output", "-o")
    sandbox.add_argument("--cmd", nargs=argparse.REMAINDER, required=True)

    files = sub.add_parser("file-run", help="Apply an exact signed filesystem.move plan")
    files.add_argument("plan")
    files.add_argument("request")
    files.add_argument("approval")
    files.add_argument("public_key")
    files.add_argument("store")
    files.add_argument("--apply", action="store_true", help="Apply moves; default is dry-run")
    files.add_argument("--manifest")
    files.add_argument("--output", "-o")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    key = _public_key(Path(args.public_key))
    if args.command == "sandbox-run":
        command = tuple(part for part in args.cmd if part != "--")
        receipt = execute_signed_sandbox(
            load_sandbox_policy(Path(args.policy)), command,
            request_path=Path(args.request), approval_path=Path(args.approval),
            public_key_raw=key, store_path=Path(args.store),
            cwd=Path(args.cwd) if args.cwd else None, write=args.write, network=args.network,
        )
        _emit(receipt, args.output)
        return 0 if receipt.status == "succeeded" else 20
    receipt = execute_signed_file_plan(
        Path(args.plan), request_path=Path(args.request), approval_path=Path(args.approval),
        public_key_raw=key, store_path=Path(args.store), dry_run=not args.apply,
        manifest=Path(args.manifest) if args.manifest else None,
    )
    _emit(receipt, args.output)
    return 0 if receipt.status == "succeeded" else 21


if __name__ == "__main__":
    raise SystemExit(main())
