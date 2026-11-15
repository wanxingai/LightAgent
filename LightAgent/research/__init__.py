"""Reproducible research inputs and deterministic, host-owned evaluation."""
from ..extensions import legacy_export


def __getattr__(name):
    if name in ("ResearchContract", "ResearchEvaluator", "PromotionPolicy", "snapshot_workspace"):
        return legacy_export(name)
    raise AttributeError(name)

__all__=['ResearchContract','ResearchEvaluator','PromotionPolicy','snapshot_workspace']
