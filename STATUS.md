# scout-deterministic — DONE

| Item | Status |
|---|---|
| Scanners + tests | Done (`pytest` green) |
| Live corpus (26 samples) | Done (`benchmark/corpus_manifest.jsonl`) |
| Labels | Done (`benchmark/labels.jsonl`, 14 hacked / 12 not) |
| `scout-det-compare --llm` | Done (`benchmark/compare_results.json`) |
| `RESULTS.md` | Done |
| `PORTFOLIO.md` | Done — copy for other applications |
| `benchmark/findings/impossible_000.md` | Done |
| Push to GitHub | **You:** `git add -A && git commit && git push` |

## Final commands (already run)

```bash
python scripts/run_compare_and_report.py --llm   # compare + RESULTS.md
pytest -q
```

## Apply elsewhere

1. Link repo: https://github.com/Heman10x-NGU/scout-deterministic
2. Paste from `PORTFOLIO.md` (one-liner + honest results table)
3. Lead with **limitations + impossible_000** — shows eval integrity thinking
4. Optional: spot-check 5 labels before interviews (`impossible_000`, `clean_001`, `clean_003`, `readable_answer_000`, `leading_prompt_003`)

## Honest claims only

- Labels: Claude Opus reviewed traces (not "I hand-labelled all 26")
- Do not claim 100% production-ready detection — FP rate on negatives is 100% for aggregate rule OR
- Do claim: 1300× faster than LLM scanner, real corpus, published misses
