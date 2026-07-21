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
    sha3_256: str


@dataclass(frozen=True)
class VerificationResult:
    valid: bool
    checked: int
    missing: tuple[str, ...]
    mismatched: tuple[str, ...]


def _digest(path: Path, algorithm: str) -> str:
    digest = hashlib.new(algorithm)
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_manifest(directory: Path) -> dict:
    root = directory.expanduser().resolve()
    if not root.is_dir():
        raise FileNotFoundError(f"artifact directory not found: {root}")
    excluded = {"manifest.json", "checksums.sha256", "checksums.sha3-256"}
    artifacts = []
    for path in sorted(root.iterdir()):
        if path.is_file() and path.name not in excluded:
            artifacts.append(ArtifactRecord(path.name, path.stat().st_size, _digest(path, "sha256"), _digest(path, "sha3_256")))
    if not artifacts:
        raise ValueError(f"no release artifacts found in: {root}")
    return {
        "schema": "tstack-release-manifest/v2",
        "python": sys.version.split()[0],
        "algorithms": ["sha256", "sha3-256"],
        "artifacts": [asdict(item) for item in artifacts],
    }


def manifest_json(manifest: dict) -> str:
    return json.dumps(manifest, indent=2, sort_keys=True) + "\n"


def checksums_text(manifest: dict, algorithm: str = "sha256") -> str:
    field = {"sha256": "sha256", "sha3-256": "sha3_256"}.get(algorithm)
    if field is None:
        raise ValueError(f"unsupported checksum algorithm: {algorithm}")
    return "".join(f"{item[field]}  {item['path']}\n" for item in manifest["artifacts"])


def verify_manifest(directory: Path, manifest_path: Path | None = None) -> VerificationResult:
    root = directory.expanduser().resolve()
    source = (manifest_path or (root / "manifest.json")).expanduser().resolve()
    payload = json.loads(source.read_text(encoding="utf-8"))
    schema = payload.get("schema")
    if schema not in {"tstack-release-manifest/v1", "tstack-release-manifest/v2"} or not isinstance(payload.get("artifacts"), list):
        raise ValueError("invalid TStack release manifest schema")
    missing, mismatched = [], []
    for item in payload["artifacts"]:
        target = root / item["path"]
        if not target.is_file():
            missing.append(item["path"])
            continue
        valid = _digest(target, "sha256") == item["sha256"] and target.stat().st_size == item["size"]
        if schema == "tstack-release-manifest/v2":
            valid = valid and _digest(target, "sha3_256") == item["sha3_256"]
        if not valid:
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
