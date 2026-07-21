"""Regression tests for the end-to-end release trust gate."""

from __future__ import annotations

import json

from tstack.cli import main
from tstack.supplychain import build_manifest, checksums_text, manifest_json
from tstack.trustgate import evaluate_release_trust

COMMIT = "a" * 40
REPOSITORY = "mosinlshaikh/tstack"
WORKFLOW = ".github/workflows/release.yml"


def _release_bundle(root) -> None:
    (root / "package.whl").write_bytes(b"trusted artifact")
    (root / "sbom.cdx.json").write_text('{"bomFormat":"CycloneDX"}\n', encoding="utf-8")
    manifest = build_manifest(root)
    (root / "manifest.json").write_text(manifest_json(manifest), encoding="utf-8")
    (root / "checksums.sha256").write_text(checksums_text(manifest, "sha256"), encoding="utf-8")
    (root / "checksums.sha3-256").write_text(checksums_text(manifest, "sha3-256"), encoding="utf-8")


def _valid_receipt() -> dict:
    return {
        "schema": "tstack-attestation-receipt/v1",
        "verified": True,
        "artifact": "package.whl",
        "repository": REPOSITORY,
        "workflow": WORKFLOW,
        "source_digest": COMMIT,
        "deny_self_hosted_runners": True,
        "verification_results": [{"verified": True}],
    }


def test_trust_gate_passes_complete_bundle(tmp_path) -> None:
    _release_bundle(tmp_path)
    result = evaluate_release_trust(
        tmp_path,
        repository=REPOSITORY,
        workflow=WORKFLOW,
        commit=COMMIT,
    )
    assert result.passed is True
    assert result.verdict == "PASS"
    assert all(item.passed for item in result.checks)


def test_trust_gate_holds_when_sbom_missing(tmp_path) -> None:
    _release_bundle(tmp_path)
    (tmp_path / "sbom.cdx.json").unlink()
    result = evaluate_release_trust(
        tmp_path,
        repository=REPOSITORY,
        workflow=WORKFLOW,
        commit=COMMIT,
    )
    assert result.passed is False
    assert result.verdict == "HOLD"


def test_attestation_receipt_can_be_required(tmp_path) -> None:
    _release_bundle(tmp_path)
    result = evaluate_release_trust(
        tmp_path,
        repository=REPOSITORY,
        workflow=WORKFLOW,
        commit=COMMIT,
        require_attestation_receipt=True,
    )
    assert result.passed is False
    (tmp_path / "attestation-verification.json").write_text(
        json.dumps(_valid_receipt()) + "\n",
        encoding="utf-8",
    )
    result = evaluate_release_trust(
        tmp_path,
        repository=REPOSITORY,
        workflow=WORKFLOW,
        commit=COMMIT,
        require_attestation_receipt=True,
    )
    assert result.passed is True


def test_cli_returns_exit_six_on_trust_hold(tmp_path, capsys) -> None:
    _release_bundle(tmp_path)
    (tmp_path / "checksums.sha3-256").unlink()
    code = main([
        "trust-gate", str(tmp_path),
        "--repository", REPOSITORY,
        "--commit", COMMIT,
        "--format", "json",
    ])
    payload = json.loads(capsys.readouterr().out)
    assert code == 6
    assert payload["verdict"] == "HOLD"


def test_invalid_commit_identity_is_rejected(tmp_path) -> None:
    _release_bundle(tmp_path)
    try:
        evaluate_release_trust(
            tmp_path,
            repository=REPOSITORY,
            workflow=WORKFLOW,
            commit="short",
        )
    except ValueError as exc:
        assert "40-character" in str(exc)
    else:
        raise AssertionError("invalid commit identity must fail")
