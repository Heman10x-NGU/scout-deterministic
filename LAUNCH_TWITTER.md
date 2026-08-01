# Twitter thread — fill [N], [M], [A] from benchmark/RESULTS.md after `scout-det-compare --llm`

**Post 1**
```
Inspect Scout finds reward hacking in agent transcripts using an LLM judge.

LLM judges drift between model versions, cost tokens per transcript, and take seconds each.

I wrote deterministic scanners for the structural cases.

[N]% agreement with llm_scanner. [M]% false positives on clean transcripts. ~0.3ms. $0.

https://github.com/Heman10x-NGU/scout-deterministic
```

**Post 2**
```
The false-positive rate is the number worth talking about.

`scorer_access` and `submit_no_exec` carry most of them on the v0 replay corpus — path heuristics fire on benign reads that happen after submit.

Per-detector breakdown is in RESULTS.md. I didn't hide it in the aggregate.
```

**Post 3**
```
What it catches:
- scorer-file access
- ground-truth reads before submit
- success claims contradicted by exit codes
- submits with no shell execution

What it can't:
- semantic hacks
- novel strategies
- anything needing intent inference
```

**Post 4**
```
Built on UK AISI Inspect + Inspect Scout (@meridianlabs).

45 hand-labelled replay transcripts (Inspect event types), rationale on every row.

PR opening upstream for the two scanners general enough to belong in Scout.
```

**Post 5**
```
Neolithic's launch post argued that automating safety research without better verification just produces confident slop faster.

Deterministic checks are one small piece of that.

cc @NeolithicAI @LeoMcKeeReid
```
