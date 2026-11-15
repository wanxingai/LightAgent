"""Explicit compatibility proxies; ordinary execution uses ExecutionHandle."""
from ..extensions import legacy_export


class _LegacyHandleType(type):
    def __instancecheck__(cls, instance):
        return isinstance(instance, legacy_export(cls.__name__))


class AgentHandle(metaclass=_LegacyHandleType):
    def __new__(cls, *args, **kwargs):
        return legacy_export("AgentHandle")(*args, **kwargs)

    @classmethod
    def connect(cls, *args, **kwargs):
        return legacy_export("AgentHandle").connect(*args, **kwargs)


class ChatHandle(metaclass=_LegacyHandleType):
    def __new__(cls, *args, **kwargs):
        return legacy_export("ChatHandle")(*args, **kwargs)
