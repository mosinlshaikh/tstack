"""CLI for the TStack Engineering Knowledge Graph."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from tstack.knowledge_graph import build_graph, graph_dot, graph_json, impact_analysis, impact_json, load_graph


def _write(content: str, output: str | None) -> None:
    if output is None:
        print(content, end="")
        return
    target = Path(output).expanduser().resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    print(f"Written: {target}", file=sys.stderr)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="tstack-graph", description="Build and query the TStack Engineering Knowledge Graph.")
    commands = parser.add_subparsers(dest="command", required=True)

    item = commands.add_parser("build", help="Build a deterministic project graph")
    item.add_argument("project", nargs="?", default=".")
    item.add_argument("--output", "-o")

    item = commands.add_parser("impact", help="Calculate reverse dependency impact")
    item.add_argument("target")
    item.add_argument("--graph", default=".tstack/knowledge-graph.json")
    item.add_argument("--output", "-o")

    item = commands.add_parser("dot", help="Export Graphviz DOT")
    item.add_argument("--graph", default=".tstack/knowledge-graph.json")
    item.add_argument("--output", "-o")

    item = commands.add_parser("summary", help="Show graph summary as JSON")
    item.add_argument("--graph", default=".tstack/knowledge-graph.json")
    item.add_argument("--output", "-o")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "build":
            graph = build_graph(Path(args.project))
            output = args.output or str(Path(args.project).expanduser().resolve() / ".tstack" / "knowledge-graph.json")
            _write(graph_json(graph), output)
            return 0
        graph = load_graph(Path(args.graph))
        if args.command == "impact":
            _write(impact_json(impact_analysis(graph, args.target)), args.output)
        elif args.command == "dot":
            _write(graph_dot(graph), args.output)
        else:
            payload = {"schema": graph.schema, "fingerprint": graph.fingerprint, "nodes": len(graph.nodes), "edges": len(graph.edges), "node_kinds": {kind: sum(1 for node in graph.nodes if node.kind == kind) for kind in sorted({node.kind for node in graph.nodes})}}
            _write(json.dumps(payload, indent=2, sort_keys=True) + "\n", args.output)
        return 0
    except (FileNotFoundError, OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"tstack-graph: error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
