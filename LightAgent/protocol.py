#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
作者: [weego/WXAI-Team]
最后更新: 2026-02-20
"""

from typing import List, Any, Protocol


class MemoryProtocol(Protocol):
    """记忆存储与检索协议"""
    def store(self, data: str, user_id: str) -> Any:
        ...

    def retrieve(self, query: str, user_id: str) -> List[Any]:
        ...