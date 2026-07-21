from __future__ import annotations

import json

from tstack.supplychain import build_manifest, checksums_text, verify_manifest


def test_manifest_contains_sha256_and_sha3_256(tmp_path) -> None:
    (tmp_path / "artifact.whl").write_bytes(b"release-bytes")
    manifest = build_manifest(tmp_path)
    record = manifest["artifacts"][0]
    assert manifest["schema"] == "tstack-release-manifest/v2"
    assert len(record["sha256"]) == 64
    assert len(record["sha3_256"]) == 64
    assert record["sha256"] != record["sha3_256"]
    assert "artifact.whl" in checksums_text(manifest, "sha256")
    assert "artifact.whl" in checksums_text(manifest, "sha3-256")


def test_either_hash_mismatch_fails_verification(tmp_path) -> None:
    artifact = tmp_path / "artifact.whl"
    artifact.write_bytes(b"release-bytes")
    manifest = build_manifest(tmp_path)
    manifest["artifacts"][0]["sha3_256"] = "0" * 64
    (tmp_path / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    result = verify_manifest(tmp_path)
    assert result.valid is False
    assert result.mismatched == ("artifact.whl",)
