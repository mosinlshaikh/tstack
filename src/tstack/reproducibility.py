"""Reproducible-build comparison and GitHub attestation receipt generation."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class ReproRecord:
    artifact: str
    original_sha256: str | None
    rebuilt_sha256: str | None
    original_sha3_256: str | None
    rebuilt_sha3_256: str | None
    reproducible: bool


@dataclass(frozen=True)
class ReproResult:
    passed: bool
    checked: int
    records: tuple[ReproRecord, ...]
    missing_original: tuple[str, ...]
    missing_rebuilt: tuple[str, ...]


def _digest(path: Path, algorithm: str) -> str:
    digest = hashlib.new(algorithm)
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def compare_builds(original: Path, rebuilt: Path) -> ReproResult:
    left = original.expanduser().resolve()
    right = rebuilt.expanduser().resolve()
    if not left.is_dir() or not right.is_dir():
        raise FileNotFoundError("both original and rebuilt artifact directories must exist")

    supported = {".whl", ".gz", ".zip"}
    left_files = {item.name: item for item in left.iterdir() if item.is_file() and item.suffix in supported}
    right_files = {item.name: item for item in right.iterdir() if item.is_file() and item.suffix in supported}
    names = sorted(set(left_files) | set(right_files))
    if not names:
        raise ValueError("no comparable release artifacts found")

    records: list[ReproRecord] = []
    for name in names:
        a, b = left_files.get(name), right_files.get(name)
        a256 = _digest(a, "sha256") if a else None
        b256 = _digest(b, "sha256") if b else None
        a3 = _digest(a, "sha3_256") if a else None
        b3 = _digest(b, "sha3_256") if b else None
        records.append(ReproRecord(name, a256, b256, a3, b3, bool(a and b and a256 == b256 and a3 == b3)))

    missing_original = tuple(name for name in names if name not in left_files)
    missing_rebuilt = tuple(name for name in names if name not in right_files)
    passed = not missing_original and not missing_rebuilt and all(item.reproducible for item in records)
    return ReproResult(passed, len(records), tuple(records), missing_original, missing_rebuilt)


def repro_json(result: ReproResult) -> str:
    return json.dumps(asdict(result), indent=2, sort_keys=True) + "\n"


def verify_attestation(
    artifact: Path,
    *,
    repository: str,
    workflow: str,
    source_digest: str | None = None,
    deny_self_hosted: bool = True,
) -> dict:
    gh = shutil.which("gh")
    if not gh:
        raise FileNotFoundError("GitHub CLI 'gh' is required for attestation verification")
    target = artifact.expanduser().resolve()
    if not target.is_file():
        raise FileNotFoundError(f"artifact not found: {target}")

    command = [
        gh, "attestation", "verify", str(target),
        "--repo", repository,
        "--signer-workflow", f"{repository}/{workflow}",
        "--format", "json",
    ]
    if source_digest:
        command.extend(["--source-digest", source_digest])
    if deny_self_hosted:
        command.append("--deny-self-hosted-runners")

    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip() or "attestation verification failed"
        raise ValueError(detail)
    payload = json.loads(completed.stdout)
    if not isinstance(payload, list) or not payload:
        raise ValueError("GitHub CLI returned no verified attestations")
    return {
        "schema": "tstack-attestation-receipt/v1",
        "verified": True,
        "artifact": target.name,
        "repository": repository,
        "workflow": workflow,
        "source_digest": source_digest,
        "deny_self_hosted_runners": deny_self_hosted,
        "verification_results": payload,
    }


def receipt_json(receipt: dict) -> str:
    return json.dumps(receipt, indent=2, sort_keys=True) + "\n"
