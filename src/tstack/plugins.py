"""Extensible rule discovery and execution for TStack.

Installed Python plugins use the ``tstack.rules`` entry-point group. Projects may
also define non-executable declarative rules under ``.tstack/rules/*.json``.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from importlib.metadata import entry_points
from pathlib import Path
from typing import Iterable, Protocol

SEVERITIES = {"low", "medium", "high", "critical"}
RULE_ID = re.compile(r"^[A-Z][A-Z0-9_-]{2,63}$")


@dataclass(frozen=True)
class PluginFinding:
    rule_id: str
    severity: str
    title: str
    path: str | None
    evidence: str
    remediation: str
    plugin: str


@dataclass(frozen=True)
class PluginDescriptor:
    name: str
    version: str
    source: str
    integrity: str
    rules: int


class RulePlugin(Protocol):
    """Public SDK contract for installed rule plugins."""

    name: str
    version: str

    def scan(self, root: Path, relative_files: frozenset[str]) -> Iterable[PluginFinding | dict]: ...


def _validate_finding(item: PluginFinding | dict, plugin_name: str) -> PluginFinding:
    if isinstance(item, PluginFinding):
        finding = item
    elif isinstance(item, dict):
        required = {"rule_id", "severity", "title", "evidence", "remediation"}
        missing = required - item.keys()
        if missing:
            raise ValueError(f"plugin {plugin_name!r} finding missing fields: {sorted(missing)}")
        finding = PluginFinding(
            rule_id=str(item["rule_id"]),
            severity=str(item["severity"]).lower(),
            title=str(item["title"]),
            path=str(item["path"]) if item.get("path") is not None else None,
            evidence=str(item["evidence"]),
            remediation=str(item["remediation"]),
            plugin=plugin_name,
        )
    else:
        raise ValueError(f"plugin {plugin_name!r} returned unsupported finding type")
    if not RULE_ID.fullmatch(finding.rule_id):
        raise ValueError(f"plugin {plugin_name!r} returned invalid rule id: {finding.rule_id!r}")
    if finding.severity not in SEVERITIES:
        raise ValueError(f"plugin {plugin_name!r} returned invalid severity: {finding.severity!r}")
    return finding


def _declarative_rules(root: Path, relative_files: frozenset[str]) -> tuple[list[PluginFinding], PluginDescriptor | None]:
    rules_dir = root / ".tstack" / "rules"
    if not rules_dir.is_dir():
        return [], None
    findings: list[PluginFinding] = []
    digest = hashlib.sha256()
    rule_count = 0
    for rule_path in sorted(rules_dir.glob("*.json")):
        raw = rule_path.read_bytes()
        digest.update(rule_path.name.encode()); digest.update(b"\0"); digest.update(raw)
        payload = json.loads(raw.decode("utf-8"))
        rules = payload.get("rules")
        if not isinstance(rules, list):
            raise ValueError(f"declarative plugin file requires a rules array: {rule_path}")
        for rule in rules:
            if not isinstance(rule, dict):
                raise ValueError(f"invalid rule object in {rule_path}")
            rule_count += 1
            rule_id = str(rule.get("id", ""))
            severity = str(rule.get("severity", "medium")).lower()
            title = str(rule.get("title", rule_id))
            pattern = str(rule.get("path_regex", ""))
            remediation = str(rule.get("remediation", "Review and resolve this custom policy finding."))
            if not RULE_ID.fullmatch(rule_id) or severity not in SEVERITIES or not pattern:
                raise ValueError(f"invalid declarative rule in {rule_path}: {rule_id!r}")
            compiled = re.compile(pattern)
            for relative in sorted(relative_files):
                if compiled.search(relative):
                    findings.append(PluginFinding(rule_id, severity, title, relative, f"Path matched custom rule regex: {pattern}", remediation, "project-rules"))
    descriptor = PluginDescriptor("project-rules", "1", str(rules_dir), digest.hexdigest(), rule_count)
    return findings, descriptor


def run_plugins(root: Path, relative_files: set[str]) -> tuple[tuple[PluginFinding, ...], tuple[PluginDescriptor, ...]]:
    """Run declarative project rules and explicitly installed Python entry points."""
    frozen_files = frozenset(relative_files)
    findings, local_descriptor = _declarative_rules(root, frozen_files)
    descriptors: list[PluginDescriptor] = [local_descriptor] if local_descriptor else []

    selected = entry_points().select(group="tstack.rules")
    for entry in sorted(selected, key=lambda value: value.name):
        plugin = entry.load()
        plugin = plugin() if isinstance(plugin, type) else plugin
        name = str(getattr(plugin, "name", entry.name))
        version = str(getattr(plugin, "version", "0"))
        raw_findings = list(plugin.scan(root, frozen_files))
        validated = [_validate_finding(item, name) for item in raw_findings]
        findings.extend(validated)
        integrity = hashlib.sha256(f"{entry.value}\0{version}".encode()).hexdigest()
        descriptors.append(PluginDescriptor(name, version, entry.value, integrity, len(validated)))

    findings.sort(key=lambda item: (item.rule_id, item.path or "", item.plugin))
    descriptors.sort(key=lambda item: item.name)
    return tuple(findings), tuple(descriptors)


def plugins_json(descriptors: Iterable[PluginDescriptor]) -> str:
    return json.dumps([item.__dict__ for item in descriptors], indent=2, sort_keys=True) + "\n"
