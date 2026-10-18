# CIN-Lab "Not Broke Rules" — Architectural Guardrails v1.0

**Status:** PROPOSED normative engineering policy; documentation-only change (not a runtime release or proof of conformance).  
**Scope:** Model-free CIN-Lab program synthesis, independently admitted worlds, bounded verification, lifecycle, inheritance and evidence.  
**Baseline inspected:** `main` at `653ef4efa7acf25395cc99d5fac21bc1cf2ee563` (2026-10-18).  
**Owners:** `cin/contracts.py`, `cin/ir.py`, `cin/search.py`, `cin/worlds.py`, `cin/evolution.py`, `cin/archive.py` and future versioned components.

> **Governing principle:** Bound *each resource and each claim*, not the mathematical ambition. A finite demonstration must never be presented as an unbounded theorem, and a speculative architectural rule must never be reported as already enforced.

This is a corrected consolidation of the original five-rule and ten-rule "Not Broke Rules" proposals. It defines engineering guardrails without silently changing the existing genome, world schema, typed IR or verifier. In any conflict about **what is implemented**, source code and tests win; about **existing versioned contracts**, the corresponding spec/schema wins until a reviewed versioned change adopts this proposal. See [AGENTS.md](../../AGENTS.md), [domain vocabulary](../../CONTEXT.md), [documentation index](../INDEX.md) and [v0.6 research design](../specs/2026-10-18-cin-verified-mathematical-evolution-v0.6.md).

## Modal language and evidence

- **MUST / MUST NOT**: invariant required when the affected feature or pathway is implemented. Existing implementations are not certified merely because this document says MUST.
- **SHOULD**: recommended default, with documented, reviewed alternatives.
- **MAY**: optional technique; never an acceptance criterion by itself.
- **IMPLEMENTED**: current code contains the mechanism; **PARTIAL**: only some requirements or assurance properties exist; **FUTURE**: design requirement, not shipped.
- **PASS**: independently established satisfaction of the *specified finite verification scope*; **FAIL**: a counterexample or stated violation; **INVALID**: malformed or inadmissible input; **UNKNOWN**: incomplete verification, resource exhaustion or unproved feasibility. These terms are not interchangeable.

No hard-coded number in the original proposals (AST depth 5, nodes 15, 100 "virtual steps", or "milliseconds") is a universal theoretical threshold. All such thresholds MUST be declared, versioned, finite, tested and charged to an explicit budget.

## Rule 1 — Explicit verification scope and bounded work

**Policy.** Every runnable finite-domain world MUST declare validated, non-empty, finite input intervals and compatible typed signatures. The verifier MUST compute or safely bound the Cartesian-product cardinality *before enumeration*, enforce a finite case budget, and reject or classify over-budget requests without silently sampling. A `PASS` over these inputs MUST be described as exhaustive **within the declared domain and applicable preconditions** only. Candidate count, intermediate enumeration, witness search and total experiment cost MUST have independent finite limits.

**Why.** Finiteness alone does not guarantee a fast verification; even `[-128,127]^8` is astronomically large. The Halting Problem does not imply that *all* infinite-domain claims are impossible, nor does a finite input interval by itself guarantee program termination. Finite enumeration plus total candidate semantics and explicit resource bounds permit a scoped, decidable check for admitted instances.

**Evidence / gate.** Test empty intervals, invalid signatures, over-budget domain products, preconditions with zero admissible cases, exact budget boundaries and honest finite-scope reporting. Any future SMT/theorem-proving backend for unbounded specifications MUST be separately versioned, soundly scoped and time/memory-bounded; an `UNKNOWN` solver result is not a proof.

**Current alignment: IMPLEMENTED for existing two-input worlds, with future generalization.** `cin/contracts.py` checks world contracts; `cin/worlds.py::_inputs` enforces `max_cases`. The opt-in 1–8-input IR support does **not** mean an equally general independent world verifier already exists.

## Rule 2 — Total, typed, data-only candidate execution

**Policy.** Generated programs MUST be parsed as a closed, typed CIN-IR with a whitelisted opcode set. Any recursion, loop or higher-order construct added later MUST carry a machine-checkable bound or termination argument and a worst-case execution budget; unrestricted loops and arbitrary Python evaluation MUST NOT enter the candidate verifier. Runtime arithmetic MUST have declared integer/value bounds; malformed trees and unsupported operations MUST be rejected without executing arbitrary code.

**Why.** Termination here follows from restricted **execution semantics and budgets**, not from bounding input values alone. "Non-Turing-complete" is a useful design objective for the micro-kernel interpreter, not a substitute for precise semantics and tests.

**Evidence / gate.** Negative tests for wrong arity/types, malformed nodes, forbidden opcodes, deep terms, oversized integers and exhausted interpreter fuel; positive tests for all admitted operators at boundary values.

**Current alignment: IMPLEMENTED for the present expression-only IR.** `cin/ir.py` exposes `check_tree`, `run_ir` and `run_ir_args`, with no candidate-native `eval()`, `exec()`, imports, I/O or unrestricted loops. Bounded iteration is a future, separately reviewed language extension.

## Rule 3 — Configurable structural and execution complexity ceilings

**Policy.** Every candidate path (seed, mutation, composition, replay and archive promotion) MUST enforce typed AST depth and node-count limits before acceptance, plus an execution-operation/value-size budget at evaluation. The search MUST also cap *attempted intermediate shapes*, not just yielded proposals. Over-budget outcomes MUST be typed rejections or `UNKNOWN` as appropriate; they MUST NOT be mislabeled as semantically incorrect or assigned fabricated "zero fitness".

**Why.** Grammar expansion can grow combinatorially; pruning controls resource consumption but may exclude the desired program. There is no sound universal maximum of five levels/fifteen nodes/100 steps. Changing limits changes experimental reach and requires reproducibility metadata.

**Evidence / gate.** Off-by-one tests at each cap, probe/intermediate-count accounting, budget-exhaustion tests, parameter-sensitivity experiments and verified reject paths before promotion.

**Current alignment: IMPLEMENTED in core paths, with broader accounting FUTURE.** `cin/ir.py::Limits` defaults to `max_ops=512`, `max_bits=64`, `max_depth=8`, `max_nodes=64`; `check_tree` uses genome `max_ast_depth` and `max_ast_nodes`. `cin/search.py` separately caps yielded proposals and intermediate shapes. These are implementation defaults, not a policy promise that every run uses those exact values.

## Rule 4 — Informative search feedback without answer leakage

**Policy.** **Independent correctness and promotion MUST remain explicit pass/fail/invalid/unknown gates.** A continuously valued "gradient fitness" is **not mandatory**. Search MAY use partial constraint satisfaction, counterexamples, novelty, ranking, observational signatures or other bounded heuristics *only* if their provenance, leakage boundary and overhead are documented. Private witness programs, sealed holdout answers and target/reference source similarity MUST NOT be exposed to or optimized by the organism's generator.

**Why.** Binary correctness does not always create a flat optimization landscape; exhaustive typed enumeration, constraint solving and counterexample-guided search can succeed without scalar fitness. Fractional syntax validity or resemblance to a known solution can optimize the wrong objective and bias scientific attribution.

**Evidence / gate.** Prove the search interface cannot access verifier-private witnesses/holdouts; log heuristic costs and ablations; evaluate actual outputs with the independent verifier; never turn a near miss into an accepted capability.

**Current alignment: IMPLEMENTED separation; scalar fitness is NOT IMPLEMENTED nor required.** `cin/search.py` is task-blind typed, cost-layered enumeration with observational pruning; `cin/worlds.py` independently checks submitted programs. Probe equality is not a mathematical equivalence proof.

## Rule 5 — Parsimony without sacrificing verified behavior

**Policy.** Search SHOULD prefer cheaper/smaller candidates **after** feasibility and correctness requirements are satisfied, for example lexicographic ranking by behavioral quality and then AST cost. It MAY combine node cost, depth and measured execution cost in a documented multi-objective policy. It MUST NOT give a short failing candidate priority over a correct longer one merely because of an arbitrary length coefficient. Distinct programs with identical probe signatures MUST NOT be declared globally equivalent.

**Why.** Bloat is a well-studied risk, but a mandatory additive length penalty can trade away correctness or expressive power. Structural caps (Rule 3), tie-breaking and measured cost are separate controls.

**Evidence / gate.** Compare equal-quality candidates by cost, retain correctness under ranking changes, measure AST/cost distributions, and disclose observational-pruning completeness loss.

**Current alignment: PARTIAL.** Current enumeration orders by AST size and prunes finite-probe observational duplicates; it does **not** implement a population-level scalar length-penalized fitness model.

## Rule 6 — Independent world feasibility and honest admission statuses

**Policy.** A generated/mutated world MUST pass schema checks, a non-vacuity check, compatible signatures, resource gates and an **independent verifier-controlled feasibility check** before active admission. A verified witness establishes that *at least one candidate* satisfies the admitted **finite-domain** specification. Its program implementation MUST remain private to the verifier. If the witness search budget is exhausted, admission MUST be `UNKNOWN`, not "unsatisfiable"; inconsistent/invalid constraints MAY be `REJECTED` on soundly established grounds. An SHA-256 witness digest is an identifier/integrity aid, **not a cryptographic proof of existence or of unbounded correctness**.

**Why.** An unadmitted or infeasible world can waste search resources, but a failed bounded witness search cannot decide general satisfiability. World solvability does not establish unique desired outputs, task novelty or useful curriculum difficulty.

**Evidence / gate.** Tests for valid admitted witnesses, vacuous domains, contradictory worlds, exhaustion yielding `UNKNOWN`, verifier-private witness isolation, and absence of solution leakage through event logs. Version any stronger uniqueness/novelty admission requirement before claiming it.

**Current alignment: IMPLEMENTED for finite-world witness admission; uniqueness/semantic novelty FUTURE.** `cin/worlds.py::admit_world` runs bounded, private candidate witness search and records only its digest and status.

## Rule 7 — Replay every claimed inherited contract

**Policy.** Before a capability is promoted/inherited, its *same immutable program artifact* MUST independently `PASS` every applicable historical and new finite specification whose satisfaction is claimed. A broadened world MUST NOT invalidate previously accepted requirements. At minimum, current two-spec inheritance MUST replay `World0` and admitted `World1`, each against its declared complete finite scope and relevant interpreter budgets. Future multi-capability composition/reproduction MUST use the complete versioned dependency/regression set, not assume that checking only two arbitrary examples proves preservation.

**Why.** Regression replay mitigates forgetting under the tested contracts. It is not evidence of cross-task transfer when `World1` is merely the same function on wider inputs, nor is "100%" on sampled data automatically exhaustive.

**Evidence / gate.** Negative tests for breaking `World0` while passing `World1`, stale artifacts/spec hashes, mismatched program hashes, unadmitted world references and unsupported inheritance claims. Record which contracts and case counts were replayed.

**Current alignment: IMPLEMENTED for the current two-spec gate (including selective inheritance).** `cin/evolution.py::spawn_verified` and experiment orchestration perform independent admission/replay. The child receives only the selected artifact in the independently replayed certified worlds; unrelated parent skills are not copied. `tests/test_evolution.py` covers this boundary. Multi-family transfer remains FUTURE.

## Rule 8 — No generated-program host side effects; precise sandbox claims

**Policy.** Untrusted CIN-IR MUST NOT gain imports, process spawning, filesystem/network access, host object introspection, native `eval()`/`exec()` or mutation of verification policy. Generated Python exports are inspection artifacts, never the verification execution path. Any future arbitrary-source/plugin execution MUST run in a separately reviewed OS-enforced isolated worker with restricted credentials, file mounts, network, CPU, memory, process count, wall-clock time and output size. In-process interpreter restrictions MUST NOT be described as an absolute security sandbox.

**Why.** A data-only interpreter reduces the current attack surface. It does not isolate a compromised trusted Python process, hostile dependency or future unsafe extension.

**Evidence / gate.** Tests for forbidden ops and side effects; security review and worker escape/failure tests before allowing arbitrary execution; explicit threat model and trusted-host assumptions.

**Current alignment: IMPLEMENTED data-only IR; OS-level sandbox FUTURE.** See [security architecture](SECURITY.md).

## Rule 9 — Tamper-evident, reproducible, crash-aware evidence

**Policy.** Every accepted growth, admission, world transition, replay, offspring birth and terminal decision MUST have content-linked versioned evidence. Where an event journal is used, entries MUST include sequence and previous-event linkage plus a canonically computed digest; chain verification MUST detect broken linkage and altered entries *relative to an independently trusted chain head*. Claims of durability, non-rewriteability, authenticity or deterministic reproduction MUST be backed by separate controls (e.g. anchored/signed checkpoints, pinned manifests/dependencies/seeds, transactionally consistent snapshots and recovery tests).

**Why.** SHA-256 hash chaining detects internal inconsistency; anyone able to rewrite the whole journal and head can recompute hashes. Hashes cannot prevent races, process crashes, data loss or nondeterminism.

**Evidence / gate.** Corrupt/reorder/remove-event negative tests; pinned semantic replay; crash-at-append recovery tests before claiming durability; no promotion on incomplete or inconsistent evidence.

**Current alignment: PARTIAL.** `cin/archive.py` provides single-process append-only JSONL and `verify_chain`. External authenticated anchoring, durable transactions, concurrent writers and restart recovery are not established.

## Rule 10 — Compositional growth with verified interfaces

**Policy.** CIN SHOULD synthesize small, typed, independently testable units and compose them when this reduces search work or enables reuse. Composition MUST declare signatures, pre/postconditions, assumptions, total-cost bounds, artifact versions and dependency lineage; *the composed behavior itself* MUST pass independent verification within its claimed scope. No fixed one-function shape such as `solve(x,y)` is universally mandated: richer signatures, bounded iteration and multi-output routines MAY be introduced through versioned proof-carrying extensions. A sequence of solved micro-kernels is not by itself evidence of open-ended intelligence or transfer.

**Why.** Decomposition can improve tractability, but can also create integration failures and abstraction overhead. It is an experimentally testable architecture choice, not a mathematical guarantee of efficiency.

**Evidence / gate.** Contract-mismatch tests, end-to-end composed-program checks, cost accounting of discovery and reuse, controlled comparisons to non-compositional baselines, and distinct-task holdout evaluation before a transfer claim.

**Current alignment: FUTURE as a reusable abstraction system.** Existing typed subterm composition in `cin/search.py` is not yet a general library of independently verified cross-task components.

## Implementation and acceptance matrix

| Rule | Current status | Existing owner / evidence | Required follow-up when extending |
| --- | --- | --- | --- |
| 1. Scoped finite work | IMPLEMENTED (2-input worlds) | `cin/contracts.py`, `cin/worlds.py` | Version multi-input verifier; cumulative budgets |
| 2. Total typed execution | IMPLEMENTED (expression IR) | `cin/ir.py`, `tests/test_ir.py` | Termination/fuel tests for new operators |
| 3. Complexity ceilings | IMPLEMENTED core, PARTIAL full accounting | `cin/ir.py`, `cin/search.py` | Charge all intermediate and witness costs |
| 4. Heuristics/proof separation | IMPLEMENTED separation; optional heuristics | `cin/search.py`, `cin/worlds.py` | Leakage/ablation controls before new feedback |
| 5. Parsimony | PARTIAL | Cost-layered `cin/search.py` | Evaluate quality/cost trade-offs, no mandatory scalar fitness |
| 6. World feasibility | IMPLEMENTED bounded witness | `cin/worlds.py` | Novelty/uniqueness proofs are separate gates |
| 7. Regression replay | IMPLEMENTED two-spec | `cin/evolution.py` | Full dependency closure for new capabilities |
| 8. No native side effects | IMPLEMENTED IR-only, not host sandbox | `cin/ir.py`, [security](SECURITY.md) | OS isolation before arbitrary code |
| 9. Evidence chain | PARTIAL | `cin/archive.py` | Anchoring, atomicity, restart/concurrency |
| 10. Verified composition | FUTURE reusable abstractions | `docs/roadmap/MATH-PHASES.md` | Versioned component contracts and transfer controls |

### Non-negotiable review checklist

- [ ] No new sixth genome gene; preserve the five names and existing schema versions or explicitly version a new protocol.
- [ ] No mutation/source execution bypasses `check_tree`, bounded IR execution or independent acceptance.
- [ ] Each proposed world is validated and independently admitted; an exhausted witness search remains `UNKNOWN`.
- [ ] Each admitted capability states exact world/version, input scope, preconditions, budgets and verdict.
- [ ] Every inherited claim replays its named regression specifications; wider inputs are not misreported as new task families.
- [ ] Search cannot access witness programs, sealed holdouts, benchmark answers or privileged verifier state.
- [ ] Candidate, witness, probe, intermediate-shape and verifier costs are distinguished in scientific performance claims.
- [ ] The evidence chain is verified without describing an unanchored digest as authenticated proof.
- [ ] New semantics receive negative/boundary tests and schema/IR/evaluator version notes.
- [ ] Claims are explicitly tagged **IMPLEMENTED**, **DESIGNED**, **RESEARCH HYPOTHESIS** or **UNPROVEN**, with exact evidence.

### Local verification commands (not run by this documentation-only proposal)

```bash
python -m pytest -q
python -m cin validate
ruff check .
ruff format --check .
```

Run `python -m cin demo --seed 0 --max-evals 250 --output runs/<unique-new-directory>` only when an experiment is needed; do not overwrite earlier evidence. Any new check above is a **future acceptance test request**, not a claim that such a test already exists or passed. This rules document itself changes no executable behavior.

## Source corrections and rationale

The original proposed wording is **not** adopted literally in the following places:

1. **"Finite bounds guarantee milliseconds"** — false; domain cardinality, program semantics and resources determine practical cost.
2. **"Halting/Gödel mandate intervals"** — overgeneralized; finite bounded checking is a deliberate proof scope, not a blanket theorem about all other verification.
3. **"Depth=5 / nodes=15 / steps=100, else zero fitness"** — arbitrary numbers and incorrect semantics for the current enumerator; use versioned budgets and typed statuses.
4. **"Fitness must be continuous"** — not applicable to all synthesis algorithms; correctness remains an independent discrete gate.
5. **"Length penalty inside fitness is mandatory"** — not necessary; lexicographic parsimony and hard constraints are valid alternatives.
6. **"Cryptographically proven world witness"** — digest ≠ proof; `PASS` witness shows scoped existence, exhausted search gives `UNKNOWN`.
7. **"Two worlds at 100% proves continued intelligence"** — proves only the stated replay obligations within the checked domains.
8. **"Absolute sandboxing in Python"** — an in-process interpreter is not an OS security boundary.
9. **"Hash chains guarantee immutable state and reproducibility"** — no, without external trust anchor and pinned/recoverable state.
10. **"Only two-input micro-kernels"** — unnecessarily constrains future verified mathematical expressivity; require contracts for compositions instead.

### References

**CIN internal authorities:** [README](../../README.md), [architecture contracts](CONTRACTS.md), [security](SECURITY.md), [ADR 0004](../adr/0004-formal-math-complexity-and-proof-separation.md), [ADR 0005](../adr/0005-cost-layered-observational-search.md), [ADR 0006](../adr/0006-versioned-multi-input-ir.md), [v0.6 math design](../specs/2026-10-18-cin-verified-mathematical-evolution-v0.6.md).

**External theory and methods (motivation, not evidence of CIN performance):**
- Clarke, Kroening, Ouaknine & Strichman, [Completeness and Complexity of Bounded Model Checking](https://people.mpi-sws.org/~joel/publications/compbmc04abs.html) — explicit completeness conditions and complexity; does not promise millisecond evaluation.
- Luke & Panait, [Lexicographic Parsimony Pressure](https://dl.acm.org/doi/abs/10.5555/2955491.2955636) — tree-size tie-breaking rather than mandatory scalar penalty.
- [Genetic Programming, Validation Sets, and Parsimony Pressure](https://arxiv.org/html/cs/0601044v1) — why selection fitness, validation and parsimony should be evaluated separately.

**Adoption note:** This is a rules *proposal for review*. Merging it may make the language normative for future changes; it does not retroactively certify current code, performance, OS sandboxing or mathematical capability.
