# R0 v0.3 isolated process peak-RSS diagnostic (Issue #12)

Status: **PREREGISTERED BEFORE MEASUREMENT; EXPLORATORY RUN COMPLETED 2026-10-22; R0 STILL OPEN**. The first code/protocol commit `279c6cb7172d43004ae621db36a5466c1db82894` was created before any study timings. This is a bounded follow-up to the R0 v0.2 integrated Python control, not a native Rust GO or an independent allocator attribution result.

## Question and protocol

Can generator/list signature composition be compared for process-scoped peak RSS without conflating successive trials' Python process high-water marks?

- Frozen manifest: [`native-rss-control.v0.3.json`](../../experiments/native-rss-control.v0.3.json), pinned to baseline main `dfd0b7b44d08358808b02e9a87b218f4b6c24311`.
- Six unchanged v0.2 workloads, seeds `0,1,2`, two repetitions and two Python arms. Pair order alternates by seed and repetition. All 72 child processes run even if outcomes are `UNKNOWN` or `SEARCH_ONLY`, unless a child errors or logical parity fails.
- Each arm runs exactly one bounded `run_workload` in a **fresh Python subprocess**. `ru_maxrss` is recorded before and after it, in bytes. Its maximum includes interpreter, imports, allocator high-water and workload. It is **not** the workload's heap-only peak, an allocation count, a native extension measurement, or an OS-enforced sandbox.
- Measure child process wall separately from existing workload timing. Their difference includes imports, startup, JSON, process exit and scheduling; do not interpret it as startup alone. Process-scoped RSS is descriptive. Small same-host repeats do not justify p95 or significance.
- Child invocation uses a fixed Python module and frozen workload/seed/arm IDs. It has no arbitrary code or path argument; independent verifier and default generator remain unchanged.
- Record canonical per-arm logical results and hashes, environment, source/lock/CI hashes **and genome/world/schema file hashes**. A mismatch must stop the study and retain completed pairs and the failing pair's available samples. Output must be a new file.
- If platform RSS is unsupported, record `NOT_MEASURED`; no fabricated cross-platform result. Shared-host interference is uncontrolled. No performance selection or R1 native GO follows, even if a memory number appears better.

## Reproduction and decision

```bash
python -m experiments.native_rss_control --output runs/new-r0-rss-control.json
python -m pytest -q tests/test_native_rss_control.py
```

Decision remains **`ITERATE_R0_NO_NATIVE_GO`**. Remaining gates: tuple/allocation/dedup attribution, compute-heavy full-lifecycle matched workload, controlled-host confirmation and later native conversion/FFI costs if independently approved. Historical R0 evidence is immutable.

## Exploratory observations collected after preregistration

Raw evidence: [`r0-rss-20261022.json.gz`](../../experiments/native/r0-rss-20261022.json.gz), a deterministic gzip archive of the full 149,729-byte JSON report (11,004 bytes compressed).

- Executed at clean commit `279c6cb7172d43004ae621db36a5466c1db82894` on Linux with Python 3.12.14, Intel Xeon Platinum 8573C, nine visible logical CPUs, and uncontrolled shared-host load. The raw report preserves source, dependency lock, CI and experiment-input SHA-256 provenance.
- Compressed SHA-256: `dab74fc3e28a3591a02a4a9b027eeb49f5b29021f82f2e39d9d78bc32d4e15fd`.
- Decompressed SHA-256: `2f596ff5faf23cbbae8c9c67a14b8fcb59373d70b48ac9f21dbdfc22a51d7ed1`.
- **36 completed pairs (72 separate child processes)**, six pairs per workload. Every comparison preserved exact logical parity; no failed cells were discarded. Each process lifetime peak includes interpreter/import baseline as disclosed above.

| Workload | Generator median peak RSS (bytes) | List median peak RSS (bytes) | Scope |
| --- | ---: | ---: | --- |
| MAX2 | 20,504,576 | 20,414,464 | UNKNOWN |
| MIN2 | 20,336,640 | 20,285,440 | Finite-world PASS |
| ABSDIFF | 22,247,424 | 21,989,376 | UNKNOWN |
| One-proposal exhaustion | 20,287,488 | 20,287,488 | UNKNOWN |
| Three-input search, 80 | 20,287,488 | 20,287,488 | SEARCH_ONLY |
| Three-input search, 3,000 | 26,050,560 | 25,528,320 | SEARCH_ONLY |

These medians describe six processes per arm/workload and are **not** a controlled estimate of per-signature heap allocations, effect size or production memory consumption. The current evidence reports small differences relative to roughly 20–26 MB complete-process peaks; the shared host, import/allocator baselines and sample count prevent a causal or significance claim. Timing with process launch is explicitly marked noncomparable to v0.2's same-process timing. No Rust speedup, FFI costs, universal verification or additional accepted mathematical capability has been measured.

**Decision: `ITERATE_R0_NO_NATIVE_GO`.** The per-trial independent-process memory evidence gate now has an exploratory observation; the independent allocation attribution, complete heavy lifecycle and controlled-host confirmatory gates remain unresolved. A negative or null result is a valid reason to continue measurement or stay with Python, not a reason to relax verifier, budget or parity safeguards.
