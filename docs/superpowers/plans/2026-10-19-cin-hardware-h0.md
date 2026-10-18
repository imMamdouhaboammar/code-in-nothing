# H0 Hardware Profiling Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Steps use checkboxes for tracking.

**Goal:** Produce repeatable, CPU-only evidence that bounds the possible speedup from accelerating CIN's observational-signature work without changing its search or verifier.

**Architecture:** Add a frozen manifest and a standalone developer profiling harness under `experiments/hardware/`. Measure separately observable search/screen/verification stages, collect `cProfile` source-attributed diagnostics, record stable proposal fingerprints and workload statuses, and compute only a conservative Amdahl ceiling for accelerating the entire search stage. Preserve current `cin/` runtime untouched.

**Tech Stack:** Python 3.11–3.13 standard library (`cProfile`, `pstats`, `time`, `hashlib`, `statistics`), existing PyYAML/jsonschema runtime, pytest. No EDA/Verilog/FPGA dependency.

**Spec:** `docs/superpowers/specs/2026-10-18-cin-hardware-co-design.md`, `docs/roadmap/HARDWARE-PHASES.md`.

## Global constraints

- Current `cin/search.py`, `cin/ir.py`, `cin/worlds.py`, genome, world, and archive semantics are immutable in this PR.
- Probe equality never becomes a proof. Multi-input probe workloads are **SEARCH_ONLY**, not verified worlds.
- No speedup or eligibility decision is inferred from a wide "entire search" Amdahl bound.
- Profiled timings are distorted by instrumentation; only unprofiled paired elapsed times describe baseline timing.
- A report must carry source provenance and distinguish measured components from `NOT_RUN`/`UNRESOLVED`.
- No mutable historical evidence or default CLI behavior changes.

## Review focus

1. A zero/negative proposal budget or malformed manifest must fail before execution.
2. Search exhaustion returns `UNKNOWN` with unchanged counters, not accidental `FAIL` or `PASS`.
3. A three-input search-only workload may not receive a world-verifier verdict.
4. `cProfile` must be disabled for the primary wall-time runs; source attribution remains diagnostic.
5. Amdahl fraction 1 requires an unbounded theoretical limit, not numeric division-by-zero.

## Task 1 — Manifest and strict validation

**Files:** Create `experiments/hardware/manifest.v0.1.json`; create `tests/test_hardware_profile.py`; implement in `experiments/hardware/profile_signature_search.py`.

**Interfaces:** `load_manifest(path: Path) -> dict`. `validate_manifest(data: object) -> dict`; structured workload records support `name`, `kind`, `max_proposals`, optional `world`, `seed`, `arity`. Frozen training-side screen uses existing M1 fixture and named world paths.

- [ ] Write tests for safe manifest load, required fields/version, duplicate IDs, traversal/unknown fixture rejection, positive bounded proposal limits and source fixture inventory.
- [ ] Run tests and observe missing-import/failing-test RED.
- [ ] Implement validator and manifest, run focused tests GREEN.
- [ ] Commit coherent slice.

## Task 2 — Observable workload and trace fidelity

**Files:** Update profile script; extend tests.

**Interfaces:** `run_workload(workload: dict, base: dict, *, profile: bool = False) -> dict`. Returns separate search/screen/verify times and logical counters, status, proposal hash digest, candidate hash/verdict, profile diagnostics.

- [ ] Write tests for deterministic trace/counters across repeated executions; search-only 3-input behavior; budget exhaustion and non-vacuous verification.
- [ ] Observe RED on tests; implement single sequential enumerator flow preserving existing `candidate_stream` and M1 public screening/finite-verifier pattern.
- [ ] Run focused tests GREEN, never alter CIN source.
- [ ] Commit.

## Task 3 — CPU timing protocol, profiler attribution, Amdahl bound

**Files:** Update profile script; extend tests.

**Interfaces:** `run_study(manifest: dict, *, repetitions: int, profile: bool) -> dict`; `amdahl_search_ceiling(search_ns: int, total_ns: int) -> float | None`.

- [ ] Write tests for wall/process time positivity, source-attribution presence, status of unmeasured allocations and admissions, provenance/determinism, repeat count, CLI JSON, and Amdahl 0/1 boundary.
- [ ] Observe RED, implement cProfile diagnostic separately from unprofiled primary measurements; explicitly tag signature-expression function self-time and whole-search stage envelope.
- [ ] Run focused tests GREEN; run CLI against pinned default manifest with bounded repetitions; inspect JSON and record outputs.
- [ ] Commit.

## Task 4 — Research documentation, integration and verification

**Files:** Create `experiments/hardware/README.md`; optionally `experiments/hardware/RESULTS.md` **only with executed evidence**. No fixture rewrite, no benchmark performance claim.

- [ ] Document invocation, comparator, costs and limitations; report profiling overhead, upper-bound reasoning, `NOT_RUN` admission/archive/unpruned control.
- [ ] Run `python -m pytest -q`, `python -m cin validate`, `python experiments/run_m1.py`, `ruff check .`, `ruff format --check .` in available CI.
- [ ] Compare branch changed paths to plan and inspect PR status; record any blockers.
- [ ] Open a reviewable PR to `main` without automatically merging.

**Execution note:** current environment cannot access GitHub via unauthenticated terminal DNS. GitHub connector writes and GitHub Actions on the PR provide remote test execution. Do not claim local red/green command execution or measured profiling results unless logs confirm them.
