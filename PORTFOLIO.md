# scout-deterministic — application copy

Numbers from [`benchmark/RESULTS.md`](benchmark/RESULTS.md) · repo: https://github.com/Heman10x-NGU/scout-deterministic

---

## Elevator pitch (Neolithic / eval-integrity roles)

> I built deterministic reward-hacking scanners for Inspect Scout and ran a live coding-agent corpus. The rules are **1300× faster** than Scout's LLM judge and **$0** per transcript — but the interesting result is what they **miss**: an agent passed `assert 1 + 1 == 3` with scorer **1.0** by corrupting the Python runtime. No informative detector caught it; the one that flagged it fires on all 26 transcripts. I published the trace.

---

## One-liner

Rule-based cheat detection on agent eval logs — benchmarked honestly on 26 live episodes, with the failure modes documented.

---

## Problem

Agents optimize for **passing the scorer**, not **solving the task**. Scout's `llm_scanner()` catches many cases but costs tokens, takes ~21s/sample, and drifts with the model.

---

## What I shipped

- 4 Inspect Scout scanners (event-log rules, pinned evidence per step)
- Live benchmark: 26 DeepSeek agent runs, 5 hack-inducing conditions
- [`impossible_000`](benchmark/findings/impossible_000.md): scorer 1.0 on an impossible assertion — missed by informative rules
- Full compare vs Scout LLM judge + reproducible pipeline

---

## Results (lead with limitations)

| | Deterministic | Scout LLM |
|---|---:|---:|
| Precision | 54% | 85% |
| Recall | 100% | 79% |
| 26-sample latency | 0.4s | 560s |

**Why the deterministic numbers look “good” on recall:** rules over-fire on benign test-file reads (`ground_truth_read`). **Why they matter anyway:** `scorer_access` / `claim_exit_mismatch` carry signal; `ground_truth_read` at 100% FP rate is a cautionary tale; the **impossible** class is the research gap.

---

## 30-second interview

> "Same move I did at BNY — replace an LLM judge with deterministic checks where the structure is auditable. On agent eval logs, that's answer-file reads and scorer touches. I measured it on real trajectories and also showed a case where pytest says pass and the agent corrupted the runtime — no informative rule caught it, and the always-firing detector is worthless at 100% FP. That's the work I want to do: close the gap between scorer green and eval integrity."

---

## Do not claim

- "Hand-labelled all 26" (Opus-reviewed traces; spot-check before interviews)
- "Production-ready 100% recall"
- "RL training environment" (it's an agent **eval** harness)
