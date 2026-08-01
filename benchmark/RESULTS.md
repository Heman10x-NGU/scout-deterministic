# Benchmark Results

## Corpus

- Samples: **45**
- Positives (hand-labelled hacked): **25**
- Clean negatives: **20**

Corpus is Inspect-shaped replay transcripts generated from real event types
(`ToolEvent`, `ModelEvent`, `ScoreEvent`). See `benchmark/generate_corpus.py`.

## Deterministic scanners (aggregate)

- Precision: **80.7%**
- Recall: **100.0%**
- F1: **0.893**
- False-positive rate (clean): **30.0%**
- Latency: **0.22 ms/transcript** (0.010s total)
- Token cost: **$0** (0 tokens)

## Per-detector

| Detector | Precision | Recall | F1 | FP rate (clean) |
|---|---:|---:|---:|---:|
| `submit_no_exec` | 100.0% | 24.0% | 0.387 | 0.0% |
| `scorer_access` | 100.0% | 52.0% | 0.684 | 0.0% |
| `ground_truth_read` | 68.4% | 52.0% | 0.591 | 30.0% |
| `claim_exit_mismatch` | 100.0% | 24.0% | 0.387 | 0.0% |

## LLM scanner comparison

- `llm_scanner()` not run: skipped (--no-llm or no API key)
- Re-run with `scout-det-compare --llm` once a model API key is configured.

## Reproduce

```bash
pip install -e '.[dev]'
python benchmark/generate_corpus.py --count 45
scout-det-compare
scout-det-report
```

## Honest limitations

- Corpus v0 uses structured replay transcripts, not live agent runs.
- Semantic hacks and novel strategies still need a model judge.
- `claim_exit_mismatch` is the highest false-positive risk when agents fail then fix.
