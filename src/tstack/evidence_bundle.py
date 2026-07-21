"""Tamper-evident release evidence bundles using canonical dual hashes and a Merkle root."""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path

EXCLUDED = {"evidence-bundle.json", "evidence-verification.json"}


@dataclass(frozen=True)
class EvidenceRecord:
    path: str
    size: int
    sha256: str
    sha3_256: str


@dataclass(frozen=True)
class EvidenceVerification:
    valid: bool
    checked: int
    missing: tuple[str, ...]
    mismatched: tuple[str, ...]
    merkle_valid: bool
    expected_root: str
    actual_root: str


def _digest(path: Path, algorithm: str) -> str:
    value = hashlib.new(algorithm)
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def _merkle_root(records: list[EvidenceRecord]) -> str:
    if not records:
        raise ValueError("evidence bundle requires at least one file")
    nodes = [hashlib.sha3_256(f"{item.path}\0{item.sha3_256}".encode()).digest() for item in records]
    while len(nodes) > 1:
        if len(nodes) % 2:
            nodes.append(nodes[-1])
        nodes = [hashlib.sha3_256(nodes[index] + nodes[index + 1]).digest() for index in range(0, len(nodes), 2)]
    return nodes[0].hex()


def build_evidence_bundle(directory: Path, *, repository: str, commit: str) -> dict:
    root = directory.expanduser().resolve()
    if not root.is_dir():
        raise FileNotFoundError(f"evidence directory not found: {root}")
    records: list[EvidenceRecord] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.is_symlink() or path.name in EXCLUDED:
            continue
        relative = path.relative_to(root).as_posix()
        records.append(EvidenceRecord(relative, path.stat().st_size, _digest(path, "sha256"), _digest(path, "sha3_256")))
    return {
        "schema": "tstack-evidence-bundle/v1",
        "repository": repository,
        "commit": commit.lower(),
        "algorithms": ["sha256", "sha3-256", "sha3-256-merkle"],
        "merkle_root": _merkle_root(records),
        "files": [asdict(item) for item in records],
    }


def bundle_json(bundle: dict) -> str:
    return json.dumps(bundle, indent=2, sort_keys=True) + "\n"


def verify_evidence_bundle(directory: Path, bundle_path: Path | None = None) -> EvidenceVerification:
    root = directory.expanduser().resolve()
    source = (bundle_path or root / "evidence-bundle.json").expanduser().resolve()
    payload = json.loads(source.read_text(encoding="utf-8"))
    if payload.get("schema") != "tstack-evidence-bundle/v1" or not isinstance(payload.get("files"), list):
        raise ValueError("invalid TStack evidence bundle schema")
    missing: list[str] = []
    mismatched: list[str] = []
    records: list[EvidenceRecord] = []
    for item in payload["files"]:
        record = EvidenceRecord(str(item["path"]), int(item["size"]), str(item["sha256"]), str(item["sha3_256"]))
        records.append(record)
        target = root / record.path
        if not target.is_file():
            missing.append(record.path)
        elif target.stat().st_size != record.size or _digest(target, "sha256") != record.sha256 or _digest(target, "sha3_256") != record.sha3_256:
            mismatched.append(record.path)
    actual_root = _merkle_root(records)
    expected_root = str(payload.get("merkle_root", ""))
    merkle_valid = actual_root == expected_root
    valid = not missing and not mismatched and merkle_valid
    return EvidenceVerification(valid, len(records), tuple(missing), tuple(mismatched), merkle_valid, expected_root, actual_root)


def verification_json(result: EvidenceVerification) -> str:
    return json.dumps(asdict(result), indent=2, sort_keys=True) + "\n"
