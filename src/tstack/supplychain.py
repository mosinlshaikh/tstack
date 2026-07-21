"""Supply-chain metadata, checksums, SBOM, and release verification for TStack."""

from __future__ import annotations

import hashlib
import json
import sys
from dataclasses import asdict, dataclass
from importlib import metadata
from pathlib import Path


@dataclass(frozen=True)
class ArtifactRecord:
    path: str
    size: int
    sha256: str


@dataclass(frozen=True)
class VerificationResult:
    valid: bool
    checked: int
    missing: tuple[str, ...]
    mismatched: tuple[str, ...]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_manifest(directory: Path) -> dict:
    root = directory.expanduser().resolve()
    if not root.is_dir():
        raise FileNotFoundError(f"artifact directory not found: {root}")
    artifacts = []
    for path in sorted(root.iterdir()):
        if path.is_file() and path.name not in {"manifest.json", "checksums.sha256"}:
            artifacts.append(ArtifactRecord(path.name, path.stat().st_size, _sha256(path)))
    if not artifacts:
        raise ValueError(f"no release artifacts found in: {root}")
    return {
        "schema": "tstack-release-manifest/v1",
        "python": sys.version.split()[0],
        "artifacts": [asdict(item) for item in artifacts],
    }


def manifest_json(manifest: dict) -> str:
    return json.dumps(manifest, indent=2, sort_keys=True) + "\n"


def checksums_text(manifest: dict) -> str:
    return "".join(f"{item['sha256']}  {item['path']}\n" for item in manifest["artifacts"])


def verify_manifest(directory: Path, manifest_path: Path | None = None) -> VerificationResult:
    root = directory.expanduser().resolve()
    source = (manifest_path or (root / "manifest.json")).expanduser().resolve()
    payload = json.loads(source.read_text(encoding="utf-8"))
    if payload.get("schema") != "tstack-release-manifest/v1" or not isinstance(payload.get("artifacts"), list):
        raise ValueError("invalid TStack release manifest schema")
    missing, mismatched = [], []
    for item in payload["artifacts"]:
        target = root / item["path"]
        if not target.is_file():
            missing.append(item["path"])
        elif _sha256(target) != item["sha256"] or target.stat().st_size != item["size"]:
            mismatched.append(item["path"])
    return VerificationResult(not missing and not mismatched, len(payload["artifacts"]), tuple(missing), tuple(mismatched))


def sbom_document() -> dict:
    components = []
    for dist in sorted(metadata.distributions(), key=lambda item: (item.metadata.get("Name") or "").lower()):
        name = dist.metadata.get("Name")
        if not name:
            continue
        components.append({"type": "library", "name": name, "version": dist.version, "purl": f"pkg:pypi/{name.lower()}@{dist.version}"})
    return {
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "version": 1,
        "metadata": {"component": {"type": "application", "name": "ttrl-tstack"}},
        "components": components,
    }


def sbom_json() -> str:
    return json.dumps(sbom_document(), indent=2, sort_keys=True) + "\n"
