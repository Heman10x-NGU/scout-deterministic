from dataclasses import dataclass


@dataclass(frozen=True)
class Finding:
    """A deterministic detection with pinned evidence."""

    rule_id: str
    step_index: int
    evidence: str
    confidence: float = 1.0
    secondary_index: int | None = None
