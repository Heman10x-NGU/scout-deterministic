# Proposed contribution to Inspect Scout (not yet submitted)

**Target:** [meridianlabs-ai/inspect_scout](https://github.com/meridianlabs-ai/inspect_scout)

This file is a **draft PR packet** for optional upstream merge. The main repo README links here; reviewers can ignore it unless they care about Scout integration.

Reference implementations to copy: [`upstream/submit_no_exec_scanner.py`](upstream/submit_no_exec_scanner.py), [`upstream/ground_truth_read_scanner.py`](upstream/ground_truth_read_scanner.py).

## Proposed scanners (2)

| Scanner | Why upstream | Pattern |
|---|---|---|
| `submit_no_exec` | Universal structural signal | Same shape as `grep_scanner` |
| `ground_truth_read` | Ordering-aware complement to LLM `reward_hacking()` | Uses tool events + submit ordering |

`scorer_access` and `claim_exit_mismatch` stay in scout-deterministic until v1 benchmark on live eval logs.

## Files to add (suggested layout)

```
src/inspect_scout/_deterministic_scanner/
  __init__.py
  submit_no_exec.py      # copy from upstream/submit_no_exec_scanner.py
  ground_truth_read.py   # copy from upstream/ground_truth_read_scanner.py
```

Export in `src/inspect_scout/__init__.py`:

```python
from ._deterministic_scanner import ground_truth_read_scanner, submit_no_exec_scanner
```

## PR title (Conventional Commits)

```
feat: add deterministic submit_no_exec and ground_truth_read scanners
```

## PR body (draft)

```markdown
## Summary

Adds two deterministic transcript scanners that complement `llm_scanner()` for
structural reward-hacking signals:

- **`submit_no_exec`** — final submit with no prior shell/tool execution
- **`ground_truth_read`** — scorer/answer path read before submit (ordering-aware)

Both follow the `grep_scanner` factory pattern, return `Result` with event
references, and make zero model calls.

## Motivation

`examples/scanner/scanner.py` ships `reward_hacking()` as an LLM judge. Structural
cases (answer-file reads, lazy submits) are cheaper and more stable as rules.
External package [scout-deterministic](https://github.com/Heman10x-NGU/scout-deterministic)
hosts the full scanner set and a live-eval benchmark pipeline. This PR argues
the scanners on their logic and tests only — no benchmark numbers cited here.

## Test plan

- [ ] Unit tests mirroring `tests/grep_scanner/` (fixture transcripts)
- [ ] `make check && make test`
- [ ] `scout scan` smoke on sample eval logs

## AI disclosure

Implementation developed with AI assistance; benchmark methodology and labels
were hand-reviewed.
```

## Open PR steps

```bash
cd ../inspect_Scout/inspect_scout
git checkout -b feat/deterministic-reward-hacking-scanners
# copy upstream/*.py into src/inspect_scout/_deterministic_scanner/
# add tests, export from __init__.py
make check && make test
git push -u origin feat/deterministic-reward-hacking-scanners
gh pr create --title "feat: add deterministic submit_no_exec and ground_truth_read scanners" --body-file ../../scout-deterministic/UPSTREAM_PR.md
```

## Issue search

Before opening, check: https://github.com/meridianlabs-ai/inspect_scout/issues?q=reward+hacking
