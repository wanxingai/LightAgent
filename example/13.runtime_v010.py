#!/usr/bin/env python
"""Minimal v0.10 Session, Policy, and SQLite RAG example."""

import os
import tempfile
from pathlib import Path

from LightAgent import (
    BudgetLimits,
    JsonlSessionStore,
    LightAgent,
    RetrievalDocument,
    SqliteFTSRetrievalProvider,
)


with tempfile.TemporaryDirectory() as directory:
    root = Path(directory)
    agent = LightAgent(
        model=os.getenv("LIGHTAGENT_MODEL", "deepseek-v4-flash"),
        api_key=os.getenv("LIGHTAGENT_API_KEY", "your_api_key"),
        base_url=os.getenv("LIGHTAGENT_BASE_URL", "your_base_url"),
        session_store=JsonlSessionStore(root / "sessions"),
        budget_limits=BudgetLimits(model_calls=10, tool_calls=20),
        auto_discover_skills=False,
    )

    # A real call persists a complete Turn under this stable Session ID:
    # print(agent.run("Summarize today's work", session_id="demo-session"))

    rag = SqliteFTSRetrievalProvider(root / "knowledge.sqlite3")
    rag.ingest(RetrievalDocument(
        title="Release policy",
        source="docs/release.md",
        content="Every release requires a passing full test suite.",
    ))
    for result in rag.search("release"):
        print(result.citation_id, result.content)
