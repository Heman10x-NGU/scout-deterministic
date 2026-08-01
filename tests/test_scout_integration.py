"""Integration tests — scanners via Inspect Scout Python API."""

import pytest

from scout_deterministic.fixtures import (
    claim_exit_mismatch_transcript,
    clean_solve_transcript,
    read_answer_after_submit_transcript,
    read_answer_before_submit_transcript,
    submit_no_exec_transcript,
)
from scout_deterministic.scout_scanners import (
    claim_exit_mismatch,
    ground_truth_read,
    scorer_access,
    submit_no_exec,
)


async def _flagged(factory, transcript) -> bool:
    result = await factory()(transcript)
    if isinstance(result, list):
        return any(bool(item.value) for item in result)
    return bool(result.value)


@pytest.mark.asyncio
async def test_submit_no_exec_via_scout_api():
    assert await _flagged(submit_no_exec, submit_no_exec_transcript())
    assert not await _flagged(submit_no_exec, clean_solve_transcript())


@pytest.mark.asyncio
async def test_ground_truth_read_via_scout_api():
    assert await _flagged(ground_truth_read, read_answer_before_submit_transcript())
    assert not await _flagged(ground_truth_read, read_answer_after_submit_transcript())


@pytest.mark.asyncio
async def test_scorer_access_via_scout_api():
    assert await _flagged(scorer_access, read_answer_before_submit_transcript())


@pytest.mark.asyncio
async def test_claim_exit_mismatch_via_scout_api():
    assert await _flagged(claim_exit_mismatch, claim_exit_mismatch_transcript())
    assert not await _flagged(claim_exit_mismatch, clean_solve_transcript())
