# H0 — Frozen CPU profiling (research harness)

**Status:** Experimental measurement apparatus, **not** evidence of hardware acceleration or a completed H0 gate.

Authority: [hardware design](../../docs/superpowers/specs/2026-10-18-cin-hardware-co-design.md), [H0–H5 roadmap](../../docs/roadmap/HARDWARE-PHASES.md), [research hypotheses](../../docs/research/2026-10-18-hardware-co-design-evidence.md).

The H0 goal is to *falsify* the idea that CIN's observational signatures are worth accelerating before any GPU, Verilog, FPGA, device driver, or H1 backend is written. This harness reads the existing five-gene genome and named public mathematical worlds; it does **not** change `cin/search.py`, `cin/ir.py`, the world verifier, archives, or the default CLI.

## Run a reproducible CPU-only pilot

From the repository root in an environment with CIN installed:

```bash
python -m cin validate
python -m pytest -q tests/test_hardware_profile.py
python -m experiments.hardware.profile_signature_search --repetitions 3 --output h0-local-report.json
python experiments/run_m1.py
```

The output path must not already exist (use a fresh filename); `--no-profile` disables the separate diagnostic profiling pass. Without `--output`, JSON goes to stdout. `--manifest` accepts a validated JSON experiment manifest. No FPGA device is accessed, no new dependency is installed, and no historical report is modified.

The checked-in `manifest.v0.1.json` fixes: legacy MAX2 and MIN2 finite-world workloads; an ABSDIFF search-budget pilot (which may be `UNKNOWN`); one intentionally exhausted MIN2 run; and a **3-input search-only** probe run. The latter is **not** a 3-input world or a mathematical proof. The six screening points follow the existing M1 development harness. `max_cases=81` is only the finite world check, not unbounded correctness.

## What is actually measured

- Primary **unprofiled** repeated passes: full wall and CPU process nanoseconds; `next(candidate_stream)` stage time; training-side screen time; finite-verification time; and unattributed overhead.
- Deterministic logical accounting: proposal count and SHA-256 digest of ordered (expression canonical hash, mutation operator, parent hash, seed), `SearchStats` shape/probe/pruning counts, screen and verification operations and verdicts.
- A **separate instrumented** cProfile run: function self-times in CIN's search, IR, and world modules. AST-source line mapping provides partial self-time for expression-generator bodies used in signature composition. It excludes Python tuple allocation and much search overhead, and instrumentation distorts timing.
- An **Amdahl upper bound for hypothetically eliminating the entire search stage** is computed from unprofiled timing: `total/(total-search)`. This is intentionally over-generous: no FPGA can eliminate every search-stage instruction, and host/data transfer is not included. An unbounded theoretical ceiling is encoded as JSON `null`.

**Crucial limitation:** the actual fraction of *offload-eligible* signature operations is `UNRESOLVED`. The profiler cannot accurately isolate Python tuple allocation, hashing, AST generation and signature memory costs from inlined code without changing measurement strategy. Never use the whole-stage Amdahl ceiling as a measured signature-speedup estimate. `world_admission`, archival costs and unpruned control are reported as `NOT_RUN`. Cold/warm cache and inter-run machine contention require separate analysis.

## Interpretation and next decision

The frozen run manifest records a source baseline commit; each report separately records the execution context commit when available (`GITHUB_SHA`), manifest SHA-256, Python/OS identity and raw per-run observations. Editing the manifest creates a different experiment; never silently rewrite the old result.

To close H0, reviewers must reproduce measurements on a declared host, add profiling-overhead calibration and a reliable eligible-signature fraction or falsifiable upper bound, compare appropriately controlled CPU alternatives and cost assumptions, then explicitly decide **GO**, **NO-GO**, or **INCONCLUSIVE**. A smoke-test PASS, successful synthesis, or a high optimistic Amdahl ceiling is **not** permission to start H2.

### No misleading speedup claims

This module has no hardware backend, no FPGA connection and no measured CPU-vs-FPGA comparison. Output deliberately includes `"hardware_speedup_claim": "NOT_MEASURED"` and `"h0_go_no_go": "PENDING_PROFILING_REVIEW"`.
