# CIN Hardware Co-Design — implementation gates and PR slices

**Status:** PROPOSED engineering backlog, not executed or approved for implementation. 2026-10-18.
**Design authority:** [Full hardware co-design spec](../superpowers/specs/2026-10-18-cin-hardware-co-design.md), [ADR 0009](../adr/0009-optional-hardware-backends.md), [Not Broke Rules](../architecture/NOT-BROKE-RULES.md).
**Independent prerequisites:** P1 cost/governor work, P1-03 crash recovery, M2 world generalization keep their own existing gates. Hardware phases do NOT certify those unrelated goals.

## Dependency structure

~~~text
H0 cost profile and frozen controls
   | STOP if signature work not worth offload
H1 CPU batch contract + shadow trace equivalence
   | STOP if CPU optimized wins or parity fails
H2 SystemVerilog signature unit + cosim + formal
   | stop/retain research-only if semantics or costs fail
H3 physical FPGA validation, optional target-specific
   | STOP if no robust net end-to-end advantage
   +--> H4 optional CIN-ISA interpreter (separate design)
   +--> H5 optional safe RTL tournament (separate design)
~~~

The phase name is a **gate**, not an implementation status. Each PR must keep original Python paths working and be independently reviewable.

## H0 — Instrument, preregister, falsify acceleration need

**Proposed PR title:** `research(hardware): baseline signature search cost and Amdahl bound`.

**Changes:**
- Create `experiments/hardware/README.md`, `experiments/hardware/profile_signature_search.py`, `experiments/hardware/manifest.v0.1.json`, and `tests/test_hardware_profile.py`. Reuse `SearchStats`; do not rewrite `candidate_stream` yet.
- Freeze inputs and version hashes for MAX2, MIN2, ABSDIFF and negative budget path; include current multi-input probe generation without claiming independent multi-input world acceptance.
- Instrument signature operations, tuple allocations, hashing, AST checking, graph build, verification, witness admission and archival separately. Sample CPU/monotonic wall time plus platform details; do not mislabel Python process CPU time as FPGA elapsed.
- Compare search with/without signature pruning where already supported by explicit future control code, otherwise mark `NOT_RUN` and version the control. Emit raw distributions and complete failure/exhaustion outcomes.
- Record baseline grammar, max_shapes/proposals, probe lengths, Python package version/commit, interpreter limits, seeds, fixed case scope, profile overhead, and profiler calibration.

**Commands/gates:** `python -m cin validate`, `python -m pytest -q`, `python experiments/run_m1.py`, `python -m ruff check .`, `python -m ruff format --check .`; new profiler reproducibility test compares numeric logical work across identical seeds. Do not claim evidence until commands run.

**GO only if:** fixed data shows sufficient eligible end-to-end fraction to meet the **proposed** 1.5× speed target after realistic host/transport cost (Amdahl upper bound ≥ target), or a reviewer documents a narrower justified research question. **NO-GO:** eligible fraction too small, dominant cost elsewhere, or quality of timing not sufficient. Publishing a negative result closes this phase successfully as research, not as an acceleration product.

## H1 — CPU reference abstraction, with zero behavioral drift

**Proposed PR title:** `feat(search): optional typed signature batch and shadow parity`.

**Files:**
- New `cin/accelerators/__init__.py`, `interface.py`, `cpu_backend.py`, `shadow_backend.py`, `errors.py`.
- Modify `cin/search.py` **only** to add opt-in backend call site after a reference-compatible CPU function exists; default path must remain unchanged.
- New `tests/test_signature_backend.py`, `tests/test_search_backend_parity.py`; optional run-manifest addition versioned without mutating prior records.

**Proposed API:** exact `SignatureOp/SignatureReply/SignatureBackend.evaluate_batch` from [spec `5](../superpowers/specs/2026-10-18-cin-hardware-co-design.md#5-signature-backend-public-contract-future-cinsignature-batchv01). Note Python bool type must be tested with `type(v) is bool`, not `isinstance(v,int)`.

**Required red/green tests:**
1. Empty/negative/overlimit length, wrong op arity, Bool-as-Int, unknown opcode, stale/duplicate/out-of-order ID and partial response are rejected deterministically.
2. Exact mathematical signed ADD/SUB on high magnitude and negative values; Bool LT/EQ; masked SELECT; no mutation/alias of input tuple.
3. Abort on known CPU/RTL mismatch; CPU fallback on declared width/device unavailability; meter attempted failed calls and fallback.
4. All existing search result hashes and proposal operators, full prune trace, shape/probe counters, final verifier statuses and archived accepted artifacts are **identical** for pinned seeds and budgets.
5. Budget boundaries: no speculative shapes beyond caps, no proposal reordering under batching, no private verifier inputs in transmitted operations.
6. Default install without Verilator, cocotb or FPGA still passes existing tests on Python 3.11–3.13.

**GO only if:** exact trace parity and cost-ledger tests pass, unchanged default CI passes, and H0's bottleneck still justifies adding an RTL backend.

## H2 — Simulation-grade RTL vector-signature unit

**Proposed PR title:** `feat(hw): proof-gated RTL signature engine and Verilator cosim`.

**Files:**
- `hardware/cin_signature_engine/rtl/cin_vector_alu.sv`: signed add/sub, LT/EQ/SELECT, explicit overflow; parameter W.
- `hardware/cin_signature_engine/rtl/cin_signature_lane.sv`: valid/ready, reset/error/transaction tags.
- `hardware/cin_signature_engine/rtl/cin_signature_top.sv`: LANES parameter, ordering/queues.
- `hardware/cin_signature_engine/tests/test_signature_rtl.py`: cocotb or equivalent runner, targeted and seeded vectors.
- `hardware/cin_signature_engine/formal/signature.sby` + property wrapper: bounded reset, ordering, overflow and response invariants.
- `cin/accelerators/rtl_backend.py`: opt-in Verilator adapter, no unrestricted runtime HDL builds inside organism.
- `.github/workflows/hardware.yml`: optional/pinned toolchain CI with path filter and/or manual trigger; default core Python CI independent.

**Directed evidence:** signed MIN/MAX, negative results, overflow, cmp around zero, Bool vs Int, malformed vectors, zero/maximum batch, request-ID ordering, backpressure, reset mid-transaction, watchdog timeout, cancellation, CPU fallback and frozen 49-probe two-input case.

**Formal scope:** name W/LANES, depths/induction, assumptions and reset behavior; run cover/non-vacuity properties. A bounded model check cannot prove properties outside its declared bound; `UNKNOWN` is not success.

**GO only if:** reference equality across all directed vectors and fixed-seed randomized tests, documented formal evidence, synthesizable target subset or justified simulator-only research status, full Python CI stays green. **No performance claim from simulation.**

## H3 — Actual board bring-up and cost-complete performance

**Proposed PR title:** `experiment(hw): device adapter and preregistered CPU-vs-FPGA study`.

**Before coding:** choose a board actually owned by the team, available SDK, licensing, memory interface and driver API; publish board and toolchain manifest; confirm expected packet size and transfer/amortization cost. None is selected by the spec PR.

**Proposed files:** `hardware/boards/<target>/README.md` and target constraints, `cin/accelerators/fpga_backend.py`, `experiments/hardware/run_device_study.py`, `experiments/hardware/RESULTS.md`, device lifecycle tests isolated from ordinary CI.

**Tests:** bit-exact full-vector comparison versus Python on board; lane parameters; cold/warm/reset; device disconnect; replay idempotence; no stale replies; memory/transfer bound; resource exhaustion; tampered/mismatched bitstream metadata; malformed frame; secure device access denial in regular CIN.

**Performance test:** ≥5 paired frozen runs against **best** working CPU arm, recording each end-to-end wall time, time to first result, transfer/setup overhead, CPU time, FPGA cycles, utilization, fallback/mismatch count, power only when measured. Include before/after budgets and manifest. Proposed target ≥1.5× median *full search* improvement with zero changes in hash/verdict sequences; confidence intervals and dispersion reported. An inconclusive result is `INCONCLUSIVE`, not a performance win.

**GO:** physical correctness and significant measured net benefit justify maintaining FPGA as optional backend. **NO-GO:** publish negative/inconclusive experiment; retain H0–H2 scientific artifacts and keep CPU product default.

## H4 — Optional CIN-ISA execution engine: separate spec gate

**Decision required:** is signature offload worth extending to full AST interpreter execution? Prepare new ISA semantics/spec before a code PR; do not treat H2 signature results as candidate execution.

**Proof obligations:** typed instruction validation, lazy `If`, signed Python integer policy including `bit_length()` on negative values, op/node/depth/fuel accounting, exact errors, 1..8-argument IR, signed/overflow boundaries, compiler-independent world verdicts.

**NO-GO:** any weakening of independent world verifier or invented unbounded correctness claim.

## H5 — Architecture tournament: separate threat model gate

**Decision required:** can team supply an OS-isolated worktree runner and immutable evaluation infrastructure? If not, allow human-authored RTL experiments but no autonomous implementation agent.

**Proposed files:** `hardware/tournament/hypothesis.schema.json`, `hardware/tournament/evaluate.py`, `hardware/tournament/accept.py`, `hardware/tournament/manifest.schema.json`, `tests/test_hardware_tournament_security.py`; never put evaluator writable in hypothesis workspace.

**Strict sequence:** schema + writable path check → lint → RTL directed tests → Python differential trace → formal (non-vacuous) → synth → 3-seed target P&R → matched end-to-end benchmark → candidate recommendation/PR **for human review**. Store negative and inconclusive candidates.

**Security negatives:** try rewriting `cin/worlds.py`, test oracle, benchmark inputs, formal assumptions, acceptance rule, path via symlink, global configuration, tool executable or gitignored script. Every mutation must be denied under OS isolation; workers must not have secrets/network/devices beyond declared needs. No automatic `main` merge, no code execution from organism-synthesized programs.

**GO:** immutable gates, isolated runner, zero correctness violations, properly benchmarked candidates and human reviewer approval. Else **STOP**.

## Global acceptance and rollback

- Existing `cin.genome/v0.1` and IR/world contracts remain unchanged unless separately versioned and approved.
- Hardware never receives witness source, sealed answers, world semantics or trusted evaluator state.
- Hardware output is a signature heuristic; `cin/worlds.py` alone determines scoped verification outcomes.
- Reproducible evidence distinguishes simulated, synthesized and physically measured results.
- All implementation slices get CI, independent review and documented rollback. New dependencies are optional.
- Phase success means **a verified exit gate**, not just PR merged or code compiling.
- After any known mismatch: stop new accelerator usage, quarantine bitstream/backend, use reference CPU for fresh experiments and retain forensic evidence. Never relabel earlier unsound results as verified.

## Future implementation handoff

Once this spec PR is reviewed and the H0 scope is approved, write a **separate** Superpowers implementation plan (`docs/superpowers/plans/2026-10-18-cin-hardware-h0.md`) with exact TDD steps. Do not execute the H1–H5 implementation from this documentation PR; their scope needs evidence and independent approval.
