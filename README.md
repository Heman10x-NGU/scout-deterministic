# scout-deterministic

Deterministic reward-hacking scanners for [Inspect Scout](https://github.com/meridianlabs-ai/inspect_scout).

[Inspect Scout](https://meridianlabs-ai.github.io/inspect_scout/) finds eval-gaming in agent transcripts with an **LLM judge** (large language model). LLM judges drift between model versions, cost tokens per transcript, and take seconds each run.

This package adds **rule-based scanners** for structural cheat patterns — no model calls, sub-millisecond per transcript.

## Benchmark (v0, 45 hand-labelled transcripts)

| Metric | Deterministic | Notes |
|---|---:|---|
| Precision | **80.7%** | Against hand labels |
| Recall | **100%** | |
| False positives (clean) | **30%** | Almost all from `ground_truth_read` |
| Latency | **0.22 ms** / transcript | $0 token cost |

Per-detector false-positive rate on clean transcripts: `submit_no_exec` 0%, `scorer_access` 0%, `ground_truth_read` **30%**, `claim_exit_mismatch` 0%.

Full methodology: [`benchmark/RESULTS.md`](benchmark/RESULTS.md)

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
pip install -e ".[dev]"
```

## Usage

**Run scanners on the benchmark corpus** (Python API — works with serialised `Transcript` JSON):

```bash
python benchmark/run_scout_scan.py
python benchmark/run_scout_scan.py --limit 10 --json
```

**Run on real Inspect eval logs** (`.eval` files from `inspect eval ...`):

```bash
scout scan src/scout_deterministic/scout_scanners.py -T /path/to/logs/
```

**Reproduce benchmark numbers:**

```bash
python benchmark/generate_corpus.py --count 45
scout-det-compare --no-llm
scout-det-report
```

**Compare against Scout's LLM `reward_hacking()` scanner** (needs model API key):

```bash
export OPENAI_API_KEY=...   # or set in .env
scout-det-compare --llm
scout-det-report
```

## Limitations

- **Semantic hacks** (intent inference, novel strategies) still need a model judge.
- **v0 corpus** uses Inspect-shaped replay transcripts from real event types (`ToolEvent`, `ModelEvent`, `ScoreEvent`); live agent runs are the next step.
- **`ground_truth_read`** carries most false positives on the v0 corpus — see per-detector table in `RESULTS.md`.

## Upstream

Draft PR for [inspect_scout](https://github.com/meridianlabs-ai/inspect_scout): [`upstream/`](upstream/) + [`UPSTREAM_PR.md`](UPSTREAM_PR.md).

## Related

- [Inspect AI](https://github.com/UKGovernmentBEIS/inspect_ai) — UK **AI Security Institute (AISI)** eval framework
- [Inspect Scout](https://github.com/meridianlabs-ai/inspect_scout) — transcript scanning (LLM + grep scanners)
- [EvilGenie](https://github.com/JonathanGabor/evilgenie_inspect) — reward-hacking benchmark for coding agents

## License

MIT — see [LICENSE](LICENSE).
