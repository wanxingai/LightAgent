"""The old persistent mode remains an explicit research extension contract."""
from ..extensions import require_extension


def persistent_run(*args, **kwargs):
    return require_extension("research").persistent_run(*args, **kwargs)
