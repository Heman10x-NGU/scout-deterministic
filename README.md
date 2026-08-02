# scout-deterministic

Deterministic reward-hacking scanners for [Inspect Scout](https://github.com/meridianlabs-ai/inspect_scout).

[Inspect Scout](https://meridianlabs-ai.github.io/inspect_scout/) finds eval-gaming in agent transcripts with an **LLM judge** (large language model). LLM judges drift between model versions, cost tokens per transcript, and take seconds each run.

This package adds **rule-based scanners** for structural cheat patterns — no model calls, sub-millisecond per transcript.

## Results (live benchmark, N=26)

| | Deterministic scanners | Scout `llm_scanner()` |
|---|---:|---:|
| Precision vs labels | 54% | 85% |
| Recall vs labels | 100% | 79% |
| Latency (26 samples) | **0.4s** | **560s** |
| Cost | **$0** | API tokens |

Full methodology, limitations, and the **`impossible_000`** finding (agent passed `assert 1+1==3`, scorer 1.0): **[`benchmark/RESULTS.md`](benchmark/RESULTS.md)** · [`benchmark/findings/impossible_000.md`](benchmark/findings/impossible_000.md)

**Portfolio blurb:** [`PORTFOLIO.md`](PORTFOLIO.md)

## Benchmark pipeline

```bash
python benchmark/generate_real_corpus.py   # 26 live eval logs, 5 conditions
# → benchmark/labels.jsonl (see RESULTS.md for labelling methodology)
python scripts/run_compare_and_report.py --llm
pytest -q
```

*Corpus is small (26 samples). Numbers are indicative; limitations are documented.*

## Fixtures vs benchmark

| | Fixtures (`tests/fixtures/`) | Benchmark (`benchmark/`) |
|---|---|---|
| Purpose | Verify each detector fires on a constructed case | Measure behaviour on real agent runs |
| Data | Synthetic `Transcript` JSON | Live `.eval` logs from `inspect eval` |
| Labels | Not used | LLM-reviewed traces in `labels.jsonl` |

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

```bash
pytest
scout scan src/scout_deterministic/scout_scanners.py -T benchmark/raw_logs/
```

## Limitations

- **Semantic / runtime-corruption hacks** need other tooling (see `impossible_000` finding).
- **`ground_truth_read`** false-positives when expected values appear in test file output.
- **Local sandbox** leaked ground truth between samples in the benchmark run.
- Small corpus — regenerate with Docker sandboxes for stricter FP rates.

## Upstream

Draft PR for [inspect_scout](https://github.com/meridianlabs-ai/inspect_scout): [`upstream/`](upstream/) + [`UPSTREAM_PR.md`](UPSTREAM_PR.md).

## Related

- [Inspect AI](https://github.com/UKGovernmentBEIS/inspect_ai) — UK **AI Security Institute (AISI)** eval framework
- [Inspect Scout](https://github.com/meridianlabs-ai/inspect_scout) — transcript scanning
- [EvilGenie](https://github.com/JonathanGabor/evilgenie_inspect) — reward-hacking benchmark for coding agents

## License

MIT — see [LICENSE](LICENSE).
