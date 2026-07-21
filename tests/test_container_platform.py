"""Regression tests for Docker and Kubernetes platform auditing."""
from __future__ import annotations

from tstack.cli import main
from tstack.container_platform import audit_platform


def test_insecure_dockerfile_is_flagged(tmp_path) -> None:
    (tmp_path / "Dockerfile").write_text("FROM python:latest\nCOPY . /app\nCMD [\"python\", \"app.py\"]\n", encoding="utf-8")
    report = audit_platform(tmp_path)
    rules = {item.rule_id for item in report.findings}
    assert report.docker_detected is True
    assert {"DOCKER001", "DOCKER002", "DOCKER003", "DOCKER008"}.issubset(rules)


def test_secure_dockerfile_can_pass(tmp_path) -> None:
    (tmp_path / ".dockerignore").write_text(".git\n.env\n", encoding="utf-8")
    (tmp_path / "Dockerfile").write_text(
        "FROM python:3.12@sha256:" + "a" * 64 + " AS build\n"
        "WORKDIR /app\nCOPY pyproject.toml .\n"
        "FROM python:3.12@sha256:" + "b" * 64 + "\n"
        "RUN useradd --uid 10001 app\nUSER 10001\nHEALTHCHECK CMD [\"python\", \"-c\", \"print(1)\"]\nCOPY --from=build /app /app\n",
        encoding="utf-8",
    )
    report = audit_platform(tmp_path)
    assert not any(item.severity in {"critical", "high"} for item in report.findings if item.rule_id.startswith("DOCKER"))


def test_insecure_kubernetes_workload_is_flagged(tmp_path) -> None:
    k8s = tmp_path / "k8s"
    k8s.mkdir()
    (k8s / "deployment.yaml").write_text(
        "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: demo\nspec:\n  template:\n    spec:\n      containers:\n        - name: app\n          image: demo:latest\n          securityContext:\n            privileged: true\n",
        encoding="utf-8",
    )
    report = audit_platform(tmp_path)
    rules = {item.rule_id for item in report.findings}
    assert report.kubernetes_detected is True
    assert report.verdict == "HOLD"
    assert {"K8S001", "K8S002", "K8S003", "K8S006", "K8S009", "K8S011"}.issubset(rules)


def test_platform_cli_exit_contract(tmp_path, capsys) -> None:
    (tmp_path / "Dockerfile").write_text("FROM alpine:latest\n", encoding="utf-8")
    assert main(["platform-audit", str(tmp_path), "--format", "json", "--fail-on", "review"]) == 9
    assert '"verdict"' in capsys.readouterr().out
