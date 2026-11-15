"""Frozen storage compatibility for v0.12 databases, including detached Jobs."""

# Old rows have no immutability marker. Keep their protection even when the
# optional extension is not installed. New domain policies live in extensions.
LEGACY_IMMUTABLE_KINDS = frozenset({
    "version", "contract_proposal", "contract_revision",
    "instruction_revision", "instruction_request",
})


def read_control_limits(owner):
    """Read saved capacities without rewriting the owner or merging schemas."""
    if not owner:
        return {}
    return owner.get("limits") or owner.get("contract") or {}
