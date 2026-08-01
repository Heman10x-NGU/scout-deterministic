# scout-deterministic status

## Blocking review — fixed in code (pending corpus run)

| Item | Status |
|---|---|
| Fixtures moved to `tests/fixtures/synthetic.py` | Done |
| Synthetic `benchmark/generate_corpus.py` removed | Done |
| Synthetic `benchmark/transcripts/` removed | Done |
| `benchmark/generate_real_corpus.py` (live evals) | Done |
| `scout-det-label` interactive CLI | Done |
| Fake precision/recall removed from README | Done |
| Live corpus generated | **Run locally** |
| Human labels (`benchmark/labels.jsonl`) | **Run `scout-det-label`** |
| `scout-det-compare --llm` | After labels |
| Push to GitHub | **Run git commit + push** |

## Quick commands

```bash
cd scout-deterministic
source .venv/bin/activate
pytest -q
python benchmark/generate_real_corpus.py   # ~26 eval logs, uses Remote-jobs/.env MiMo key
scout-det-label                            # you label each sample (~1.5h)
scout-det-compare --llm
scout-det-report
```

Or: `bash scripts/run_benchmark_pipeline.sh`

## Git commit (if not pushed yet)

```bash
git add -A
git commit -m "$(cat <<'EOF'
fix(benchmark): replace synthetic corpus with live agent transcripts

The v0 benchmark generated its corpus from the same fixture functions the
detectors were written against, and described machine-written labels as
hand-labelled. Both are corrected here.

- fixtures moved to tests/, no longer used as benchmark data
- corpus generator for live inspect evals across 5 conditions
- interactive scout-det-label CLI for human ground truth
- compare/report load .eval logs; README and RESULTS restated
EOF
)"
git push origin main
```
