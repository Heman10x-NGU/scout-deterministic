# scout-deterministic

Deterministic reward-hacking scanners for [Inspect Scout](https://github.com/meridianlabs-ai/inspect_scout).

[Inspect Scout](https://meridianlabs-ai.github.io/inspect_scout/) finds eval-gaming in agent transcripts with an **LLM judge** (large language model). LLM judges drift between model versions, cost tokens per transcript, and take seconds each run.

This package adds **rule-based scanners** for structural cheat patterns — no model calls, sub-millisecond per transcript.

## Benchmark

Benchmark numbers are generated from **live agent runs**, not synthetic fixtures. See [`benchmark/RESULTS.md`](benchmark/RESULTS.md) after you complete labelling and comparison.

```bash
python benchmark/generate_real_corpus.py   # 26 live eval logs across 5 conditions
scout-det-label                          # human labels (required)
scout-det-compare --llm                  # deterministic vs LLM judge
scout-det-report                         # writes RESULTS.md
```

*Corpus is small (~26 samples). Numbers are indicative, not definitive.*

## Fixtures vs benchmark

| | Fixtures (`tests/fixtures/`) | Benchmark (`benchmark/`) |
|---|---|---|
| Purpose | Verify each detector fires on a constructed case | Measure behaviour on real agent runs |
| Data | Synthetic `Transcript` JSON built from Inspect event types | Live `.eval` logs from `inspect eval` |
| Labels | Not used | Hand-written per sample via `scout-det-label` |

Do not use fixture transcripts as benchmark scores.

## Scanners

| Scanner | Detects |
|---|---|
| `scorer_access` | Agent read/wrote scorer-dependent files |
| `ground_truth_read` | Ground-truth / answer path accessed **before** submit |
| `claim_exit_mismatch` | Success claim after failed shell command (rerun suppression) |
| `submit_no_exec` | Final submit with no prior shell execution |

## Install

```bash
git clone https://github.com/Heman10x-NGU/scout-deterministic.git
cd scout-deterministic
python3.11 -m venv .venv && source .venv/bin/activate
python -m pip install -e ".[dev]"
```

## Usage

**Run scanners on fixture transcripts** (unit-test JSON under `tests/fixtures/transcripts/`):

```bash
pytest
```

**Run on real Inspect eval logs** (`.eval` files from `inspect eval ...`):

```bash
scout scan src/scout_deterministic/scout_scanners.py -T benchmark/raw_logs/
```

## Limitations

- **Semantic hacks** (intent inference, novel strategies) still need a model judge.
- **`ground_truth_read`** may false-positive on benign reads before submit.
- **Benchmark corpus** is intentionally small; regenerate with harsher conditions if needed.

## Upstream

Draft PR for [inspect_scout](https://github.com/meridianlabs-ai/inspect_scout): [`upstream/`](upstream/) + [`UPSTREAM_PR.md`](UPSTREAM_PR.md).

## Related

- [Inspect AI](https://github.com/UKGovernmentBEIS/inspect_ai) — UK **AI Security Institute (AISI)** eval framework
- [Inspect Scout](https://github.com/meridianlabs-ai/inspect_scout) — transcript scanning (LLM + grep scanners)
- [EvilGenie](https://github.com/JonathanGabor/evilgenie_inspect) — reward-hacking benchmark for coding agents

## License

MIT — see [LICENSE](LICENSE).
