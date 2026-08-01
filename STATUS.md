# scout-deterministic — status

**Location:** `Neo-lithic/scout-deterministic/` (keep company projects inside the company folder).

**Upstream reference:** `../inspect_Scout/inspect_scout/` (local clone of [inspect_scout](https://github.com/meridianlabs-ai/inspect_scout)).

## Done criteria (from `project-scout-deterministic/00_BUILD_PLAN.md`)

| Criterion | Status | Notes |
|---|---|---|
| `pip install -e .` works | ✅ | Python 3.11 venv |
| Four scanners + unit tests | ✅ | 7+ tests in `tests/` |
| `benchmark/labels.jsonl` 40+ samples | ✅ | 45 labelled |
| `RESULTS.md` with precision/recall/FP/latency | ✅ | v0 replay corpus |
| LLM agreement in `RESULTS.md` | ⏳ | Needs model API key + `scout-det-compare --llm` |
| README Limitations | ✅ | |
| `scout scan` on transcript directory | ⚠️ | Scout CLI needs `.eval` logs; use `python benchmark/run_scout_scan.py` |
| Upstream PR to inspect_scout | 📋 | Draft ready in `upstream/` + `UPSTREAM_PR.md` |
| 40s demo video | 👤 | Human task — see `LAUNCH_TWITTER.md` |

## Remaining (this session)

1. Fix benchmark false positives (`read_after_submit` path heuristic).
2. Scout API integration test + `run_scout_scan.py` runner.
3. Align `llm_scanner` benchmark with Inspect Scout's `reward_hacking()` question.
4. Package upstream PR for `submit_no_exec` + `ground_truth_read`.
5. Regenerate benchmark + `RESULTS.md`.
