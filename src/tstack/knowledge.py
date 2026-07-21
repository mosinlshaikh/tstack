"""Read-only access to TStack knowledge packs."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class KnowledgeTopic:
    id: str
    title: str
    path: str


@dataclass(frozen=True)
class KnowledgePack:
    id: str
    title: str
    version: str
    status: str
    category: str
    language: str | None
    summary: str
    topics: tuple[KnowledgeTopic, ...]
    path: str


@dataclass(frozen=True)
class KnowledgeValidationResult:
    valid: bool
    packs_checked: int
    errors: tuple[str, ...]


@dataclass(frozen=True)
class KnowledgeStats:
    total_packs: int
    language_packs: int
    categories: dict[str, int]
    statuses: dict[str, int]
    languages: tuple[str, ...]


def knowledge_root() -> Path:
    return Path(__file__).resolve().parents[2] / "knowledge"


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_knowledge_index(root: Path | None = None) -> dict:
    base = root or knowledge_root()
    return _load_json(base / "index.json")


def list_packs(root: Path | None = None) -> tuple[KnowledgePack, ...]:
    base = root or knowledge_root()
    packs = []
    for item in load_knowledge_index(base)["packs"]:
        manifest = _load_json(base.parent / item["path"])
        topics = tuple(KnowledgeTopic(topic["id"], topic["title"], topic["path"]) for topic in manifest["topics"])
        packs.append(
            KnowledgePack(
                id=manifest["id"],
                title=manifest["title"],
                version=manifest["version"],
                status=manifest["status"],
                category=manifest["category"],
                language=manifest.get("language"),
                summary=manifest["summary"],
                topics=topics,
                path=item["path"],
            )
        )
    return tuple(sorted(packs, key=lambda pack: pack.id))


def get_pack(pack_id: str, root: Path | None = None) -> KnowledgePack:
    for pack in list_packs(root):
        if pack.id == pack_id:
            return pack
    raise KeyError(f"unknown knowledge pack: {pack_id}")


def packs_json(packs: tuple[KnowledgePack, ...]) -> str:
    payload = {
        "schema": "tstack-knowledge-list/v1",
        "packs": [
            {
                "id": pack.id,
                "title": pack.title,
                "version": pack.version,
                "status": pack.status,
                "category": pack.category,
                "language": pack.language,
                "path": pack.path,
                "topics": [topic.id for topic in pack.topics],
            }
            for pack in packs
        ],
    }
    return json.dumps(payload, indent=2) + "\n"


def pack_json(pack: KnowledgePack) -> str:
    payload = {
        "schema": "tstack-knowledge-pack-summary/v1",
        "id": pack.id,
        "title": pack.title,
        "version": pack.version,
        "status": pack.status,
        "category": pack.category,
        "language": pack.language,
        "summary": pack.summary,
        "path": pack.path,
        "topics": [{"id": topic.id, "title": topic.title, "path": topic.path} for topic in pack.topics],
    }
    return json.dumps(payload, indent=2) + "\n"


def packs_markdown(packs: tuple[KnowledgePack, ...]) -> str:
    lines = ["# TStack Knowledge Packs", ""]
    for pack in packs:
        language = f" ({pack.language})" if pack.language else ""
        lines.append(f"- `{pack.id}`{language} - {pack.title} `{pack.version}` [{pack.status}]")
    return "\n".join(lines) + "\n"


def pack_markdown(pack: KnowledgePack) -> str:
    lines = [
        f"# {pack.title}",
        "",
        f"- ID: `{pack.id}`",
        f"- Version: `{pack.version}`",
        f"- Status: `{pack.status}`",
        f"- Category: `{pack.category}`",
    ]
    if pack.language:
        lines.append(f"- Language: `{pack.language}`")
    lines.extend(["", pack.summary, "", "## Topics", ""])
    for topic in pack.topics:
        lines.append(f"- `{topic.id}` - {topic.title} ({topic.path})")
    return "\n".join(lines) + "\n"


def knowledge_stats(packs: tuple[KnowledgePack, ...] | None = None) -> KnowledgeStats:
    items = packs or list_packs()
    categories: dict[str, int] = {}
    statuses: dict[str, int] = {}
    languages: list[str] = []
    for pack in items:
        categories[pack.category] = categories.get(pack.category, 0) + 1
        statuses[pack.status] = statuses.get(pack.status, 0) + 1
        if pack.language:
            languages.append(pack.language)
    return KnowledgeStats(
        total_packs=len(items),
        language_packs=len(languages),
        categories=dict(sorted(categories.items())),
        statuses=dict(sorted(statuses.items())),
        languages=tuple(sorted(languages)),
    )


def stats_json(stats: KnowledgeStats) -> str:
    return json.dumps(
        {
            "schema": "tstack-knowledge-stats/v1",
            "total_packs": stats.total_packs,
            "language_packs": stats.language_packs,
            "categories": stats.categories,
            "statuses": stats.statuses,
            "languages": list(stats.languages),
        },
        indent=2,
    ) + "\n"


def stats_markdown(stats: KnowledgeStats) -> str:
    lines = [
        "# TStack Knowledge Stats",
        "",
        f"- Total packs: {stats.total_packs}",
        f"- Language packs: {stats.language_packs}",
        "",
        "## Categories",
        "",
    ]
    lines.extend(f"- `{category}`: {count}" for category, count in stats.categories.items())
    lines.extend(["", "## Statuses", ""])
    lines.extend(f"- `{status}`: {count}" for status, count in stats.statuses.items())
    lines.extend(["", "## Languages", "", ", ".join(stats.languages)])
    return "\n".join(lines) + "\n"


def validate_knowledge(root: Path | None = None) -> KnowledgeValidationResult:
    base = root or knowledge_root()
    errors: list[str] = []
    packs_checked = 0

    try:
        index = load_knowledge_index(base)
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        return KnowledgeValidationResult(False, 0, (f"invalid knowledge index: {exc}",))

    if index.get("schema") != "tstack-knowledge-index/v1":
        errors.append("knowledge index schema must be tstack-knowledge-index/v1")
    if index.get("compatibility", {}).get("knowledge_schema") != "tstack-knowledge-pack/v1":
        errors.append("knowledge index compatibility.knowledge_schema must be tstack-knowledge-pack/v1")

    pack_ids: set[str] = set()
    registered_dirs: set[Path] = set()
    required_topics = {"overview", "security", "performance", "testing", "production"}

    for item in index.get("packs", []):
        packs_checked += 1
        pack_id = item.get("id", "<missing-id>")
        if pack_id in pack_ids:
            errors.append(f"duplicate pack id: {pack_id}")
        pack_ids.add(pack_id)

        manifest_path = base.parent / item.get("path", "")
        registered_dirs.add(manifest_path.parent)
        if not manifest_path.exists():
            errors.append(f"{pack_id}: missing manifest {manifest_path}")
            continue

        try:
            manifest = _load_json(manifest_path)
        except json.JSONDecodeError as exc:
            errors.append(f"{pack_id}: invalid manifest JSON: {exc}")
            continue

        for field in ("schema", "id", "title", "version", "status", "category", "summary", "topics", "quality_gates", "limitations"):
            if not manifest.get(field):
                errors.append(f"{pack_id}: missing manifest field {field}")

        if manifest.get("schema") != "tstack-knowledge-pack/v1":
            errors.append(f"{pack_id}: manifest schema must be tstack-knowledge-pack/v1")
        for field in ("id", "version", "status", "category"):
            if manifest.get(field) != item.get(field):
                errors.append(f"{pack_id}: manifest {field} does not match index")

        topics = {topic.get("id"): topic for topic in manifest.get("topics", [])}
        missing_topics = required_topics - set(topics)
        if missing_topics:
            errors.append(f"{pack_id}: missing topics {','.join(sorted(missing_topics))}")
        for topic_id, topic in topics.items():
            topic_path = manifest_path.parent / topic.get("path", "")
            if not topic_path.exists():
                errors.append(f"{pack_id}: missing topic file {topic_id}: {topic_path}")
                continue
            if not topic_path.read_text(encoding="utf-8").startswith("# "):
                errors.append(f"{pack_id}: topic {topic_id} must start with a markdown heading")

    language_root = base / "languages"
    if language_root.exists():
        language_dirs = {path for path in language_root.iterdir() if path.is_dir()}
        unregistered = language_dirs - registered_dirs
        missing_dirs = registered_dirs - language_dirs
        for path in sorted(unregistered):
            errors.append(f"unregistered language directory: {path.name}")
        for path in sorted(missing_dirs):
            errors.append(f"registered language directory is missing: {path.name}")

    return KnowledgeValidationResult(not errors, packs_checked, tuple(errors))


def validation_json(result: KnowledgeValidationResult) -> str:
    return json.dumps(
        {
            "schema": "tstack-knowledge-validation/v1",
            "valid": result.valid,
            "packs_checked": result.packs_checked,
            "errors": list(result.errors),
        },
        indent=2,
    ) + "\n"


def validation_markdown(result: KnowledgeValidationResult) -> str:
    lines = [
        "# TStack Knowledge Validation",
        "",
        f"- Verdict: **{'PASS' if result.valid else 'FAIL'}**",
        f"- Packs checked: {result.packs_checked}",
    ]
    if result.errors:
        lines.extend(["", "## Errors", ""])
        lines.extend(f"- {error}" for error in result.errors)
    return "\n".join(lines) + "\n"
