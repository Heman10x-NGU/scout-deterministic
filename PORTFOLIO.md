# scout-deterministic — portfolio blurb

Use this for applications, LinkedIn, or cold email. Numbers from [`benchmark/RESULTS.md`](benchmark/RESULTS.md) (2026-08-02 run).

---

## One-liner

**Deterministic reward-hacking scanners for Inspect Scout** — rule-based transcript checks that run in ~16ms/sample with $0 API cost, benchmarked on 26 live coding-agent episodes.

---

## Problem

Coding agents optimize for **passing the scorer** (pytest green), not always **solving the task**. Inspect Scout detects this with an **LLM judge** (`llm_scanner`) — slow (~21s/sample in our run), costly, and model-dependent.

---

## What I built

- **4 Scout-integrated scanners** (`ground_truth_read`, `scorer_access`, `submit_no_exec`, `claim_exit_mismatch`)
- **Live benchmark corpus**: 26 DeepSeek agent runs fixing `calc.py` under 5 conditions (readable answer file, impossible test, leading prompt, tight turn budget)
- **Honest measurement**: precision/recall vs labelled transcripts; comparison to Scout's LLM scanner

**Repo:** https://github.com/Heman10x-NGU/scout-deterministic

---

## Results (honest)

| Metric | Deterministic (aggregate) | Scout LLM scanner |
|---|---:|---:|
| Precision vs labels | 54% | 85% |
| Recall vs labels | 100% | 79% |
| Wall time (26 samples) | **0.4s** | **560s** |
| Token cost | **$0** | API spend |

**Lead with limitations (this is the differentiator):**

- `ground_truth_read` **false-alarms** when agents read `tests/test_math.py` (expected value visible) — 100% FP on label-negatives in this corpus
- **Misses** `test_environment_corruption`: agents passed `assert 1 + 1 == 3` with pytest scorer **1.0** — see `benchmark/findings/impossible_000.md`
- **Local sandbox leaked** ground truth between samples — methodology caveat, also a real finding

---

## Why it matters

Shows eval-integrity thinking: not "my tool gets 100% recall," but **here is what structural detection catches, here is what it structurally cannot, with a captured transcript.**

Parallel to BNY work: replaced drifting LLM-as-judge with deterministic claim-coverage checks for financial Q&A.

---

## Stack

Python · Inspect AI · Inspect Scout · pytest agent sandbox · DeepSeek API

---

## 30-second interview answer

> "I built deterministic scanners for agent eval logs — catch answer-file reads and scorer touches without calling an LLM. I ran 26 live agent episodes under hack-inducing conditions. The rules are 1300× faster and free, but I also published where they fail: agents corrupted the Python runtime to pass impossible tests and the scorer still said 1.0. That's the kind of eval gap I'm interested in closing."
