#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
作者: [weego/WXAI-Team]
最后更新: 2026-02-20
"""

from dataclasses import dataclass
from typing import Any, Protocol


class MemoryProtocol(Protocol):
    """记忆存储与检索协议"""
    def store(self, data: str, user_id: str) -> Any:
        ...

    def retrieve(self, query: str, user_id: str) -> Any:
        ...


@dataclass(frozen=True)
class MemoryPolicy:
    """Optional safety policy for shared memory backends."""

    namespace: str | None = None
    allow_unattributed_results: bool = True

    def scoped_user_id(self, user_id: str) -> str:
        user = str(user_id)
        if not self.namespace:
            return user
        return f"{self.namespace}:{user}"

    def allows_result(self, item: Any, scoped_user_id: str, original_user_id: str) -> bool:
        """Return whether a retrieved memory item can be injected into context."""
        if not isinstance(item, dict):
            return self.allow_unattributed_results

        metadata = item.get("metadata") if isinstance(item.get("metadata"), dict) else {}
        item_user_id = (
            item.get("user_id")
            or item.get("userId")
            or metadata.get("user_id")
            or metadata.get("userId")
        )
        if item_user_id is None:
            return self.allow_unattributed_results

        allowed = {str(original_user_id), str(scoped_user_id)}
        return str(item_user_id) in allowed
