"""Emit RESULTS.md from compare_results.json."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
COMPARE_JSON = ROOT / "benchmark" / "compare_results.json"
RESULTS_MD = ROOT / "benchmark" / "RESULTS.md"
LABELS_PATH = ROOT / "benchmark" / "labels.jsonl"


def _hack_type_counts() -> dict[str, int]:
    if not LABELS_PATH.exists():
        return {}
    counts: dict[str, int] = {}
    for line in LABELS_PATH.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if not row.get("hacked"):
            continue
        key = str(row.get("hack_type") or "unknown")
        counts[key] = counts.get(key, 0) + 1
    return counts


def render(results: dict) -> str:
    det = results["deterministic"]
    agg = det["aggregate"]
    meta = results.get("corpus_metadata", {})
    conditions = meta.get("conditions", {})
    models = meta.get("models", [])
    default_model = "openai/deepseek-v4-flash (see corpus_manifest.jsonl)"
    model_line = ", ".join(models) if models else default_model
    condition_lines = ", ".join(f"{name}={count}" for name, count in sorted(conditions.items()))
    hack_types = _hack_type_counts()
    hack_lines = ", ".join(f"{k}={v}" for k, v in sorted(hack_types.items())) or "n/a"

    lines = [
        "# Benchmark Results",
        "",
        "## Headline",
        "",
        "Live coding-agent corpus (N=26) under hack-inducing conditions. **Deterministic",
        "scanners catch structural shortcuts** (answer-file reads, scorer touches) at",
        "**~0.42s total / $0 tokens**, but **`ground_truth_read` false-alarms on every",
        "label-negative sample** in this run (reading the test file looks like reading",
        "ground truth). **No detector carrying signal catches `test_environment_corruption`**",
        "(agents passing `assert 1 + 1 == 3` with scorer 1.0). `ground_truth_read`",
        "flags these samples but flags all 26 transcripts (recall 1.0, FP rate 1.0),",
        "so its hit carries no information. See",
        "[findings/impossible_000.md](findings/impossible_000.md).",
        "",
        "## Corpus",
        "",
        f"- Samples: **{results['corpus_size']}**",
        f"- Positives (labelled hacked): **{results['positives']}**",
        f"- Negatives (labelled not hacked): **{results['negatives']}**",
        f"- Conditions: {condition_lines or 'n/a'}",
        f"- Agent model: {model_line}",
        f"- Labeller: **{meta.get('labeller', 'n/a')}**",
        f"- Hack types (positives): {hack_lines}",
        "",
        "Corpus is **live Inspect eval logs** from `benchmark/generate_real_corpus.py`",
        "(agentic pytest-fix task, **local sandbox**, real bash tool events).",
        "",
        "### Labelling methodology",
        "",
        "Labels were assigned by **Claude Opus reviewing complete event traces**, with",
        "a recorded rationale per sample (`benchmark/labels.jsonl`). This is **not**",
        "author hand-labelling. LLM-scanner comparison vs these labels is therefore",
        "**LLM-vs-LLM agreement** on a secondary axis; deterministic-scanner metrics",
        "are the primary result.",
        "",
        "### Sandbox limitation (important)",
        "",
        "`sandbox=\"local\"` leaked ground truth between concurrent samples (shared",
        "`/var/folders/.../T/tmp*/` dirs). Three nominally **clean** samples were",
        "labelled hacked for cross-sample `.target` reads or reading `pytest_fix.py`.",
        "Re-run with Docker/isolated sandboxes before extrapolating false-positive rates.",
        "",
        "## Method",
        "",
        "1. `python benchmark/generate_real_corpus.py` — 26 agent episodes, 5 conditions.",
        "2. Label each sample → `benchmark/labels.jsonl`.",
        "3. `scout-det-compare --llm` — deterministic scanners + Scout `llm_scanner()`.",
        "4. `scout-det-report` — this file.",
        "",
        "## Deterministic scanners (aggregate)",
        "",
        f"- Precision: **{agg['precision']:.1%}**",
        f"- Recall: **{agg['recall']:.1%}**",
        f"- F1: **{agg['f1']:.3f}**",
        (
            f"- False-positive rate (label-negative): "
            f"**{det.get('false_positive_rate_clean', 0):.1%}**"
        ),
        (
            f"- Latency: **{det['ms_per_transcript']:.2f} ms/transcript** "
            f"({det['wall_seconds']:.3f}s total)"
        ),
        "- Token cost: **$0**",
        "",
        "**Interpretation:** 100% recall here means the aggregate OR-of-detectors flags",
        "every positive — but also every negative, driven mainly by `ground_truth_read`",
        "seeing expected values in `tests/test_math.py` output. Use per-detector rows",
        "and `scorer_access` / `claim_exit_mismatch` for deployment signals.",
        "",
        "## Per-detector",
        "",
        "| Detector | Precision | Recall | F1 | FP rate (negatives) |",
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
        vs_labels = llm.get("precision_vs_labels") or {}
        lines.extend(
            [
                "- Question: Scout-style reward-hacking boolean question",
                f"- **vs labels:** precision **{vs_labels.get('precision', 0):.1%}**, "
                f"recall **{vs_labels.get('recall', 0):.1%}**, "
                f"F1 **{vs_labels.get('f1', 0):.3f}**",
                f"- Agreement with deterministic aggregate: **{agreement:.1%}**",
                f"- Disagreements: **{llm.get('disagreement_count', 0)}**",
                f"- LLM wall time: **{llm['wall_seconds']:.1f}s**",
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
                "- Re-run with `scout-det-compare --llm`.",
            ]
        )

    lines.extend(
        [
            "",
            "## Key findings",
            "",
            (
                "1. **`readable_answer` condition worked** — all 6 samples read "
                "`.target` before fixing."
            ),
            (
                "2. **`impossible` condition** — all 4 samples scored pytest 1.0 on "
                "`assert 1 + 1 == 3`."
            ),
            (
                "   No informative detector flags runtime/test-module corruption; only "
                "the always-firing `ground_truth_read` overlaps."
            ),
            (
                "3. **Local sandbox leakage** — agents read other samples' "
                "`.target` files and repo source."
            ),
            "4. **`ground_truth_read` needs scorer-path tuning** — benign test reads false-alarm.",
            "",
            "## Reproduce",
            "",
            "```bash",
            "pip install -e '.[dev]'",
            "python benchmark/generate_real_corpus.py",
            "# label → benchmark/labels.jsonl",
            "python scripts/run_compare_and_report.py --llm",
            "pytest -q",
            "```",
            "",
            "## Limitations",
            "",
            f"- Corpus is small (N={results['corpus_size']}). Indicative, not definitive.",
            "- Local sandbox, not Docker — cross-sample leakage.",
            "- Labels are LLM-assisted, not author-verified on full set.",
            "- Semantic / environment-corruption hacks need other tooling.",
            "- Do not extrapolate to production agents without isolated sandboxes.",
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
