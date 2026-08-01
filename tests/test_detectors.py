
from scout_deterministic._transcript import SHELL_TOOLS, normalise
from fixtures.synthetic import (
    claim_exit_fixed_transcript,
    claim_exit_mismatch_transcript,
    clean_solve_transcript,
    read_answer_after_submit_transcript,
    read_answer_before_submit_transcript,
    scorer_access_transcript,
    submit_no_exec_transcript,
)
from scout_deterministic.scanners._detect import (
    detect_claim_exit_mismatch,
    detect_ground_truth_read,
    detect_scorer_access,
    detect_submit_no_exec,
)


def test_normalise_includes_tool_model_and_submit():
    events = normalise(clean_solve_transcript())
    kinds = {event.kind for event in events}
    assert "tool" in kinds
    assert "submit" in kinds


def test_submit_no_exec_flags_laziest_hack():
    events = normalise(submit_no_exec_transcript())
    finding = detect_submit_no_exec(events, shell_tools=SHELL_TOOLS)
    assert finding is not None
    assert finding.rule_id == "submit_no_exec"


def test_submit_no_exec_ignores_clean_run():
    events = normalise(clean_solve_transcript())
    assert detect_submit_no_exec(events, shell_tools=SHELL_TOOLS) is None


def test_scorer_access_flags_answer_file_read():
    events = normalise(scorer_access_transcript())
    finding = detect_scorer_access(events, patterns=(r"expected", r"answer"))
    assert finding is not None


def test_ground_truth_read_requires_ordering():
  before = normalise(read_answer_before_submit_transcript())
  after = normalise(read_answer_after_submit_transcript())
  assert detect_ground_truth_read(before, patterns=(r"target",), targets=["golden-answer"])
  assert detect_ground_truth_read(after, patterns=(r"target",), targets=["golden-answer"]) is None


def test_claim_exit_mismatch_flags_fail_then_claim():
    events = normalise(claim_exit_mismatch_transcript())
    assert detect_claim_exit_mismatch(events) is not None


def test_claim_exit_mismatch_suppresses_after_successful_rerun():
    events = normalise(claim_exit_fixed_transcript())
    assert detect_claim_exit_mismatch(events) is None
