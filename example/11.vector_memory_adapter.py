#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Minimal vector-memory adapter example.

This file demonstrates the MemoryProtocol shape expected by LightAgent without
adding a hard dependency on any one vector database. Replace the in-memory
`_records` list with Qdrant, Chroma, Milvus, FAISS, or another backend while
keeping the same `store(data, user_id)` / `retrieve(query, user_id)` methods.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from math import sqrt
from re import findall
from typing import Any

from LightAgent import LightAgent, MemoryPolicy, MemoryScope


def _embed(text: str) -> Counter[str]:
    """Tiny local embedding substitute for the example.

    Real adapters should call their embedding model here and store vectors in
    the selected vector database. Keeping this local makes the example runnable
    in CI and easy to port.
    """
    return Counter(findall(r"[a-z0-9]+", text.lower()))


def _cosine(a: Counter[str], b: Counter[str]) -> float:
    if not a or not b:
        return 0.0
    dot = sum(a[token] * b[token] for token in a.keys() & b.keys())
    norm_a = sqrt(sum(value * value for value in a.values()))
    norm_b = sqrt(sum(value * value for value in b.values()))
    return dot / (norm_a * norm_b)


@dataclass
class MemoryRecord:
    user_id: str
    memory: str
    embedding: Counter[str]
    metadata: dict[str, Any] = field(default_factory=dict)


class LocalVectorMemoryAdapter:
    """Example MemoryProtocol adapter with provenance-aware records."""

    def __init__(self, *, agent_name: str = "example-agent", top_k: int = 3):
        self.agent_name = agent_name
        self.top_k = top_k
        self._records: list[MemoryRecord] = []

    def store(self, data: str, user_id: str) -> dict[str, Any]:
        scope = MemoryScope.user(agent_name=self.agent_name, user_id=user_id)
        record = MemoryRecord(
            user_id=user_id,
            memory=data,
            embedding=_embed(data),
            metadata=scope.to_metadata(),
        )
        self._records.append(record)
        return {"stored": True, "user_id": user_id}

    def retrieve(self, query: str, user_id: str) -> dict[str, list[dict[str, Any]]]:
        query_embedding = _embed(query)
        scored = [
            (_cosine(query_embedding, record.embedding), record)
            for record in self._records
            if record.user_id == user_id
        ]
        scored.sort(key=lambda item: item[0], reverse=True)

        results = [
            {
                "memory": record.memory,
                "score": score,
                "user_id": record.user_id,
                "metadata": record.metadata,
            }
            for score, record in scored[: self.top_k]
            if score > 0
        ]
        return {"results": results}


def build_agent(memory: LocalVectorMemoryAdapter) -> LightAgent:
    return LightAgent(
        role="You are LightAgent with a custom vector memory adapter.",
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


if __name__ == "__main__":
    memory = LocalVectorMemoryAdapter(agent_name="travel-agent")
    agent = build_agent(memory)
    user_id = "user_01"

    print(agent.run("Remember that I prefer quiet beach towns.", user_id=user_id))
    print(agent.run("Where should I travel next?", user_id=user_id))
