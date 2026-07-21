"""Supply-chain regression tests."""

from __future__ import annotations

import json

from tstack.cli import main
from tstack.supplychain import build_manifest, checksums_text, verify_manifest


def test_manifest_is_deterministic_and_verifiable(tmp_path) -> None:
    (tmp_path / "a.whl").write_bytes(b"wheel")
    (tmp_path / "b.tar.gz").write_bytes(b"source")
    first = build_manifest(tmp_path)
    second = build_manifest(tmp_path)
    assert first == second
    assert [item["path"] for item in first["artifacts"]] == ["a.whl", "b.tar.gz"]
    (tmp_path / "manifest.json").write_text(json.dumps(first), encoding="utf-8")
    result = verify_manifest(tmp_path)
    assert result.valid is True
    assert result.checked == 2


def test_verify_detects_tampering(tmp_path) -> None:
    artifact = tmp_path / "a.whl"
    artifact.write_bytes(b"original")
    manifest = build_manifest(tmp_path)
    (tmp_path / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    artifact.write_bytes(b"tampered")
    result = verify_manifest(tmp_path)
    assert result.valid is False
    assert result.mismatched == ("a.whl",)


def test_checksums_use_sha256sum_format(tmp_path) -> None:
    (tmp_path / "package.whl").write_bytes(b"content")
    text = checksums_text(build_manifest(tmp_path))
    digest, filename = text.strip().split("  ")
    assert len(digest) == 64
    assert filename == "package.whl"


def test_cli_manifest_and_verify_exit_contract(tmp_path, capsys) -> None:
    (tmp_path / "package.whl").write_bytes(b"content")
    assert main(["manifest", str(tmp_path), "--checksums"]) == 0
    capsys.readouterr()
    assert (tmp_path / "manifest.json").is_file()
    assert (tmp_path / "checksums.sha256").is_file()
    assert main(["verify", str(tmp_path)]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["valid"] is True


def test_sbom_is_cyclonedx_json(tmp_path, capsys) -> None:
    output = tmp_path / "sbom.json"
    assert main(["sbom", "--output", str(output)]) == 0
    capsys.readouterr()
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["bomFormat"] == "CycloneDX"
    assert payload["specVersion"] == "1.5"
    assert isinstance(payload["components"], list)
