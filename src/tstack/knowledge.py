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
