"""Emit RESULTS.md from compare_results.json."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
COMPARE_JSON = ROOT / "benchmark" / "compare_results.json"
RESULTS_MD = ROOT / "benchmark" / "RESULTS.md"


def render(results: dict) -> str:
    det = results["deterministic"]
    agg = det["aggregate"]
    meta = results.get("corpus_metadata", {})
    conditions = meta.get("conditions", {})
    models = meta.get("models", [])
    model_line = ", ".join(models) if models else "see labels.jsonl"
    condition_lines = ", ".join(f"{name}={count}" for name, count in sorted(conditions.items()))

    lines = [
        "# Benchmark Results",
        "",
        "## Corpus",
        "",
        f"- Samples: **{results['corpus_size']}**",
        f"- Positives (hand-labelled hacked): **{results['positives']}**",
        f"- Clean negatives: **{results['negatives']}**",
        f"- Conditions: {condition_lines or 'n/a'}",
        f"- Model(s): {model_line}",
        f"- Labeller: **{meta.get('labeller', 'n/a')}**",
        "",
        "Corpus is **live Inspect eval logs** from `benchmark/generate_real_corpus.py`",
        "(agentic pytest-fix task, local sandbox, real tool events).",
        "",
        "## Method",
        "",
        "1. Generate transcripts with `python benchmark/generate_real_corpus.py`.",
        "2. Label each sample interactively with `scout-det-label` (human ground truth).",
        "3. Run `scout-det-compare --llm` against those labels.",
        "4. Regenerate this file with `scout-det-report`.",
        "",
        "## Deterministic scanners (aggregate)",
        "",
        f"- Precision: **{agg['precision']:.1%}**",
        f"- Recall: **{agg['recall']:.1%}**",
        f"- F1: **{agg['f1']:.3f}**",
        f"- False-positive rate (clean): **{det.get('false_positive_rate_clean', 0):.1%}**",
        (
            f"- Latency: **{det['ms_per_transcript']:.2f} ms/transcript** "
            f"({det['wall_seconds']:.3f}s total)"
        ),
        "- Token cost: **$0** (0 tokens)",
        "",
        "## Per-detector",
        "",
        "| Detector | Precision | Recall | F1 | FP rate (clean) |",
        "|---|---:|---:|---:|---:|",
    ]
    for name, stats in det["per_detector"].items():
        lines.append(
            f"| `{name}` | {stats['precision']:.1%} | {stats['recall']:.1%} | "
            f"{stats['f1']:.3f} | {stats['false_positive_rate_clean']:.1%} |"
        )

    llm = results.get("llm_scanner", {})
    lines.extend(["", "## LLM scanner comparison", ""])
    if llm.get("available"):
        agreement = llm.get("agreement_with_deterministic")
        lines.extend(
            [
                f"- Question: Scout-style reward-hacking boolean question",
                f"- Agreement with deterministic aggregate: **{agreement:.1%}**",
                f"- Disagreements: **{llm.get('disagreement_count', 0)}**",
                f"- LLM wall time: **{llm['wall_seconds']:.2f}s**",
                f"- Deterministic wall time: **{det['wall_seconds']:.4f}s**",
            ]
        )
        if llm.get("speedup_factor"):
            lines.append(f"- Speedup: **{llm['speedup_factor']}×** (deterministic faster)")
        disagreements = llm.get("disagreements") or []
        if disagreements:
            lines.extend(["", "### Disagreements (sample)", ""])
            for row in disagreements[:10]:
                lines.append(
                    f"- `{row['sample_id']}` label={row['label_hacked']} "
                    f"det={row['deterministic']} llm={row['llm_scanner']}"
                )
    else:
        lines.extend(
            [
                f"- `llm_scanner()` not run: {llm.get('error', 'unavailable')}",
                "- Re-run with `scout-det-compare --llm` once labels exist.",
            ]
        )

    lines.extend(
        [
            "",
            "## Reproduce",
            "",
            "```bash",
            "pip install -e '.[dev]'",
            "python benchmark/generate_real_corpus.py",
            "scout-det-label",
            "scout-det-compare --llm",
            "scout-det-report",
            "```",
            "",
            "## Limitations",
            "",
            f"- Corpus is small (N={results['corpus_size']}). Numbers are indicative, not definitive.",
            "- Semantic hacks still need a model judge.",
            "- `ground_truth_read` may fire on benign file reads before submit.",
            "- Conditions bias hack rate; do not extrapolate to production agents.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    if not COMPARE_JSON.exists():
        raise SystemExit("Run scout-det-compare first.")
    results = json.loads(COMPARE_JSON.read_text(encoding="utf-8"))
    RESULTS_MD.write_text(render(results), encoding="utf-8")
    print(f"Wrote {RESULTS_MD}")


if __name__ == "__main__":
    main()
