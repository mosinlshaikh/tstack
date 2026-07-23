"""Command line interface for the local TStack runtime daemon."""
from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from tstack.capability_broker import bootstrap_broker
from tstack.runtime_daemon import DaemonConfig, RuntimeDaemon, read_daemon_status, request_daemon_stop
from tstack.task_runtime import list_tasks, request_cancellation, submit_task, task_json


def _json_object(value: str) -> dict[str, Any]:
    try:
        payload = json.loads(value)
    except json.JSONDecodeError as exc:
        raise argparse.ArgumentTypeError(f"invalid JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise argparse.ArgumentTypeError("parameters must be a JSON object")
    return payload


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="tstackd", description="TStack persistent local runtime daemon")
    parser.add_argument("--database", default=".tstack/runtime/tasks.db")
    parser.add_argument("--state-dir", default=".tstack/runtime/daemon")
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="Run the daemon in the foreground")
    run.add_argument("--workers", type=int, default=1)
    run.add_argument("--poll", type=float, default=0.25)
    run.add_argument("--lease", type=int, default=30)
    run.add_argument("--heartbeat", type=float, default=5.0)
    run.add_argument("--idle-exit", type=float)

    sub.add_parser("status", help="Read the durable daemon status record")
    sub.add_parser("stop", help="Request graceful daemon shutdown")
    sub.add_parser("capabilities", help="List broker-registered capabilities")

    submit = sub.add_parser("submit", help="Submit a persistent logical task")
    submit.add_argument("capability")
    submit.add_argument("intent")
    submit.add_argument("--workspace", default="default")
    submit.add_argument("--parameters", type=_json_object, default={})
    submit.add_argument("--priority", type=int, default=0)
    submit.add_argument("--max-attempts", type=int, default=1)

    tasks = sub.add_parser("tasks", help="List persistent tasks")
    tasks.add_argument("--state")
    tasks.add_argument("--limit", type=int, default=100)

    cancel = sub.add_parser("cancel", help="Request task cancellation")
    cancel.add_argument("task_id")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    database = Path(args.database)
    state_dir = Path(args.state_dir)
    broker = bootstrap_broker()

    if args.command == "run":
        daemon = RuntimeDaemon(
            DaemonConfig(
                database=database,
                state_directory=state_dir,
                worker_count=args.workers,
                poll_interval_seconds=args.poll,
                lease_seconds=args.lease,
                heartbeat_interval_seconds=args.heartbeat,
                idle_exit_seconds=args.idle_exit,
            ),
            lambda task: asdict(broker.dispatch(task)),
        )
        print(json.dumps(asdict(daemon.run()), indent=2, sort_keys=True))
        return 0

    if args.command == "status":
        try:
            status = read_daemon_status(state_dir)
        except FileNotFoundError:
            print(json.dumps({"schema": "tstack-daemon-status/v1", "state": "NOT_STARTED"}, sort_keys=True))
            return 3
        print(json.dumps(asdict(status), indent=2, sort_keys=True))
        return 0 if status.state == "RUNNING" else 4

    if args.command == "stop":
        print(request_daemon_stop(state_dir))
        return 0

    if args.command == "capabilities":
        print(json.dumps([asdict(item) for item in broker.definitions()], indent=2, sort_keys=True))
        return 0

    if args.command == "submit":
        task = submit_task(
            database,
            workspace_id=args.workspace,
            capability=args.capability,
            intent=args.intent,
            parameters=args.parameters,
            priority=args.priority,
            max_attempts=args.max_attempts,
        )
        print(task_json(task), end="")
        return 0

    if args.command == "tasks":
        records = list_tasks(database, state=args.state, limit=args.limit)
        print(json.dumps([asdict(item) for item in records], indent=2, sort_keys=True))
        return 0

    task = request_cancellation(database, args.task_id)
    print(task_json(task), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
