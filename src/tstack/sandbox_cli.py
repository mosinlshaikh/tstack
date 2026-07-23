"""CLI for planning and running rootless Docker sandboxes."""
from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from tstack.container_sandbox import (
    PROFILES,
    create_sandbox_request,
    docker_command,
    execute_sandbox,
    receipt_json,
    request_json,
    verify_rootless_docker,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="tstack-sandbox", description="Rootless Docker sandbox runtime")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("doctor", help="Verify rootless Docker availability")
    sub.add_parser("profiles", help="List built-in sandbox profiles")

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("image")
    common.add_argument("--workspace", default=".")
    common.add_argument("--profile", choices=sorted(PROFILES), default="restricted")
    common.add_argument("--artifact", action="append", default=[])
    common.add_argument("--env", action="append", default=[])
    common.add_argument("--cmd", nargs=argparse.REMAINDER, required=True)

    sub.add_parser("plan", parents=[common], help="Emit the exact Docker execution plan")
    sub.add_parser("run", parents=[common], help="Execute the sandbox after rootless verification")
    return parser


def _environment(items: list[str]) -> dict[str, str]:
    result: dict[str, str] = {}
    for item in items:
        if "=" not in item:
            raise ValueError(f"environment value must be KEY=VALUE: {item}")
        key, value = item.split("=", 1)
        result[key] = value
    return result


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "doctor":
        print(json.dumps(verify_rootless_docker(), indent=2, sort_keys=True))
        return 0
    if args.command == "profiles":
        print(json.dumps({name: asdict(profile) for name, profile in PROFILES.items()}, indent=2, sort_keys=True))
        return 0

    command = tuple(item for item in args.cmd if item != "--")
    request = create_sandbox_request(
        image=args.image,
        command=command,
        workspace=Path(args.workspace),
        profile=args.profile,
        environment=_environment(args.env),
        artifact_paths=args.artifact,
    )
    if args.command == "plan":
        payload = {
            "request": json.loads(request_json(request)),
            "docker_command": list(docker_command(request)),
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0
    receipt = execute_sandbox(request)
    print(receipt_json(receipt), end="")
    return 0 if receipt.status == "succeeded" else 30


if __name__ == "__main__":
    raise SystemExit(main())
