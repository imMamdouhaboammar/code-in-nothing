# R0 v0.3 isolated process peak-RSS diagnostic (Issue #12)

Status: **PREREGISTERED, NOT YET MEASURED**. This is a bounded follow-up to the R0 v0.2 integrated Python control, not a native Rust GO or an independent allocator attribution result.

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
