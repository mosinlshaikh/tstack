"""Regression tests for the single-command release orchestrator."""
from __future__ import annotations

from types import SimpleNamespace

from tstack import release_orchestrator as module


def _patch_stages(monkeypatch, *, policy=True, manifest=True, repro=True, trust=True):
    monkeypatch.setattr(module, "scan_project", lambda path: object())
    monkeypatch.setattr(module, "load_policy", lambda path: object())
    monkeypatch.setattr(module, "evaluate_policy", lambda report, policy: SimpleNamespace(passed=policy, active_findings=(), suppressed_findings=()))
    monkeypatch.setattr(module, "verify_manifest", lambda path: SimpleNamespace(valid=manifest, checked=2, missing=(), mismatched=()))
    records = (SimpleNamespace(reproducible=repro),)
    monkeypatch.setattr(module, "compare_builds", lambda left, right: SimpleNamespace(passed=repro, checked=1, records=records, missing_original=(), missing_rebuilt=()))
    monkeypatch.setattr(module, "evaluate_release_trust", lambda *args, **kwargs: SimpleNamespace(passed=trust, verdict="PASS" if trust else "HOLD"))


def test_release_decision_passes_only_when_all_stages_pass(monkeypatch, tmp_path) -> None:
    _patch_stages(monkeypatch)
    result = module.evaluate_release(tmp_path, tmp_path, tmp_path, repository="owner/repo", workflow=".github/workflows/release.yml", commit="a" * 40)
    assert result.passed is True
    assert result.verdict == "PASS"
    assert all(stage.passed for stage in result.stages)


def test_release_decision_holds_on_reproducibility_failure(monkeypatch, tmp_path) -> None:
    _patch_stages(monkeypatch, repro=False)
    result = module.evaluate_release(tmp_path, tmp_path, tmp_path, repository="owner/repo", workflow=".github/workflows/release.yml", commit="b" * 40)
    assert result.passed is False
    assert result.verdict == "HOLD"
    assert next(stage for stage in result.stages if stage.name == "reproducible-build").passed is False
