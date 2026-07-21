"""Tests for reproducible build and provenance verification flows."""

from __future__ import annotations

import json
from pathlib import Path

from tstack.reproducibility import compare_builds
from tstack.trustgate import evaluate_release_trust
from tstack.supplychain import build_manifest, checksums_text, manifest_json


def _release_bundle(root: Path) -> None:
    (root / "pkg-1.0.0-py3-none-any.whl").write_bytes(b"artifact")
    (root / "sbom.cdx.json").write_text('{"bomFormat":"CycloneDX"}\n', encoding="utf-8")
    manifest = build_manifest(root)
    (root / "manifest.json").write_text(manifest_json(manifest), encoding="utf-8")
    (root / "checksums.sha256").write_text(checksums_text(manifest, "sha256"), encoding="utf-8")
    (root / "checksums.sha3-256").write_text(checksums_text(manifest, "sha3-256"), encoding="utf-8")


def test_reproducible_artifacts_pass(tmp_path) -> None:
    original = tmp_path / "official"
    rebuilt = tmp_path / "rebuilt"
    original.mkdir(); rebuilt.mkdir()
    (original / "pkg.whl").write_bytes(b"same")
    (rebuilt / "pkg.whl").write_bytes(b"same")
    result = compare_builds(original, rebuilt)
    assert result.passed is True
    assert result.records[0].reproducible is True


def test_reproducible_artifacts_detect_mismatch(tmp_path) -> None:
    original = tmp_path / "official"
    rebuilt = tmp_path / "rebuilt"
    original.mkdir(); rebuilt.mkdir()
    (original / "pkg.whl").write_bytes(b"one")
    (rebuilt / "pkg.whl").write_bytes(b"two")
    assert compare_builds(original, rebuilt).passed is False


def test_trust_gate_validates_receipt_identity(tmp_path) -> None:
    _release_bundle(tmp_path)
    receipt = {
        "schema": "tstack-attestation-receipt/v1",
        "verified": True,
        "artifact": "pkg-1.0.0-py3-none-any.whl",
        "repository": "mosinlshaikh/tstack",
        "workflow": ".github/workflows/release.yml",
        "verification_results": [{"verificationResult": {}}],
    }
    (tmp_path / "attestation-verification.json").write_text(json.dumps(receipt), encoding="utf-8")
    result = evaluate_release_trust(
        tmp_path,
        repository="mosinlshaikh/tstack",
        workflow=".github/workflows/release.yml",
        commit="a" * 40,
        require_attestation_receipt=True,
    )
    assert result.passed is True


def test_trust_gate_rejects_wrong_receipt_repository(tmp_path) -> None:
    _release_bundle(tmp_path)
    receipt = {
        "schema": "tstack-attestation-receipt/v1",
        "verified": True,
        "artifact": "pkg-1.0.0-py3-none-any.whl",
        "repository": "attacker/repo",
        "workflow": ".github/workflows/release.yml",
        "verification_results": [{"verificationResult": {}}],
    }
    (tmp_path / "attestation-verification.json").write_text(json.dumps(receipt), encoding="utf-8")
    result = evaluate_release_trust(
        tmp_path,
        repository="mosinlshaikh/tstack",
        workflow=".github/workflows/release.yml",
        commit="a" * 40,
        require_attestation_receipt=True,
    )
    assert result.passed is False
