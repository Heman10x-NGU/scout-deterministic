"""Shared helpers for building Scout Result objects."""

from __future__ import annotations

from inspect_scout import Reference, Result

from scout_deterministic._findings import Finding


def finding_to_result(finding: Finding, *, label: str) -> Result:
    explanation = finding.evidence
    if finding.secondary_index is not None:
        explanation = (
            f"{finding.evidence} (steps {finding.step_index} and {finding.secondary_index})"
        )
    return Result(
        value=True,
        label=label,
        explanation=explanation,
        references=[
            Reference(
                type="event",
                cite=f"[E{finding.step_index}]",
                id=f"step-{finding.step_index}",
            )
        ],
        metadata={
            "rule_id": finding.rule_id,
            "step_index": finding.step_index,
            "confidence": finding.confidence,
        },
    )


def clean_result(*, label: str) -> Result:
    return Result(value=False, label=label, explanation=None, references=[])
