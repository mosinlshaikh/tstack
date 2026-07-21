"""Regression tests for the Engineering Knowledge Graph."""
from __future__ import annotations

import json

from tstack.graph_cli import main
from tstack.knowledge_graph import build_graph, impact_analysis


def _project(root) -> None:
    package = root / "src" / "demo"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text("", encoding="utf-8")
    (package / "core.py").write_text("def run(): return 1\n", encoding="utf-8")
    (package / "api.py").write_text("from demo.core import run\n", encoding="utf-8")
    tests = root / "tests"
    tests.mkdir()
    (tests / "test_api.py").write_text("from demo.api import run\n\ndef test_run(): assert run() == 1\n", encoding="utf-8")


def test_graph_is_deterministic_and_links_imports(tmp_path) -> None:
    _project(tmp_path)
    first = build_graph(tmp_path)
    second = build_graph(tmp_path)
    assert first.fingerprint == second.fingerprint
    edges = {(item.source, item.target, item.relation) for item in first.edges}
    assert ("src/demo/api.py", "src/demo/core.py", "imports") in edges
    assert ("tests/test_api.py", "src/demo/api.py", "imports") in edges


def test_impact_finds_transitive_dependents_and_tests(tmp_path) -> None:
    _project(tmp_path)
    result = impact_analysis(build_graph(tmp_path), "src/demo/core.py")
    assert "src/demo/api.py" in result.impacted
    assert "tests/test_api.py" in result.impacted
    assert result.tests == ("tests/test_api.py",)


def test_graph_cli_build_and_summary_emit_json(tmp_path, capsys) -> None:
    _project(tmp_path)
    graph_path = tmp_path / ".tstack" / "knowledge-graph.json"
    assert main(["build", str(tmp_path)]) == 0
    assert graph_path.is_file()
    assert main(["summary", "--graph", str(graph_path)]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["nodes"] >= 4
    assert payload["edges"] >= 2
