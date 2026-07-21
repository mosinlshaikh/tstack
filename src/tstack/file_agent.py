"""Local-first file agent inventory and duplicate detection."""
from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path


FILE_INVENTORY_SCHEMA = "tstack-file-inventory/v1"

EXCLUDED_DIRS = {".git", "__pycache__", "node_modules", ".venv", "venv", "dist", "build", ".pytest_cache"}


@dataclass(frozen=True)
class FileRecord:
    path: str
    size: int
    extension: str
    sha256: str


@dataclass(frozen=True)
class DuplicateGroup:
    sha256: str
    size: int
    paths: tuple[str, ...]


@dataclass(frozen=True)
class FileInventory:
    schema: str
    root: str
    files_scanned: int
    bytes_scanned: int
    extensions: dict[str, int]
    duplicates: tuple[DuplicateGroup, ...]
    records: tuple[FileRecord, ...]
    execution_allowed: bool = False


def _iter_files(root: Path, max_files: int) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*"):
        if len(files) >= max_files:
            break
        if path.is_dir():
            continue
        if any(part in EXCLUDED_DIRS for part in path.relative_to(root).parts):
            continue
        if path.is_symlink():
            continue
        files.append(path)
    return files


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_inventory(root: Path, *, max_files: int = 5000) -> FileInventory:
    base = root.expanduser().resolve()
    if not base.exists() or not base.is_dir():
        raise ValueError(f"inventory root must be an existing directory: {base}")
    records: list[FileRecord] = []
    extensions: Counter[str] = Counter()
    by_hash: dict[str, list[FileRecord]] = defaultdict(list)
    bytes_scanned = 0
    for path in _iter_files(base, max_files):
        size = path.stat().st_size
        digest = _sha256(path)
        relative = str(path.relative_to(base))
        extension = path.suffix.lower() or "<none>"
        record = FileRecord(relative, size, extension, digest)
        records.append(record)
        extensions[extension] += 1
        by_hash[digest].append(record)
        bytes_scanned += size
    duplicates = tuple(
        DuplicateGroup(digest, group[0].size, tuple(sorted(item.path for item in group)))
        for digest, group in by_hash.items()
        if len(group) > 1
    )
    return FileInventory(
        schema=FILE_INVENTORY_SCHEMA,
        root=str(base),
        files_scanned=len(records),
        bytes_scanned=bytes_scanned,
        extensions=dict(sorted(extensions.items())),
        duplicates=tuple(sorted(duplicates, key=lambda item: (item.size, item.sha256), reverse=True)),
        records=tuple(sorted(records, key=lambda item: item.path)),
    )


def inventory_json(inventory: FileInventory) -> str:
    return json.dumps(asdict(inventory), indent=2, sort_keys=True) + "\n"


def inventory_markdown(inventory: FileInventory) -> str:
    lines = [
        "# TStack File Inventory",
        "",
        f"- Root: `{inventory.root}`",
        f"- Files scanned: {inventory.files_scanned}",
        f"- Bytes scanned: {inventory.bytes_scanned}",
        f"- Duplicate groups: {len(inventory.duplicates)}",
        f"- Execution allowed: {'yes' if inventory.execution_allowed else 'no'}",
        "",
        "## Extensions",
        "",
    ]
    lines.extend(f"- `{extension}`: {count}" for extension, count in inventory.extensions.items())
    lines.extend(["", "## Duplicate Groups", ""])
    if not inventory.duplicates:
        lines.append("- none")
    for group in inventory.duplicates:
        lines.append(f"- `{group.sha256[:16]}` size={group.size}: {', '.join(group.paths)}")
    return "\n".join(lines) + "\n"
