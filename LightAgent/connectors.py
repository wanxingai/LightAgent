#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Dependency-free connector manifests and offline validation utilities."""

from __future__ import annotations

import ast
import inspect
import re
import textwrap
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from .skills import Skill
from .tools import ToolRegistry


_CONNECTOR_NAME_PATTERN = re.compile(r"[A-Za-z][A-Za-z0-9._-]*")
_VERSION_PATTERN = re.compile(r"\d+\.\d+\.\d+(?:[-+][A-Za-z0-9.-]+)?")
_EXTRA_NAME_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")
_REQUIREMENT_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*(?:\[[A-Za-z0-9,._-]+\])?(?:\s*[<>=!~].+)?")
_SECRET_FIELD_PATTERN = re.compile(r"(?:api[_-]?key|token|secret|password|authorization)", re.IGNORECASE)
_PLACEHOLDER_PATTERN = re.compile(r"(?:\$\{|\{\{|<[^>]+>|your[_ -]|replace[_ -]|env:)", re.IGNORECASE)

_UNSAFE_IMPORT_HINTS = {
    "ctypes": "native process access",
    "importlib": "dynamic imports",
    "os": "host operating-system access",
    "pickle": "unsafe deserialization",
    "pty": "pseudo-terminal access",
    "shutil": "host filesystem mutation",
    "socket": "direct network access",
    "subprocess": "child-process execution",
}
_NETWORK_IMPORT_HINTS = {"aiohttp", "httpx", "requests", "urllib"}
_HOOK_PHASES = {
    "before_run",
    "after_run",
    "on_error",
    "before_model_request",
    "after_model_response",
    "before_tool_call",
    "after_tool_result",
    "before_memory_retrieve",
    "after_memory_retrieve",
    "before_memory_write",
    "after_memory_write",
    "before_memory_promote",
    "after_memory_promote",
    "on_handoff",
    "before_flow_run",
    "after_flow_run",
    "before_flow_step",
    "after_flow_step",
}


def _as_tuple(value: Any) -> tuple[Any, ...]:
    if value is None:
        return ()
    if isinstance(value, tuple):
        return value
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return tuple(value)
    return (value,)


@dataclass(frozen=True)
class ConnectorManifest:
    """Declarative bundle of existing LightAgent extension primitives.

    A manifest is metadata only. Constructing or validating it never starts an
    MCP server, imports an optional provider SDK, or invokes a tool or hook.
    """

    name: str
    version: str
    description: str = ""
    tools: tuple[Callable[..., Any], ...] = ()
    skills: tuple[Skill | str, ...] = ()
    mcp_servers: Mapping[str, Mapping[str, Any]] = field(default_factory=dict)
    hooks: tuple[Callable[..., Any] | Any, ...] = ()
    memory_adapters: Mapping[str, Any] = field(default_factory=dict)
    extras: Mapping[str, Sequence[str]] = field(default_factory=dict)
    docs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "tools", _as_tuple(self.tools))
        object.__setattr__(self, "skills", _as_tuple(self.skills))
        object.__setattr__(self, "hooks", _as_tuple(self.hooks))
        object.__setattr__(self, "docs", tuple(str(item) for item in _as_tuple(self.docs)))


@dataclass(frozen=True)
class ConnectorDiagnostic:
    """One offline connector validation finding."""

    connector: str
    level: str
    field: str
    message: str
    component: str | None = None

    def to_dict(self) -> dict[str, str]:
        data = {
            "connector": self.connector,
            "level": self.level,
            "field": self.field,
            "message": self.message,
        }
        if self.component is not None:
            data["component"] = self.component
        return data


@dataclass(frozen=True)
class ConnectorValidationReport:
    """Structured result returned by :func:`validate_connector`."""

    connector: str
    diagnostics: tuple[ConnectorDiagnostic, ...] = ()

    @property
    def valid(self) -> bool:
        return not any(item.level == "error" for item in self.diagnostics)

    @property
    def errors(self) -> tuple[ConnectorDiagnostic, ...]:
        return tuple(item for item in self.diagnostics if item.level == "error")

    @property
    def warnings(self) -> tuple[ConnectorDiagnostic, ...]:
        return tuple(item for item in self.diagnostics if item.level == "warning")

    def to_dict(self) -> dict[str, Any]:
        return {
            "connector": self.connector,
            "valid": self.valid,
            "diagnostics": [item.to_dict() for item in self.diagnostics],
        }


class ConnectorValidator:
    """Validate a connector manifest without loading external services."""

    def __init__(self, *, base_path: str | Path | None = None):
        self.base_path = Path(base_path or ".").expanduser().resolve()

    def validate(self, manifest: ConnectorManifest) -> ConnectorValidationReport:
        if not isinstance(manifest, ConnectorManifest):
            diagnostic = ConnectorDiagnostic(
                connector="<unknown>",
                level="error",
                field="manifest",
                message="manifest must be a ConnectorManifest",
            )
            return ConnectorValidationReport("<unknown>", (diagnostic,))

        connector_name = str(manifest.name or "<unknown>")
        diagnostics: list[ConnectorDiagnostic] = []

        def add(level: str, field: str, message: str, component: str | None = None) -> None:
            diagnostics.append(ConnectorDiagnostic(connector_name, level, field, message, component))

        self._validate_identity(manifest, add)
        self._validate_tools(manifest, add)
        self._validate_skills(manifest, add)
        self._validate_mcp_servers(manifest, add)
        self._validate_hooks(manifest, add)
        self._validate_memory_adapters(manifest, add)
        self._validate_extras(manifest, add)
        self._validate_docs(manifest, add)
        return ConnectorValidationReport(connector_name, tuple(diagnostics))

    @staticmethod
    def _validate_identity(manifest: ConnectorManifest, add: Callable[..., None]) -> None:
        if not isinstance(manifest.name, str) or not _CONNECTOR_NAME_PATTERN.fullmatch(manifest.name):
            add("error", "name", "name must match [A-Za-z][A-Za-z0-9._-]*")
        if not isinstance(manifest.version, str) or not _VERSION_PATTERN.fullmatch(manifest.version):
            add("error", "version", "version must be a semantic version such as 1.0.0")
        if not isinstance(manifest.description, str) or not manifest.description.strip():
            add("warning", "description", "description should not be empty")

    @staticmethod
    def _validate_tools(manifest: ConnectorManifest, add: Callable[..., None]) -> None:
        names: dict[str, int] = {}
        for index, tool in enumerate(manifest.tools):
            field_name = f"tools[{index}]"
            if not callable(tool):
                add("error", field_name, "tool must be callable")
                continue
            tool_info = getattr(tool, "tool_info", None)
            component = getattr(tool, "__name__", tool.__class__.__name__)
            if tool_info is None:
                add("error", f"{field_name}.tool_info", "tool must define tool_info metadata", component)
                continue
            for item in ToolRegistry.validate_tool_info(tool_info):
                add(item["level"], f"{field_name}.{item['field']}", item["message"], component)
            tool_name = tool_info.get("tool_name") if isinstance(tool_info, dict) else None
            if isinstance(tool_name, str) and tool_name:
                names[tool_name] = names.get(tool_name, 0) + 1
            ConnectorValidator._validate_tool_source(tool, field_name, component, add)

        for tool_name, count in names.items():
            if count > 1:
                add("error", "tools", f"duplicate tool name `{tool_name}` appears {count} times", tool_name)

    @staticmethod
    def _validate_tool_source(tool: Callable[..., Any], field_name: str, component: str, add: Callable[..., None]) -> None:
        try:
            source = textwrap.dedent(inspect.getsource(tool))
            tree = ast.parse(source)
        except (OSError, TypeError, IndentationError, SyntaxError):
            return

        imports: set[str] = set()
        dynamic_import = False
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".", 1)[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".", 1)[0])
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "__import__":
                dynamic_import = True

        for module in sorted(imports & _UNSAFE_IMPORT_HINTS.keys()):
            add(
                "warning",
                f"{field_name}.imports",
                f"tool imports `{module}`, which permits {_UNSAFE_IMPORT_HINTS[module]}; protect it with policy and isolation",
                component,
            )
        for module in sorted(imports & _NETWORK_IMPORT_HINTS):
            add(
                "warning",
                f"{field_name}.imports",
                f"tool imports network client `{module}`; keep network access opt-in and document authentication",
                component,
            )
        if dynamic_import:
            add("warning", f"{field_name}.imports", "tool uses dynamic __import__; static validation is incomplete", component)

    def _validate_skills(self, manifest: ConnectorManifest, add: Callable[..., None]) -> None:
        for index, skill in enumerate(manifest.skills):
            field_name = f"skills[{index}]"
            if isinstance(skill, Skill):
                if not skill.name.strip() or not skill.description.strip():
                    add("error", field_name, "Skill name and description must not be empty", skill.name or None)
                path = Path(skill.path)
            elif isinstance(skill, str) and skill.strip():
                path = Path(skill)
            else:
                add("error", field_name, "skill must be a Skill instance or local path")
                continue
            resolved = path.expanduser()
            if not resolved.is_absolute():
                resolved = self.base_path / resolved
            skill_file = resolved if resolved.name == "SKILL.md" else resolved / "SKILL.md"
            if not skill_file.is_file():
                add("error", field_name, f"SKILL.md not found at {skill_file}", getattr(skill, "name", None))

    @staticmethod
    def _validate_mcp_servers(manifest: ConnectorManifest, add: Callable[..., None]) -> None:
        if not isinstance(manifest.mcp_servers, Mapping):
            add("error", "mcp_servers", "mcp_servers must be a mapping")
            return
        for server_name, config in manifest.mcp_servers.items():
            field_name = f"mcp_servers.{server_name}"
            if not isinstance(server_name, str) or not server_name.strip():
                add("error", field_name, "MCP server name must be a non-empty string")
            if not isinstance(config, Mapping):
                add("error", field_name, "MCP server config must be a mapping")
                continue
            has_url = isinstance(config.get("url"), str) and bool(config.get("url"))
            has_command = isinstance(config.get("command"), str) and bool(config.get("command"))
            if has_url == has_command:
                add("error", field_name, "MCP config must define exactly one of `url` or `command`")
            args = config.get("args", [])
            if has_command and (
                isinstance(args, (str, bytes, bytearray))
                or not isinstance(args, Sequence)
            ):
                add("error", f"{field_name}.args", "stdio MCP args must be a sequence")
            ConnectorValidator._scan_secrets(config, field_name, add)

    @staticmethod
    def _scan_secrets(value: Any, field_name: str, add: Callable[..., None]) -> None:
        if not isinstance(value, Mapping):
            return
        for key, item in value.items():
            nested_field = f"{field_name}.{key}"
            if isinstance(item, Mapping):
                ConnectorValidator._scan_secrets(item, nested_field, add)
            elif _SECRET_FIELD_PATTERN.search(str(key)) and isinstance(item, str) and item.strip():
                if not _PLACEHOLDER_PATTERN.search(item):
                    add("warning", nested_field, "credential-like value should use an environment/config placeholder")

    @staticmethod
    def _validate_hooks(manifest: ConnectorManifest, add: Callable[..., None]) -> None:
        for index, hook in enumerate(manifest.hooks):
            if callable(hook):
                continue
            if any(callable(getattr(hook, phase, None)) for phase in _HOOK_PHASES):
                continue
            add("error", f"hooks[{index}]", "hook must be callable or implement a supported lifecycle phase")

    @staticmethod
    def _validate_memory_adapters(manifest: ConnectorManifest, add: Callable[..., None]) -> None:
        if not isinstance(manifest.memory_adapters, Mapping):
            add("error", "memory_adapters", "memory_adapters must be a mapping")
            return
        for name, adapter in manifest.memory_adapters.items():
            field_name = f"memory_adapters.{name}"
            if not callable(getattr(adapter, "store", None)):
                add("error", field_name, "memory adapter must implement store(data, user_id)")
            if not callable(getattr(adapter, "retrieve", None)):
                add("error", field_name, "memory adapter must implement retrieve(query, user_id)")

    @staticmethod
    def _validate_extras(manifest: ConnectorManifest, add: Callable[..., None]) -> None:
        if not isinstance(manifest.extras, Mapping):
            add("error", "extras", "extras must be a mapping of extra names to requirement sequences")
            return
        for extra_name, requirements in manifest.extras.items():
            field_name = f"extras.{extra_name}"
            if not isinstance(extra_name, str) or not _EXTRA_NAME_PATTERN.fullmatch(extra_name):
                add("error", field_name, "extra name contains unsupported characters")
            if isinstance(requirements, str) or not isinstance(requirements, Sequence):
                add("error", field_name, "extra requirements must be a sequence of requirement strings")
                continue
            for index, requirement in enumerate(requirements):
                if not isinstance(requirement, str) or not _REQUIREMENT_PATTERN.fullmatch(requirement.strip()):
                    add("error", f"{field_name}[{index}]", "invalid optional dependency declaration")

    def _validate_docs(self, manifest: ConnectorManifest, add: Callable[..., None]) -> None:
        if not manifest.docs:
            add("warning", "docs", "at least one local usage document is recommended")
            return
        for index, doc in enumerate(manifest.docs):
            field_name = f"docs[{index}]"
            if doc.startswith(("http://", "https://")):
                add("warning", field_name, "remote documentation cannot be verified offline")
                continue
            path = Path(doc).expanduser()
            if not path.is_absolute():
                path = self.base_path / path
            if not path.is_file():
                add("error", field_name, f"documentation file not found at {path}")


def validate_connector(
        manifest: ConnectorManifest,
        *,
        base_path: str | Path | None = None,
) -> ConnectorValidationReport:
    """Validate a connector manifest without invoking connector components."""

    return ConnectorValidator(base_path=base_path).validate(manifest)


__all__ = [
    "ConnectorDiagnostic",
    "ConnectorManifest",
    "ConnectorValidationReport",
    "ConnectorValidator",
    "validate_connector",
]
