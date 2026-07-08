#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Minimal ClawMem memory adapter example.

This file demonstrates how to connect a ClawMem-like client to LightAgent's
small MemoryProtocol without adding ClawMem as a required dependency. The
provided client is intentionally injected so tests and CI can use a fake client
instead of making live network calls or requiring secrets.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from LightAgent import LightAgent, MemoryPolicy, MemoryScope


class ClawMemMemoryAdapter:
    """MemoryProtocol adapter for a ClawMem-compatible client.

    The injected client should expose:

    - `create_memory(payload: dict[str, Any])`
    - `search_memories(query: str, *, user_id: str, limit: int, metadata_filter: dict[str, Any] | None = None)`

    Wrap the real ClawMem HTTP, MCP, or SDK client behind those two methods so
    this adapter can stay dependency-free.
    """

    def __init__(
            self,
            client: Any,
            *,
            agent_name: str = "lightagent",
            category: str = "lightagent",
            top_k: int = 5,
            default_source: str = "user",
            default_scope: str = "user",
    ):
        if top_k <= 0:
            raise ValueError("top_k must be greater than 0")
        self.client = client
        self.agent_name = agent_name
        self.category = category
        self.top_k = top_k
        self.default_source = default_source
        self.default_scope = default_scope

    def store(self, data: str, user_id: str, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
        """Store a LightAgent memory as a ClawMem knowledge item."""
        memory_text = str(data)
        record_metadata = self._metadata(user_id=user_id, metadata=metadata)
        payload = {
            "title": self._title(memory_text),
            "description": self._description(memory_text),
            "content": memory_text,
            "category": self.category,
            "user_id": str(user_id),
            "metadata": record_metadata,
            "tags": self._tags(record_metadata),
        }
        created = self.client.create_memory(payload)
        return {
            "stored": True,
            "user_id": str(user_id),
            "memory_id": self._value(created, "id", "memory_id", "memoryId"),
        }

    def retrieve(self, query: str, user_id: str) -> dict[str, list[dict[str, Any]]]:
        """Search ClawMem and return LightAgent-compatible memory results."""
        metadata_filter = {
            "source": self.default_source,
            "scope": self.default_scope,
            "agent_name": self.agent_name,
        }
        raw_results = self.client.search_memories(
            str(query),
            user_id=str(user_id),
            limit=self.top_k,
            metadata_filter=metadata_filter,
        )

        results = []
        for item in raw_results or []:
            memory = self._value(item, "memory", "content", "text")
            if memory is None:
                continue
            item_metadata = self._value(item, "metadata") or {}
            if not isinstance(item_metadata, dict):
                item_metadata = {}
            result_user_id = str(self._value(item, "user_id", "userId") or user_id)
            item_metadata.setdefault("user_id", result_user_id)
            item_metadata.setdefault("source", self.default_source)
            item_metadata.setdefault("scope", self.default_scope)
            item_metadata.setdefault("agent_name", self.agent_name)
            results.append({
                "memory": str(memory),
                "score": self._value(item, "score"),
                "user_id": result_user_id,
                "metadata": item_metadata,
            })
        return {"results": results}

    def _metadata(self, *, user_id: str, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
        record_metadata = MemoryScope(
            source=self.default_source,
            scope=self.default_scope,
            agent_name=self.agent_name,
            metadata={"user_id": str(user_id)},
        ).to_metadata()
        if metadata:
            record_metadata.update(metadata)
        record_metadata.setdefault("user_id", str(user_id))
        record_metadata.setdefault("source", self.default_source)
        record_metadata.setdefault("scope", self.default_scope)
        record_metadata.setdefault("agent_name", self.agent_name)
        return record_metadata

    @staticmethod
    def _title(text: str, *, max_length: int = 80) -> str:
        title = " ".join((text.strip().splitlines() or [""])[0].split())
        if not title:
            return "LightAgent memory"
        if len(title) <= max_length:
            return title
        return f"{title[:max_length - 3].rstrip()}..."

    @classmethod
    def _description(cls, text: str) -> str:
        return cls._title(text, max_length=160)

    @staticmethod
    def _tags(metadata: dict[str, Any]) -> list[str]:
        tags = [
            f"source:{metadata.get('source')}",
            f"scope:{metadata.get('scope')}",
        ]
        agent_name = metadata.get("agent_name")
        if agent_name:
            tags.append(f"agent:{agent_name}")
        user_id = metadata.get("user_id")
        if user_id:
            tags.append(f"user:{user_id}")
        return tags

    @staticmethod
    def _value(item: Any, *names: str) -> Any:
        if item is None:
            return None
        if isinstance(item, dict):
            for name in names:
                if name in item:
                    return item[name]
            return None
        for name in names:
            if hasattr(item, name):
                return getattr(item, name)
        return None


def build_agent(memory: ClawMemMemoryAdapter) -> LightAgent:
    return LightAgent(
        role="You are LightAgent with an optional ClawMem long-term memory adapter.",
        model="deepseek-chat",
        api_key="your_api_key",
        base_url="your_base_url",
        memory=memory,
        memory_policy=MemoryPolicy(
            namespace="demo",
            allow_unattributed_results=False,
            allowed_sources=("user",),
            allowed_scopes=("user",),
        ),
        tree_of_thought=False,
    )


class ExampleClawMemClient:
    """Tiny placeholder showing the methods the adapter expects.

    Replace this with a wrapper around your ClawMem SDK, HTTP client, or MCP
    client. The methods deliberately raise so the example never performs a live
    network call unless the user supplies a real client.
    """

    def create_memory(self, payload: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError("Wrap your ClawMem client and create the memory item here.")

    def search_memories(
            self,
            query: str,
            *,
            user_id: str,
            limit: int,
            metadata_filter: dict[str, Any] | None = None,
    ) -> Iterable[dict[str, Any]]:
        raise NotImplementedError("Wrap your ClawMem client and search memory items here.")


if __name__ == "__main__":
    client = ExampleClawMemClient()
    memory = ClawMemMemoryAdapter(client, agent_name="travel-agent")
    agent = build_agent(memory)

    print(agent.run("Remember that I prefer quiet beach towns.", user_id="user_01"))
    print(agent.run("Where should I travel next?", user_id="user_01"))
