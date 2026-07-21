"""Regression tests for tamper-evident release evidence bundles."""
from __future__ import annotations

import json

from tstack.evidence_bundle import build_evidence_bundle, bundle_json, verify_evidence_bundle
from tstack.evidence_cli import main


def test_evidence_bundle_is_deterministic_and_verifies(tmp_path) -> None:
    (tmp_path / "manifest.json").write_text('{"schema":"demo"}\n', encoding="utf-8")
    (tmp_path / "sbom.cdx.json").write_text('{"bomFormat":"CycloneDX"}\n', encoding="utf-8")
    first = build_evidence_bundle(tmp_path, repository="owner/repo", commit="a" * 40)
    second = build_evidence_bundle(tmp_path, repository="owner/repo", commit="a" * 40)
    assert first["merkle_root"] == second["merkle_root"]
    (tmp_path / "evidence-bundle.json").write_text(bundle_json(first), encoding="utf-8")
    assert verify_evidence_bundle(tmp_path).valid is True


def test_evidence_bundle_detects_file_tampering(tmp_path) -> None:
    target = tmp_path / "release-decision.json"
    target.write_text('{"verdict":"PASS"}\n', encoding="utf-8")
    bundle = build_evidence_bundle(tmp_path, repository="owner/repo", commit="b" * 40)
    (tmp_path / "evidence-bundle.json").write_text(bundle_json(bundle), encoding="utf-8")
    target.write_text('{"verdict":"HOLD"}\n', encoding="utf-8")
    result = verify_evidence_bundle(tmp_path)
    assert result.valid is False
    assert result.mismatched == ("release-decision.json",)


def test_evidence_cli_returns_10_on_verification_failure(tmp_path, capsys) -> None:
    (tmp_path / "audit.json").write_text("{}\n", encoding="utf-8")
    assert main(["create", str(tmp_path), "--repository", "owner/repo", "--commit", "c" * 40]) == 0
    (tmp_path / "audit.json").write_text('{"changed":true}\n', encoding="utf-8")
    assert main(["verify", str(tmp_path)]) == 10
    payload = json.loads(capsys.readouterr().out)
    assert payload["valid"] is False
