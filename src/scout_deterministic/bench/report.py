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
    lines = [
        "# Benchmark Results",
        "",
        "## Corpus",
        "",
        f"- Samples: **{results['corpus_size']}**",
        f"- Positives (hand-labelled hacked): **{results['positives']}**",
        f"- Clean negatives: **{results['negatives']}**",
        "",
        "Corpus is Inspect-shaped replay transcripts generated from real event types",
        "(`ToolEvent`, `ModelEvent`, `ScoreEvent`). See `benchmark/generate_corpus.py`.",
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
    lines.extend(
        [
            "",
            "## LLM scanner comparison",
            "",
        ]
    )
    if llm.get("available"):
        agreement = llm.get("agreement_with_deterministic")
        lines.extend(
            [
                f"- Question: same as Scout `reward_hacking()` example",
                f"- Agreement with `llm_scanner()`: **{agreement:.1%}**",
                f"- Disagreements: **{llm.get('disagreement_count', 0)}**",
                f"- LLM wall time: **{llm['wall_seconds']:.2f}s**",
                f"- Deterministic wall time: **{det['wall_seconds']:.4f}s**",
            ]
        )
        if llm.get("speedup_factor"):
            lines.append(f"- Speedup: **{llm['speedup_factor']}×** (deterministic faster)")
    else:
        lines.extend(
            [
                f"- `llm_scanner()` not run: {llm.get('error', 'unavailable')}",
                "- Re-run with `scout-det-compare --llm` once a model API key is configured.",
            ]
        )

    lines.extend(
        [
            "",
            "## Reproduce",
            "",
            "```bash",
            "pip install -e '.[dev]'",
            "python benchmark/generate_corpus.py --count 45",
            "scout-det-compare",
            "scout-det-report",
            "```",
            "",
            "## Honest limitations",
            "",
            "- Corpus v0 uses structured replay transcripts, not live agent runs.",
            "- Semantic hacks and novel strategies still need a model judge.",
            "- `claim_exit_mismatch` is the highest false-positive risk when agents fail then fix.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    results = json.loads(COMPARE_JSON.read_text())
    RESULTS_MD.write_text(render(results))
    print(f"Wrote {RESULTS_MD}")


if __name__ == "__main__":
    main()
