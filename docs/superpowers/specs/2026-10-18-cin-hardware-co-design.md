# CIN Hardware Co-Design — Full System Design v0.1

**Date:** 2026-10-18 · **Status:** PROPOSED, not implemented or measured · **Design class:** architectural.
**Baseline:** CIN `main` at `c414a4894b29af8497801dbae0bccc941a4e1230`.
**Companion documents:** [hardware phase gates](../../roadmap/HARDWARE-PHASES.md), [evidence/research](../../research/2026-10-18-hardware-co-design-evidence.md), [ADR 0009](../../adr/0009-optional-hardware-backends.md).
**Authority:** [AGENTS](../../../AGENTS.md), [domain language](../../../CONTEXT.md), [CIN rules](../../architecture/NOT-BROKE-RULES.md), [v0.6 mathematics](../../specs/2026-10-18-cin-verified-mathematical-evolution-v0.6.md).

## 1. Mission and design decision

**User goal:** make a product-grade, implementable path for optional Verilog/SystemVerilog acceleration within CIN, taking evidence-based inspiration from both FeSens/openTPU and FeSens/auto-arch-tournament, without rewriting CIN or weakening correctness. This PR delivers the **design only**; it does not authorize running untrusted HDL or merging agents' changes.

**Research hypotheses — not observed results:**
- HYP-A: significant fractions of CIN's end-to-end search cost may be eligible signature-vector work.
- HYP-B: a CPU batch backend can preserve exact enumeration and improve overhead.
- HYP-C: when sufficiently amortized, FPGA signature offload may outperform the best CPU implementation *after transport cost*.
- HYP-D: a correctness-gated architecture tournament might later discover improved RTL microarchitectures; no auto-optimization advantage is assumed.

**Alternatives evaluated:**
1. **CPU-first signature abstraction — adopt first:** profile, factor a typed pure backend interface, compare to existing scalar Python. No silicon or simulator dependency.
2. **Optional RTL signature engine — adopt conditionally:** offload elementwise observational signatures only if profiling/CPU controls justify it. Keep independent verifier in Python.
3. **Entire evolutionary system as RTL — reject:** would mix mutable genomes, independent admission, archiving and proof scope; no workload evidence justifies it.
4. **Full CIN-ISA hardware interpreter — defer:** possible separately, but fundamentally harder to preserve lazy branch/error/fuel semantics.

**Product boundary:** hardware accelerates calculation, **not** organism cognition, search correctness, growth acceptance or universal mathematical proof. The five seed genes stay exactly `base`, `driver`, `directive`, `maturity_point` and `stop_station`.

## 2. What the inspected CIN actually does

| Current owner | Observed baseline behavior | Boundary preserved |
| --- | --- | --- |
| `cin/search.py` | Task-blind, typed cost-layered AST enumeration with dedup by fixed, finite probe signatures; `SearchStats` measures attempted shapes/probes | Primary acceleration seam; heuristic equality is not a correctness proof |
| `cin/ir.py` | Bounded, data-only `check_tree` and `run_ir_args`; Python integer-bit limits; lazy `If` | Interpreter semantics remain authoritative |
| `cin/worlds.py` | Finite 2-input worlds, independent scoped `PASS/FAIL/INVALID/UNKNOWN`, private feasibility witness | Hardware cannot issue verdicts, receive witness, or rewrite specifications |
| `cin/evolution.py` | Growth and selectively replayed inheritance | No backend-induced new capability, altered lineage or genotype |
| `cin/archive.py` and proposed governor | Evidence, resource budgets and reproducibility | Hardware adds metering; not a second source of truth |
| `docs/adr/0003-single-process-first.md` | Single Python orchestrator preferred until further evidence | No mandatory broker, remote worker or independent microservice |

**Key semantic trap:** `search.py` constructs signature vectors with arbitrary-precision Python integers (`a+b`, `a-b`), Booleans (`a<b`, `a==b`), and elementwise `If` selection. These are *not* always equivalent to executing a candidate tree through `run_ir_args`, which enforces `Limits.max_bits` and lazily executes only the selected branch. Do **not** accelerate a 64-bit ALU using silent wraparound: doing so changes observational classes and may prune a valid future solution.

The two-input search uses 49 probes from `[-3,3]²`. Other arities use `_probe_inputs(arity)` with different bounded sets. All vectors must carry exact length; **never hardcode 49 into the protocol**.

## 3. User journeys, functional and nonfunctional requirements

**Researcher:** run a frozen cost profile; compare scalar Python, batch CPU, shadow Verilator simulation, optionally physical FPGA; receive exact proposal/verdict parity report plus measured total-cost comparison.
**Hardware engineer:** implement isolated RTL ALU, run vector/property tests, lint, cosimulation, synthesis; change lane/width/queue parameters without modifying CIN's formal verifier.
**Maintainer:** reject unsound backends, approve only scoped/evidence-backed results, disable acceleration instantly, review an explicit architecture-tournament proposal in a normal PR.

| ID | Requirement / acceptance principle |
| --- | --- |
| FR-01 | All existing APIs/CLI and historical genomes/worlds run unchanged, CPU default |
| FR-02 | Pure, task-blind typed signature backend, independent of world/admission/witness |
| FR-03 | Stable candidate ordering, hashes, prune decisions, verdicts, stats and run stopping |
| FR-04 | Exact mathematical signed arithmetic; unsupported width falls back before dedup |
| FR-05 | Observable failures and bounded retries; mismatch quarantines accelerator |
| FR-06 | Optional RTL simulation is usable without owning or flashing an FPGA |
| FR-07 | Device experiments report actual host+transport overhead, not ALU cycles alone |
| FR-08 | Separate frozen benchmark/evaluator, verifiable test records and negative results |
| FR-09 | Tournament cannot edit or bypass verifier, test oracle, benchmark or acceptance gate |
| FR-10 | Each enhancement lands in a separately reviewable implementation PR |
| NFR-01 | Default path has no HDL/toolchain runtime dependency or device side effects |
| NFR-02 | Bounded CPU/FPGA/RAM/time/case/probe budgets, exact outcome statuses |
| NFR-03 | No data leak of witness, sealed holdouts, secret world specifications |
| NFR-04 | Reproducible manifests, pinned toolchain, deterministic logical work |
| NFR-05 | Fail closed for known incorrect results; safe CPU fallback for unavailability |
| NFR-06 | Rollback to CPU requires no data migration, no regenerated organism identity |

## 4. Architectural ownership

~~~mermaid
flowchart TD
    CTRL["Trusted CIN controller / governor"] --> S["cin/search.py - typed, task-blind"]
    S --> B["Optional signature backend facade"]
    B --> CPU["Reference Python (always present)"]
    B --> SH["Shadow differential comparison"]
    SH --> CPU
    SH --> SIM["Verilator RTL simulator"]
    B --> FPGA["Physical FPGA (future opt-in)"]
    S --> W["cin/worlds.py independent verifier"]
    W --> PRIV["Private witness / fixed world scopes"]
    CTRL --> ARC["Provenance archive + cost ledger"]
    B --> ARC
    W --> ARC
~~~

**Trusted control plane:** Python owns generation, type checking, cost layering, signature dedup, yield sequence, independent verification, admission, acceptance, replay, lifecycle and archive. Backend returns only typed vectors/errors. RTL never gets a world, postcondition, evaluator-secret, accepted-program target, hidden tests or organizer policy. FPGA responses are treated as untrusted inputs.

**Execution plane:** CPU reference is mandatory; `shadow` compares CPU to RTL and never affects output; `rtl-sim` is optional for correctness tests and experiments; `fpga` is a separately enabled production experiment after H3. No toolchain installed when the user runs plain `pytest` or `python -m cin validate`.

## 5. Signature backend public contract (future `cin.signature-batch/v0.1`)

Names here are **DESIGNED**, not existing imports.

~~~python
from dataclasses import dataclass
from typing import Literal, Protocol, Sequence, TypeAlias

Vector: TypeAlias = tuple[int, ...] | tuple[bool, ...]

@dataclass(frozen=True)
class SignatureOp:
    request_id: int
    opcode: Literal["ADD", "SUB", "LT", "EQ", "SELECT"]
    operands: tuple[Vector, ...]
    length: int

@dataclass(frozen=True)
class SignatureReply:
    request_id: int
    status: Literal["OK", "UNSUPPORTED", "WIDTH_OVERFLOW",
                    "INVALID_REQUEST", "DEVICE_FAILURE", "TIMEOUT", "MISMATCH"]
    values: Vector | None

class SignatureBackend(Protocol):
    def evaluate_batch(self, requests: Sequence[SignatureOp]) -> list[SignatureReply]: ...
~~~

**Semantics and type contract:**
- `ADD`/`SUB`: two Int vectors → Int vector, exact mathematical result, no truncation; `LT`/`EQ`: two Int vectors → *Python Bool* vector; `SELECT`: (Bool vector, Int vector, Int vector) → Int vector. Python `bool` must not masquerade as `int` at type boundary.
- Every operand has precisely the declared positive finite `length`; validation caps length, batch count and serialized bytes. Wrong arity, duplicated IDs, missing/extra responses, illegal ops and shape mismatch must fail, not return plausible data.
- CPU reference uses Python's mathematical integers. Physical RTL may use **declared signed W-bit two's-complement** (initial design knob W=64). Inputs outside `[-2^(W-1),2^(W-1)-1]` or arithmetic outputs beyond this range trigger `WIDTH_OVERFLOW` on the complete request, followed by exact CPU recomputation. Comparison respects signedness; Boolean output stays Boolean.
- A batch is a deterministic mapping, not a capability evaluator. Stable request IDs/order; immutable input/output; no callback may change pruning, proposal budgets, or give candidate-level verdicts. Responses out of order or duplicated are invalid even if vector values look right.
- `If` signature combination is elementwise `SELECT` on precomputed subterm signatures, **not lazy interpreter evaluation**. Candidate interpreter semantics stay separate.
- When backend is unavailable (`UNSUPPORTED`, width, device error or timeout) CPU fallback occurs for the *whole affected request* and records failure and wasted work. In shadow mode CPU results always win and any divergence fails the experiment. In active mode known `MISMATCH` **aborts run and quarantines backend**; it must not be papered over with silent fallback.
- Backend modes: `disabled`/`cpu`/`shadow`/`rtl-sim`/`fpga`. Device selection is a run-level operator parameter external to genome and IR; unavailable dependencies return a clear `UNAVAILABLE` at setup.

## 6. Search integration and batching discipline

1. `candidate_stream` continues to determine typed shape order, fixed task-independent probes, candidate identities, dedup and budget counting. Existing `max_proposals` and intermediate `max_shapes` boundaries cannot change.
2. `cin/accelerators/cpu_backend.py` implements exact `SignatureOp` semantics and is compared to current scalar `search.py` as a golden behavioral baseline.
3. First integration is a simple *ordered, synchronous, one-operation* seam, shadow-only. Profiling determines later batching strategy; do not precompute speculative shapes past budget or change which signature first claims a dedup class.
4. Batch groups may contain parallel lane operations only when dependencies are resolved and their outputs can be committed in original enumeration order. Each internally attempted shape (including pruned/failed) remains charged once.
5. If any element cannot be represented exactly, mark the affected request and recompute it in CPU before signature-bank insertion. Entire vector is atomic. Device resets/timeouts must never emit stale or partial results.
6. Run a *trace parity oracle*: compare ordered (AST canonical hash, proposal operator, parent hash, seed), per-shape prune result, counts, verifier verdicts and accepted artifacts for full experiments. Deterministic equality is a gate, not a soft metric.
7. Keep separate **logical** search counters (`attempted_shapes`, `probe_evaluations`, emitted proposals, prunes, verifier cases) and **physical** backend counters (lane ops, CPU fallback ops, serialized bytes, transfer latency, device time, host CPU time, setup/compilation). Never report equivalent “less search work” just because a device runs the same work faster.

## 7. RTL unit design: minimal Vector Signature Engine (H2)

**Files proposed:** `hardware/cin_signature_engine/rtl/cin_vector_alu.sv`, `cin_signature_lane.sv`, `cin_signature_top.sv`; tests under `hardware/cin_signature_engine/tests/`; sim integration in `cin/accelerators/rtl_backend.py`.

- `cin_vector_alu` implements Add/Sub/Compare Less/Equal/Select with signed `W` input and explicit overflow detection. No global black-box hashing/pruning logic. Parameterize `W=64` and `LANES=1/4/8` only as synthesis variants, not promises that all map to an FPGA.
- `cin_signature_lane` has valid/ready handshake and registered transaction index/status. `cin_signature_top` aggregates lanes, enforces bounded queue/length and monotonically completed response order. Reset cancels pending transactions with an observable failure; never reuses stale data.
- Sim transport (testbench/Verilator wrapper) and prospective board transport (H3) share one versioned frame contract: little-endian, magic/version, widths, lengths, request IDs, checksum/integrity checks and max byte size. Do not interpret arbitrary untrusted lengths before validation. A local in-process object adapter may avoid wire packing until H3.
- HDL has no access to CIN genome, world evaluator, secrets, Python process objects or external code. No generated Verilog from candidate organisms is executed.
- Verification gates: directed boundary values and Bool/int mixes; randomized differential tests vs Python reference; reset/stall/order/overflow/cancellation assertions; bounded formal properties (SBY) with exact assumptions and coverage to avoid vacuity; synthesis/timing/resource estimates where tools support chosen SystemVerilog subset.
- **Caveat:** Verilator runs as software on the host; passing RTL simulation demonstrates candidate semantics, **not hardware speedup**. FPGA performance cannot be claimed until measured on actual board with full transfer and driver overhead.

## 8. Conditional CIN-ISA Interpreter (H4), not part of signature protocol

If H3 establishes useful offload economics, a separate `cin.hardware.isa/v0.1` can lower a fully validated typed AST to bounded LOAD_ARG/LOAD_CONST/ADD/SUB/LT/EQ/BRANCH_IF/HALT/FAULT instructions with typed registers, immutable code image and explicit fuel/memory limits. It must match `run_ir_args`'s **lazy branch**, signed input handling, `bit_length()` limit (including negative value edge cases), runtime fault class and operation counting. A signature SIMD implementation does not automatically satisfy these stronger obligations.

Hardware execution is never an independent proof of an unbounded theorem. `cin/worlds.py` remains verdict authority. Do not start H4 merely because H2 simulates correctly.

## 9. Verified Architecture Tournament (H5; optional, later)

**Inspiration:** FeSens/auto-arch-tournament runs schema-checked hypotheses in isolated git worktrees and gates lint/synthesis/formal/cosim before multi-seed place-and-route. CIN borrows the *frozen evaluator + hypothesis isolation + promote only correctness-preserving improvements* pattern. It does **not** borrow RV32IM, CoreMark as CIN fitness, or unrestricted AI control.

**Tournament hypothesis schema (future `cin.hw.hypothesis/v0.1`):**

~~~yaml
id: hyp-0001
base_commit: pinned_champion_sha
category: lane_count # lane_count|pipeline|buffering|arithmetic|transport
motivation: "Measured bottleneck in workload profile"
changes:
  - hardware/cin_signature_engine/rtl/cin_signature_top.sv
benchmark_manifest_hash: pinned_benchmark_sha
expected_impact: "Throughput improves without incorrect results"
~~~

**Agent write allowlist:** `hardware/cin_signature_engine/rtl/**` and designated non-authoritative HDL unit-test files only; validator accepts only allowlisted paths and prevents symlink escape. **Agent forbidden:** `cin/ir.py`, `cin/search.py`, `cin/worlds.py`, `cin/evolution.py`, `cin/archive.py`, schemas, evaluator/cosim oracle, holdouts, reference tests, benchmark harness, governor, CI, toolchain wrappers, any other target. No direct promotion/merge to `main`.

**Trusted evaluation:** hypothesis schema/path diff validation → Verilator lint → RTL unit/property tests → independent Python/RTL differential tests → formal with explicit scope/assumption/vacuity checks → synthesis → ≥3 fixed P&R seeds for a declared board → frozen paired end-to-end CIN performance assessment. Reject early on first failing gate; save all negative and passed-but-slower outcomes. No use of formal “PASS” for properties that were not actually proved. Do not mistake ALTOPS-style weakened arithmetic verification for full arithmetic proof.

**Promotion:** correctness is a hard gate, then compare measured throughput/latency/transfer costs and area/power constraints against current champion using preregistered thresholds; the best eligible result is only a *proposed* replacement pending human review. Multi-seed PPA is evidence of target synthesis estimates, not universal FPGA performance. Every experiment records base commit, test/tool hashes, outcomes and counterexamples.

**Security:** worktrees isolate git files, **not processes**. Untrusted HDL/tool scripts/agent actions require OS-enforced sandbox (container/VM, no credentials/network/private mounts, capped CPU/RAM/disk/process/time) and evaluator integrity checks *before unattended execution*. The orchestrator and accept rule are outside the worktree, immutable to the proposer, and cannot be edited by candidate systems. No default agent loop in CIN's runtime.

## 10. Measurement contract and stop/go science

**H0 profiling:** freeze workloads: existing MAX2, M1 MIN2 and ABSDIFF, failed/UNKNOWN budget cutoff, conditional/comparison signatures and signed overflow; test multi-input **search probes** without asserting multi-input world verification. Measure tuple allocation, hashing, AST synthesis, observational pruning, verifier, witness, I/O and interpreter costs. Amdahl ceiling for accelerating fraction `f` is `1/(1-f)` before transport; if eligible fraction is small, halt hardware work.

**Comparisons:** original scalar Python; reference batch CPU; optimized CPU implementation; optional RTL simulation for correctness-only; actual FPGA if available. Control seeds, fixed probes, grammar, shape/proposal caps, final verifier, machine/OS and dev workload. Compare ordered traces **before** scoring time. Record setup, compilation, transfers, host overhead, wall-clock/CPU, peak memory, hardware resources, failures/fallback and energy only if measured. Synthetic ALU microbenchmarks are diagnostics, not the primary endpoint.

**Proposed *predeclared* H3 target (not a predicted result):** ≥1.5× median end-to-end search-wall-time speedup versus best validated CPU arm, across ≥5 paired runs on the same platform including transfer/initialization amortization declared upfront, with no trace/verdict discrepancies and within a fixed resource cap. Report all repetitions and confidence interval/dispersion; noisy/incomplete results are `INCONCLUSIVE`, not `PASS`. H5 thresholds require a new frozen preregistration after H3 data exists; no adaptive success criteria.

**Work accounting:** logical candidate shape/probe/verification/admission costs never reset based on backend; physical work is separately charged to relevant actor/governor. Include retries and failing calls. `UNKNOWN`, timeout, overflow fallback, invalid request, simulation-only, synthesis failed, FPGA PPA regression and correctness mismatch are distinct statuses; never collapse them into score zero or correctness success.

## 11. Evidence, provenance, compatibility, rollout

- Versioned run manifest pins CIN/IR/probe/backend protocol/RTL SHA, verifier version, inputs/witness *hashes* where safe, search budget, seed, hardware tool versions/hashes, board/bitstream/driver/clock, benchmark hash, host/OS, performance methodology. Never publish private witness source or held-out answers.
- Existing archive hash chain remains evidence linkage, not authenticated durable storage; P1-03 remains owner of crash/atomic recovery. No new evidence field may silently overwrite accepted historical artifacts.
- Default `disabled` means zero changes to today’s CIN CLI, schema, five genes, canonical hashes, `PASS/FAIL/INVALID/UNKNOWN`, or independent admission. Roll back by disabling adapter, invalidating suspect device outputs, retaining exact provenance.
- Optional tooling candidates: Verilator, cocotb, Yosys, SBY/SymbiYosys; versions must be pinned per future toolchain manifest. Board/vendor drivers must be optional and not required by regular Linux/macOS Python CI. Physical target selection is explicitly deferred.
- Research success does not establish new mathematical generalization or capability transfer; any claim about those topics must pass their existing independent CIN phase gates.

## 12. Reviewable work decomposition

| Phase | Deliverable (proposed future PR) | Hard exit / stop |
| --- | --- | --- |
| H0 | Frozen profiler and full-cost benchmark, no altered runtime | Evidence that eligible signatures are a bottleneck; otherwise STOP |
| H1 | New `cin/accelerators` CPU reference, optional shadow API, exact trace tests | Identical streams, prunes, budgets, verdicts and no regression of default |
| H2 | RTL ALU, deterministic simulation/cosim, formal and opt-in CI | Signed overflow/reset/error/order/property tests; report bounded scope |
| H3 | Selected board adapter, FPGA bitstream/transport and measured study | Physical reproducible net benefit or STOP (no fabricated claim) |
| H4 | Separately designed opt-in CIN-ISA interpreter | Lazy `If`/fuel/error semantic equivalence; optional, H3 dependent |
| H5 | Secured RTL microarchitecture hypothesis tournament | Frozen evaluator, OS isolation, no autonomous merge; optional, H3 dependent |

See [HARDWARE-PHASES](../../roadmap/HARDWARE-PHASES.md) for file-level tasks, commands and falsifiers. **Merging this documentation does not implement any phase.** H0 requires a fresh scoped implementation PR and baseline evidence before H1; no speculative tool installation, FPGA purchase, AI agent execution or automatic deployment.

## 13. Risks, decisions and exit checks

**R1 Semantic drift:** fixed-width arithmetic or Bool conversion changes signature pruning; exact CPU fallback + differential full-trace test.
**R2 Amdahl/overhead:** device transport dominates tiny vectors; H0/CPU control can close the project.
**R3 Missing verification scope:** bounded formal checks falsely presented as universal; manifest proofs by property/bound/assumption, independent Python world verification stays.
**R4 Agent security:** git worktrees not an OS sandbox; require isolated runner and nonmodifiable evaluator for H5.
**R5 Nondeterminism:** concurrency changes signature winning representative or proposal sequence; ordered commit, hash/trace comparison.
**R6 Reproducibility:** changing FPGA clocks/seeds/driver produces false improvements; freeze environment and independent validation.
**R7 Roadmap distraction:** P1 crash recovery and M2 independent worlds are still separate obligations; hardware never substitutes for those.

**Spec PR acceptance:** link integrity, clear ownership/protocol/types/statuses, exact width/fallback and lazy-If separation, safe tournament scope, falsifiable phase gates, measured-cost controls and no claims of shipped hardware.

## 14. Primary source trail (inspected 2026-10-18)

- [openTPU README](https://github.com/FeSens/openTPU/blob/f237dab2f196855a59a083b1454786df8f01291f/README.md) and [ISA contract](https://github.com/FeSens/openTPU/blob/f237dab2f196855a59a083b1454786df8f01291f/docs/isa.md): SystemVerilog RTL / Python simulator / compiler separation and stated bit-exactness; reported FPGA figures are authors' measurements, not CIN evidence.
- [openTPU as-built design](https://github.com/FeSens/openTPU/blob/f237dab2f196855a59a083b1454786df8f01291f/docs/superpowers/specs/2026-09-23-opentpu-design.md): differential test layers, memory/compute trade-offs; do not copy TPU matrix array.
- [auto-arch-tournament README](https://github.com/FeSens/auto-arch-tournament/blob/4a137bb1378834ca3664a1c971684777eb5f364a/README.md), [I/O](https://github.com/FeSens/auto-arch-tournament/blob/4a137bb1378834ca3664a1c971684777eb5f364a/ARCHITECTURE.md), [benchmark protocol](https://github.com/FeSens/auto-arch-tournament/blob/4a137bb1378834ca3664a1c971684777eb5f364a/BENCH_METHODOLOGY.md), [hard invariants](https://github.com/FeSens/auto-arch-tournament/blob/4a137bb1378834ca3664a1c971684777eb5f364a/CLAUDE.md): editable RTL boundaries, correctness gates, multi-seed PPA, known formal limitations.
- [Verilator docs](https://verilator.org/guide/latest/), [cocotb 2.1 runner docs](https://docs.cocotb.org/en/v2.1.0/library_reference.html), [Yosys](https://github.com/YosysHQ/yosys), [SBY](https://symbiyosys.readthedocs.io/en/latest/verilog.html): **optional future** EDA tool candidates; not currently installed or required by CIN.

**Status caution:** external project self-reported results demonstrate motivation, not independent benchmark replication or predicted CIN speedup; all CIN backend/interfaces/CLI/hardware paths in this document are DESIGNED until implemented and verified.
