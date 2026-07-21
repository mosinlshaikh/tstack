import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
KNOWLEDGE_ROOT = ROOT / "knowledge"
INDEX_PATH = KNOWLEDGE_ROOT / "index.json"
REQUIRED_TOPICS = {"overview", "security", "performance", "testing", "production"}


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_knowledge_index_contract():
    index = load_json(INDEX_PATH)

    assert index["schema"] == "tstack-knowledge-index/v1"
    assert index["version"]
    assert index["compatibility"]["knowledge_schema"] == "tstack-knowledge-pack/v1"
    assert index["packs"]

    category_ids = {category["id"] for category in index["categories"]}
    assert "languages" in category_ids


def test_registered_knowledge_packs_are_valid():
    index = load_json(INDEX_PATH)
    pack_ids = set()

    for pack in index["packs"]:
        pack_id = pack["id"]
        assert pack_id not in pack_ids
        pack_ids.add(pack_id)

        assert pack["category"] == "languages"
        assert pack["status"] in {"draft", "review", "stable"}
        assert REQUIRED_TOPICS.issubset(set(pack["topics"]))

        manifest_path = ROOT / pack["path"]
        assert manifest_path.exists(), f"missing manifest for {pack_id}: {manifest_path}"

        manifest = load_json(manifest_path)
        assert manifest["schema"] == "tstack-knowledge-pack/v1"
        assert manifest["id"] == pack_id
        assert manifest["version"] == pack["version"]
        assert manifest["status"] == pack["status"]
        assert manifest["category"] == pack["category"]
        assert manifest["summary"]
        assert manifest["audience"]
        assert manifest["quality_gates"]
        assert manifest["limitations"]

        manifest_topics = {topic["id"]: topic for topic in manifest["topics"]}
        assert REQUIRED_TOPICS.issubset(manifest_topics.keys())

        for topic_id, topic in manifest_topics.items():
            assert topic["title"]
            topic_path = manifest_path.parent / topic["path"]
            assert topic_path.exists(), f"missing topic {topic_id} for {pack_id}: {topic_path}"
            content = topic_path.read_text(encoding="utf-8")
            assert content.startswith("# "), f"topic {topic_id} for {pack_id} needs a markdown heading"


def test_language_pack_directories_are_registered():
    index = load_json(INDEX_PATH)
    registered_paths = {(ROOT / pack["path"]).parent for pack in index["packs"]}
    language_dirs = {path for path in (KNOWLEDGE_ROOT / "languages").iterdir() if path.is_dir()}

    assert language_dirs == registered_paths
