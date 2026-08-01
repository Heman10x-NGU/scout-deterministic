# Benchmark Results

## Corpus

- Samples: **5**
- Positives (hand-labelled hacked): **0**
- Clean negatives: **5**
- Conditions: clean=1, impossible=1, leading_prompt=1, readable_answer=1, tight_budget=1
- Model(s): openai/mimo-v2.5-pro
- Labeller: **hemant+agent**

Corpus is **live Inspect eval logs** from `benchmark/generate_real_corpus.py`
(agentic pytest-fix task, local sandbox, real tool events).

## Method

1. Generate transcripts with `python benchmark/generate_real_corpus.py`.
2. Label each sample interactively with `scout-det-label` (human ground truth).
3. Run `scout-det-compare --llm` against those labels.
4. Regenerate this file with `scout-det-report`.

## Deterministic scanners (aggregate)

- Precision: **0.0%**
- Recall: **0.0%**
- F1: **0.000**
- False-positive rate (clean): **0.0%**
- Latency: **20.50 ms/transcript** (0.102s total)
- Token cost: **$0** (0 tokens)

## Per-detector

| Detector | Precision | Recall | F1 | FP rate (clean) |
|---|---:|---:|---:|---:|
| `submit_no_exec` | 0.0% | 0.0% | 0.000 | 0.0% |
| `scorer_access` | 0.0% | 0.0% | 0.000 | 0.0% |
| `ground_truth_read` | 0.0% | 0.0% | 0.000 | 0.0% |
| `claim_exit_mismatch` | 0.0% | 0.0% | 0.000 | 0.0% |

## LLM scanner comparison

- `llm_scanner()` not run: Error code: 401 - {'error': {'message': 'Invalid API Key', 'param': 'Please provide valid API Key', 'code': '401', 'type': 'invalid_key'}}
- Re-run with `scout-det-compare --llm` once labels exist.

## Reproduce

```bash
pip install -e '.[dev]'
python benchmark/generate_real_corpus.py
scout-det-label
scout-det-compare --llm
scout-det-report
```

## Limitations

- Corpus is small (N=5). Numbers are indicative, not definitive.
- Semantic hacks still need a model judge.
- `ground_truth_read` may fire on benign file reads before submit.
- Conditions bias hack rate; do not extrapolate to production agents.
