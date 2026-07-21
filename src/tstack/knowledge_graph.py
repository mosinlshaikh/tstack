"""Deterministic engineering knowledge graph and impact analysis for TStack."""
from __future__ import annotations

import ast
import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path

EXCLUDED = {".git", ".venv", "venv", "node_modules", "dist", "build", "__pycache__", ".pytest_cache"}
SOURCE_SUFFIXES = {".py", ".js", ".jsx", ".ts", ".tsx", ".go", ".rs", ".java", ".kt", ".php"}


@dataclass(frozen=True)
class GraphNode:
    id: str
    kind: str
    path: str


@dataclass(frozen=True)
class GraphEdge:
    source: str
    target: str
    relation: str


@dataclass(frozen=True)
class KnowledgeGraph:
    schema: str
    root: str
    fingerprint: str
    nodes: tuple[GraphNode, ...]
    edges: tuple[GraphEdge, ...]


@dataclass(frozen=True)
class ImpactResult:
    target: str
    impacted: tuple[str, ...]
    direct_dependents: tuple[str, ...]
    tests: tuple[str, ...]
    risk: str


def _files(root: Path) -> list[Path]:
    result: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file() or path.is_symlink():
            continue
        relative = path.relative_to(root)
        if any(part in EXCLUDED for part in relative.parts):
            continue
        if path.suffix.lower() in SOURCE_SUFFIXES or path.name in {"Dockerfile", "pyproject.toml", "package.json", "go.mod", "Cargo.toml"}:
            result.append(path)
    return sorted(result, key=lambda item: item.relative_to(root).as_posix())


def _kind(relative: str) -> str:
    lowered = relative.lower()
    name = Path(relative).name
    if "test" in lowered or lowered.startswith("tests/"):
        return "test"
    if name in {"Dockerfile", "pyproject.toml", "package.json", "go.mod", "Cargo.toml"} or name.endswith((".yml", ".yaml", ".json", ".toml")):
        return "config"
    return "source"


def _python_imports(path: Path) -> tuple[str, ...]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, SyntaxError):
        return ()
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return tuple(sorted(names))


def _module_candidates(relative: str) -> tuple[str, ...]:
    path = Path(relative)
    no_suffix = path.with_suffix("").as_posix()
    dotted = no_suffix.replace("/", ".")
    candidates = {dotted}
    if dotted.startswith("src."):
        candidates.add(dotted[4:])
    if dotted.endswith(".__init__"):
        candidates.add(dotted[:-9])
    return tuple(sorted(candidates))


def build_graph(project: Path) -> KnowledgeGraph:
    root = project.expanduser().resolve()
    if not root.is_dir():
        raise FileNotFoundError(f"project directory not found: {root}")
    paths = _files(root)
    nodes = [GraphNode(path.relative_to(root).as_posix(), _kind(path.relative_to(root).as_posix()), path.relative_to(root).as_posix()) for path in paths]
    module_index: dict[str, str] = {}
    for node in nodes:
        if Path(node.path).suffix == ".py":
            for candidate in _module_candidates(node.path):
                module_index[candidate] = node.id

    edges: set[GraphEdge] = set()
    for path in paths:
        relative = path.relative_to(root).as_posix()
        if path.suffix == ".py":
            for imported in _python_imports(path):
                target = module_index.get(imported)
                if not target:
                    target = next((value for key, value in module_index.items() if key.endswith(imported)), None)
                if target and target != relative:
                    edges.add(GraphEdge(relative, target, "imports"))
        if _kind(relative) == "test":
            stem = path.stem.removeprefix("test_").removesuffix("_test")
            for node in nodes:
                if node.kind == "source" and stem and stem in Path(node.path).stem:
                    edges.add(GraphEdge(relative, node.id, "tests"))

    digest = hashlib.sha256()
    for node in sorted(nodes, key=lambda item: item.id):
        digest.update(f"N\0{node.id}\0{node.kind}\n".encode())
    for edge in sorted(edges, key=lambda item: (item.source, item.target, item.relation)):
        digest.update(f"E\0{edge.source}\0{edge.target}\0{edge.relation}\n".encode())
    return KnowledgeGraph("tstack-knowledge-graph/v1", str(root), digest.hexdigest(), tuple(sorted(nodes, key=lambda item: item.id)), tuple(sorted(edges, key=lambda item: (item.source, item.target, item.relation))))


def impact_analysis(graph: KnowledgeGraph, target: str) -> ImpactResult:
    ids = {node.id for node in graph.nodes}
    if target not in ids:
        raise KeyError(f"graph node not found: {target}")
    reverse: dict[str, set[str]] = {}
    for edge in graph.edges:
        reverse.setdefault(edge.target, set()).add(edge.source)
    direct = sorted(reverse.get(target, set()))
    seen = {target}
    queue = list(direct)
    impacted: set[str] = set()
    while queue:
        current = queue.pop(0)
        if current in seen:
            continue
        seen.add(current)
        impacted.add(current)
        queue.extend(sorted(reverse.get(current, set())))
    tests = sorted(node for node in impacted if next((item.kind for item in graph.nodes if item.id == node), "") == "test")
    count = len(impacted)
    risk = "HIGH" if count >= 10 else "MEDIUM" if count >= 3 else "LOW"
    return ImpactResult(target, tuple(sorted(impacted)), tuple(direct), tuple(tests), risk)


def graph_json(graph: KnowledgeGraph) -> str:
    return json.dumps(asdict(graph), indent=2, sort_keys=True) + "\n"


def load_graph(path: Path) -> KnowledgeGraph:
    payload = json.loads(path.expanduser().resolve().read_text(encoding="utf-8"))
    if payload.get("schema") != "tstack-knowledge-graph/v1":
        raise ValueError("invalid TStack knowledge graph schema")
    return KnowledgeGraph(payload["schema"], payload["root"], payload["fingerprint"], tuple(GraphNode(**item) for item in payload["nodes"]), tuple(GraphEdge(**item) for item in payload["edges"]))


def impact_json(result: ImpactResult) -> str:
    return json.dumps(asdict(result), indent=2, sort_keys=True) + "\n"


def graph_dot(graph: KnowledgeGraph) -> str:
    lines = ["digraph tstack {", "  rankdir=LR;"]
    for node in graph.nodes:
        shape = "box" if node.kind == "source" else "ellipse" if node.kind == "test" else "diamond"
        safe = node.id.replace('"', '\\"')
        lines.append(f'  "{safe}" [shape={shape}];')
    for edge in graph.edges:
        lines.append(f'  "{edge.source}" -> "{edge.target}" [label="{edge.relation}"];')
    lines.append("}")
    return "\n".join(lines) + "\n"
