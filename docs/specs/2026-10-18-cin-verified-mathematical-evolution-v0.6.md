# Code in Nothing v0.6: Verified Mathematical Evolution

**Status:** Integrated engineering and scientific design, not a released runtime version.
**Date:** 2026-10-18
**Baseline:** `main` commit `ca65b95d4ea0e22c55ad3cb0ea430588cad7e75f`, merging M1 in [PR #1](https://github.com/imMamdouhaboammar/code-in-nothing/pull/1).
**Current implementation proposal:** [M2 foundation PR #2](https://github.com/imMamdouhaboammar/code-in-nothing/pull/2), independently reviewable and **not assumed merged**.
**Prior authorities:** [integrated v0.4](2026-10-18-cin-integrated-system-spec-v0.4.md), [mathematical v0.5](2026-10-18-cin-mathematical-evolution-v0.5.md), [formal benchmark protocol](../research/MATH-BENCHMARK-PROTOCOL.md), [current mathematical roadmap](../roadmap/MATH-PHASES.md), [M1 CI evidence](../research/2026-10-18-m1-math-synthesis-evidence.md), and [ADR 0005](../adr/0005-cost-layered-observational-search.md).

The v0.4 and v0.5 specifications remain applicable to their declared scopes. This document resolves **execution priorities and acceptance gates** for the next research program; it does not silently supersede previous versioned contracts. "Implemented", "tested", "designed", "hypothesis", "negative result", and "unproven" have separate meanings.

## 1. Falsifiable research mission

Measure whether a fully model-free, resource-limited evolving system can increase **independently verified mathematical capability per unit of complete computation**, retain reusable mathematical abstractions, and transfer those abstractions across *different* task relations.

A program becoming longer, a world acquiring a new name, a population becoming larger, a solver returning UNKNOWN, or a generation counter advancing is never evidence for this claim.

Primary hypotheses, each subject to matched controls:

- **H1 (search):** typed compositional enumeration improves time or work to first independently verified solution versus legal-grammar baseline searches after **all** generator, fingerprint, screening, and verifier costs are included.
- **H2 (semantic novelty):** generated worlds include three independently admitted, semantically distinct relations, not mere renamings, parameter shifts, or expanded domains.
- **H3 (transfer):** training-discovered, independently replayed abstraction(s) reduce cumulative solution work on different held-out mathematical functions after charging initial discovery, replay, extraction and reuse.
- **H4 (evolution):** three or more descendants preserve inherited capability and replay under deterministic restart, with immutable birth rules and correctly accounted budgets.
- **H5 (adaptation):** birth-gated search-policy changes outperform non-adaptive controls under frozen, comparable budgets, including negative-transfer analysis.

If a control is faster or a required proof is UNKNOWN, report the negative or inconclusive result. No retrospective benchmark/seed selection, unlimited search retries, reference-solution insertion, or benchmark-specific operations.

## 2. Verified baseline versus future system

| Subsystem or claim | Status as of baseline `ca65b95` | Evidence / boundary |
| --- | --- | --- |
| Five exact genome genes | IMPLEMENTED + TESTED | `cin/contracts.py`, v0.1 genome schema, contract tests |
| Bounded, data-only two-input Int/Bool IR | IMPLEMENTED + TESTED | `cin/ir.py`, `tests/test_ir.py` |
| Typed cost-layered search with task-blind fixed probes | IMPLEMENTED + TESTED | `cin/search.py`, M1 CI |
| `min2`, `absdiff` discovery | EXPERIMENTALLY OBSERVED | M1 development pilot, 59 and 22,698 proposals respectively |
| Finite signed-domain pass | INDEPENDENT FINITE-DOMAIN CHECK | 81/81 input pairs per relation; not universal proof |
| Full search cost and matched baselines | NOT DEMONSTRATED | Signature/prune and witness cost missing; M1 pilot only |
| Opt-in 1..8 Int signature / task-blind N-input search | IN UNMERGED PR #2 | Green CI at commit `9dd32575`; not a baseline-main capability |
| Formal three-input world contract and verified discovery | NOT IMPLEMENTED | Independent world `v0.3` and verifier required |
| Semantic novelty / uniquely functional world admission | NOT DEMONSTRATED | Old admission finds bounded witness; it does not prove output uniqueness |
| Cross-task verified abstraction library | NOT DEMONSTRATED | Replay of one solution over widened domains is not transfer |
| Reliable >=3-generation checkpointed evolution | NOT DEMONSTRATED | Current pilot is not a multi-epoch research study |
| SMT proof / bounded GCD / Bézout tuples | RESEARCH TARGET | No universal claim permitted |

**Observed M1 evidence:** `min2`: 59 proposals, 832 internal shape attempts, 722 observational prunes; `absdiff`: 22,698 proposals, 229,135 shape attempts, 197,970 prunes. Both passed 81 finite cases. These are not matched-control performance comparisons. PR #1's research experiment uses external screening examples, charges screen and final-verifier operations separately, and does **not** run admission cost accounting.

## 3. Inviolable laws and trust boundaries

The organism's genome contains **exactly** `base`, `driver`, `directive`, `maturity_point`, `stop_station`. Neither worlds, evaluation manifests, archives, proofs, population state, nor solver settings are added as genes.

The runtime remains **model-free**: no hosted LLM, pretrained code model, external solution-generation API, generated-Python execution, or inaccessible off-loop reference implementation is allowed to manufacture organism discoveries. Human engineering assistance must never be attributed to the organism.

The fixed trust sequence is:

```text
Public typed grammar + immutable policy + declared world
                        |
                Task-blind generator
                        |
               Candidate IR (untrusted)
                        |
                Static IR checking
                        |
                Bounded interpreter
                        |
       Independent world verifier [trusted]
                        |
      Scoped verdict / provenance / cost ledger
                        |
           Evidence archive [append-only]
                        |
     Governor-controlled selection / inheritance
                        |
              Deterministic offspring
```

The private witness/admission search, hidden holdout answers, solver models, and counterexample-private records never enter the unmodified generator. A separately justified **public** CEGIS interface may release scored counterexamples from **training** worlds only with charged cost and an auditable information-flow contract. Holdouts remain sealed.

Candidates cannot edit the verifier, active maturity/termination policies, proof-record semantics, hidden benchmarks, resource governor or evaluation protocol. `UNKNOWN` is not `PASS`; observational signatures are not proofs. Prevent access to arbitrary Python evaluation, imports, subprocesses, filesystem/network I/O, and generated code execution. Every generated world is untrusted structured data.

## 4. Ownership, interfaces and architectural alternatives

Keep the existing Python package and responsibility locality. Add a new module only if existing ownership becomes ambiguous.

| Owner | Existing responsibility | Next compatible evolution |
| --- | --- | --- |
| `cin/contracts.py` and versioned schemas | Admit outer immutable contract shapes | Strict `cin.world/v0.3` signature and DSL validation |
| `cin/ir.py` | Static type checking, canonical representation, bounded interpretation, readable non-executable export | Multi-input signatures, future typed outputs/iteration via separate opt-in IR versions |
| `cin/search.py` | Deterministic task-blind cost-layered enumerator and heuristic probes | Signature-derived typed grammar, search-cost ledger and explicit pruning ablation |
| `cin/worlds.py` | Formal finite-world checks; verifier-private witness admission | General input tuples, preconditions and independent existence/uniqueness checking |
| `cin/evolution.py` | Governor, selection, acceptance, replay, offspring | Birth-gated policies; deterministic lifecycle transitions |
| `cin/archive.py` | Hash-chained evidence journal | Crash-safe checkpoints and integrity recovery when needed |
| `experiments/` | Development harnesses and evidence | Frozen manifests, matched control arms, outputs and raw failures |
| `docs/` | Architectural authority and scientific interpretation | Explicit maturity ledger, phase gates, ADR decisions, research limitations |

**Decision A: incremental versioned generalization versus rewrite.** Prefer opt-in typed signature and argument-tuple execution, preserving original two-input contracts. Reject adding a benchmark-specific third-variable switch or rewriting `cin.world/v0.2` semantics.

**Decision B: bounded observational pruning versus unpruned search.** Keep pruning as **optional heuristic**, never as a semantic proof, and pay for its fingerprints. An unpruned, cost-fair control is mandatory to estimate what solutions pruning hides.

**Decision C: finite enumeration versus early SMT dependency.** First make typed mathematical interpretation stable and independently check finite domains. Add an optional version-pinned SMT verifier only when theory semantics and proof obligations are translated and cross-checked. A solver never becomes a candidate oracle or unrestricted generator.

**Decision D: one process versus distributed services.** Continue single-process deterministic execution with local data-only artifacts. No service bus, plugin framework, orchestration cluster, optional GPU assumption or new dependency without evidence of necessity.

## 5. M1 scientific closure and accounting protocol

Every experiment writes a versioned, machine-readable `cin.cost/v0.1` ledger, with a fixed measurement contract and an accompanying run manifest. Do not assume existing `SearchStats` captures all work.

**Counted units and precise denominators:**

- `generated_shape_attempts`: each intermediate AST composition attempt before acceptance/pruning, including invalid shapes; record separate `depth_rejections`, `type_rejections`, `resource_rejections`, `observational_prunes`, `retained_int`, `retained_bool`.
- `candidate_proposals_emitted`: only program IRs given to the harness; it is **not** equal to internal attempted shapes.
- `signature_probes_evaluated`: actual scalar probe-point evaluations; `signature_scalar_operations` counts arithmetic/comparisons and tuple work under a defined algorithm, not an unvalidated proxy.
- `screen_evaluations` and `screen_ir_operations`: development training-side screening; **separate** from complete verification.
- `verification_calls`, `verification_cases`, and `verification_ir_operations`: formal-domain verifier cost, including partial/failing checks; record verdict-specific totals.
- `admission_calls`, `witness_candidates`, `witness_ir_operations`, `admission_predicate_operations`: verifier-private world admission cost; mark `NOT_RUN` explicitly when absent.
- `typecheck_calls`, `typecheck_nodes_visited`, `canonicalization_bytes`: static work where technically measurable without changing semantics.
- `process_cpu_ns`, `elapsed_ns`, `peak_rss_bytes`: **non-additive envelope metrics**; do not sum them into operation counts.
- `budget_consumed`, `limit_failures`, `invalid`, `rejected`, `unknown`, `failed`, `passed`: exact outcomes and stop reason.

Counters belong at the boundary where the work occurs; each scalar operation is attributed once to an exclusive work domain. Inclusive totals must be labeled as derived **sums of disjoint subsets**. Record integer bitwidth/depth/node ceilings; version, Python, OS, architecture, commit, seed, grammar/hash, sample order, budget, proof scope and run environment. An incomplete ledger is allowed only if named incomplete.

**Critical pruning counterexample:** construct expressions identical on search probes but distinguishable at a legal out-of-probe point. Run with pruning on and off, freezing the same typed grammar, interpreter and resource budget. Report false observational equivalence as heuristic incompleteness; never relabel it as "same function".

**Matched M1 controls:** original shallow grammar, cost-layered enumeration, typed random selection, enumeration without pruning and (only if safely implemented) CEGIS. Freeze domain definitions, generated grammar, declared budgets, seeds, CPU environment, primary outcome and total accounting. Proposal limits alone are **not equal-compute comparisons**. Include unsuccessful runs and their consumed work. Explicitly distinguish exploratory pilot from preregistered confirmation.

## 6. M2 generalized typed mathematical functions

Target independent typed signature semantics:

```python
Signature(parameters=("Int", "Int", "Int"), returns="Int")
```

The example is conceptual; do not add an unused class merely to mirror syntax. Derive the same contract from the existing genome `base.input_types` and `return_type` where that is already the source of truth.

- **Version:** keep `cin.genome/v0.1` and `cin.ir/v0.1` stable; opt into v0.2 for N-input IR. `cin.world/v0.2` retains its recursive subtraction meaning; introduce `cin.world/v0.3` for variable-arity formal worlds.
- **Types:** explicit `Int` and `Bool` expression types, Int root in initial release; reject ill-typed, malformed, oversize, unknown primitive and out-of-range Arg.
- **Runtime:** deterministic bounded interpreter with strict input count/type, operation/node/depth bounds, bitwidth policy, lazy conditionals and canonical SHA-256 identity.
- **Search:** enumerate leaves from signature arity, compose typed subterms by cost, bound internal attempt count and retained banks, freeze task-independent probe scheme, and retain a no-pruning control.
- **Worlds:** independently validate preconditions/postconditions, finite input tuples and every admissible case. No candidate-generated Python or benchmark-specific `Median3`/`Clamp` primitive. A task result must not be accepted from screening or fingerprint collision.
- **Targets:** `median3(x,y,z)` with all six permutations, ties, negatives, zeros; `clamp(x,lo,hi)` with declared `lo <= hi` and exact boundary behavior. Derived finite verification domain must include precondition-true cases and explicit resource caps.

**M2 exit:** old MAX2/min2/absdiff remain valid; versioned 3+ input IR and task-independent search exist; independent v0.3 world admission and verifier exist; at least one 3-input target is *actually synthesized* within a frozen budget and receives finite exhaustive verification; other target is solved or recorded as a negative study; all failures and budgets archived.

The existence of a hand-written demonstrator program, passing unit tests on an example, or simple Arg(2) support **does not** satisfy discovery.

## 7. M3 semantically co-evolving formal worlds

A v0.3 world record has a versioned signature, named input variables/domain, declarative precondition, declarative output relation, arithmetic semantics, output scope, lineage/provenance, proof scope, admission verdict and bounded complexity. No executable user-provided predicates or generated Python.

Admit independently only after:
1. Schema + recursive formula/term depth/size and integer-bound validation.
2. Nonempty input product and at least one satisfiable precondition.
3. Consistency: every declared admissible input has an admissible result.
4. Functional uniqueness: **exactly one** result for each admissible input in **the declared mathematical output semantics**.
5. Sufficient resource budget to establish those checks; inconclusive cases remain `UNKNOWN`.
6. Witness feasibility, if the contract separately requires an admissible grammar witness, without exposing witness source.
7. Semantic novelty relative to already admitted worlds under a comparison scope that is independently justified.

A finite output search interval cannot implicitly redefine the mathematical codomain to manufacture uniqueness. Where unbounded-output uniqueness cannot be proved, admission is UNKNOWN or strictly qualified to an explicit finite output domain.

Novelty taxonomy: ID/variable renaming, equivalent commutative constraint reorder, mere numeric-range extension, and superficial constant shifts are NOT new families. A new piecewise relation, ordering/selection structure, valid non-equivalent boundary condition, or a genuinely new function family MAY be novel once independently distinguished. When equivalence is unproven, mark UNKNOWN, not "novel".

**M3 exit:** at least three admitted worlds whose mathematical relations are independently non-equivalent, with counterexamples or proofs and no oracle leakage.

## 8. M4 verified hereditary abstractions

Represent a reusable capability as a versioned record:
`capability_hash`, `typed_signature`, `ir_version`, `canonical_ir_hash`, `dependencies`, `assumptions`, `verification_scope`, `evidence_refs`, `origin_world_hash`, `discovery_cost`, `replay_cost`, `inherited_from`.

Only promote a subexpression or macro if it is type-correct, dependency-closed, acyclic, replayed by an independent interpreter/verifier, and valid under declared assumptions. Whole-program correctness is not automatically subterm equivalence on arbitrary new domains. Reject any candidate that attempts verifier-private access.

Training tasks and distinct held-out relations must be frozen before comparison. Report:

```text
No-inheritance total work: search + checks on target task
Inherited total work: initial abstraction discovery + proof/extraction
                     + replay + search + checks on target task
Net transfer benefit: difference at equal declared total compute budget
```

Count negative transfer and misleading shortcuts; revisiting MAX2 on a larger domain is **not** cross-task transfer.

**M4 exit:** at least one independently verified abstraction reused by two different mathematical relations, with accounting and a matched no-inheritance control.

## 9. M5 birth-gated deterministic generations

Every organism has immutable parentage, birth-genome hash, maturity and stop rule hashes, active policy version, accepted capabilities, and durable account ledger. The governor owns candidate survival and policy changes. Adaptation is **staged** for a descendant and cannot mutate an existing organism's fixed maturity or stopping conditions.

Transition evidence includes `PROPOSED`, `CHECKED`, `ACCEPTED`/`REJECTED`/`UNKNOWN`, `ARCHIVED`, `REPRODUCTION_ELIGIBLE`, `CHILD_COMMITTED`, and `STOPPED`. State-machine ownership must make duplicate births invalid, not merely unlikely.

Checkpoint writes require atomic replace or equivalent durable commit protocol; replay checks hashes, sequence and budgets and rejects incomplete or tampered state. Test interruption before verification, after verification before acceptance, during append-only archive persistence, before child birth, and during recovery. Record full compute cost across parents/offspring.

**M5 exit:** three legitimate generations with bytewise-or-semantically equivalent deterministic replay and no lost accounting, silent rule changes or duplicate births. Mere count of descendants is not evidence for H4/H5.

## 10. M6 proof adapter and conditional mathematical frontier

An optional independently versioned SMT adapter may classify:
`FINITE_EXHAUSTIVE`, `BOUNDED_BITVECTOR`, `SMT_VALID`, `TESTED_ONLY`, `UNKNOWN`, `INVALID`.

`SMT_VALID` means the solver established the translated formal claim with the precise quantified scope and correct arithmetic theory, **not** that a random solver call returned "sat", that a finite sample passed, or that an uninterpreted relation was assumed correct. Pin a solver version, log formula digest, timeout, model/counterexample treatment and integer-overflow translation. Cross-check bounded solver claims against the CIN interpreter.

Research-only GCD frontier: add *general-purpose* modulo/guarded bounded iteration only after its type/safety/proof contract is settled; no `Gcd` primitive; declare `gcd(0,0)=0`, signed semantics and termination/operation bounds. Later egcd requires tuples, iterative state and Bézout checks `s*a + t*b = g`, with independently scoped formal evidence.

Do not equate broader grammar with increased discovered mathematical competence.

## 11. Experimental arms, controls and holdouts

| Arm | Search | World policy | Abstractions | Offspring adaptation | Prerequisite |
| --- | --- | --- | --- | --- | --- |
| R0 | Typed random | Fixed | None | None | M1 baseline |
| R1 | Cost-fair enumeration | Fixed | None | None | M1 baseline |
| R2 | Charged training-only CEGIS | Fixed | None | None | Independent verifier feedback contract |
| R3 | Search with replayed typed macros | Fixed | Yes | None | M4 |
| R4 | Inherited abstractions | Semantically changing | Yes | None | M3 + M4 |
| R5 | Inherited abstractions | Semantically changing | Yes | Birth-gated only | M5 |

Publish only arms that exist. Each study pre-registers task-family split, hidden holdout integrity digest, eligible run count, permitted primitives, seeds, budgets, hardware class, dependency/solver versions, proof semantics and outcome aggregation. A held-out set must never be used to choose search policies, macros, probe lists, or tasks after results are inspected.

**Primary metric:** number of previously unseen *distinct mathematical relations* solved with independent proof scope divided by the full measured compute budget (or formally predeclared, auditable equivalent). Secondary measures: cumulative time/work to first pass, validation cost, failure rate, unknown rate, macro return-on-cost, negative transfer, restart integrity and memory footprint. Report distribution and uncertainty, not an invented intelligence score.

A pilot can guide engineering but cannot justify a claim of statistically significant superiority. Keep failures and truncation/censoring visible.

## 12. Adversarial validation and threat model

Negative tests cross every boundary:
- Wrong/boolean/negative argument indexes, malformed AST nodes, incorrect type/arity and unsupported schema versions.
- Deep recursive world terms, excessive formulas, oversized domains, signed arithmetic overflow and zero verification scope.
- Nonfunctional/unsatisfiable world relations, insufficient uniqueness proof, forged novelty and silent truncation of output domains.
- Fingerprint collisions outside probes, a result marked PASS after UNKNOWN, hidden-witness/program leakage into search.
- Tampered capability hash, cyclic macro dependency, expired/unreplayable evidence and stale solver proof scope.
- Interrupted archive writes, replay divergence, repeated child creation, resource-limit violations and inconsistent ledgers.

Use deterministic fixtures and real input boundaries; a mocked verifier cannot establish independent correctness. Never weaken published assertions or modify original M1 evidence to fit a new implementation.

## 13. Maturity ledger: independent evidence axes

Every dimension records `status`, `evidence`, `scope`, `limitations`, `regressions`, `unmet_exit_criteria`, and `next_required_experiment`. No fabricated integer scores.

| Axis | Current evidence boundary | Next falsifiable gate |
| --- | --- | --- |
| Expressiveness | Two-input M1 IR merged; N-input proposed in PR #2 | Three-input formal-world verification |
| Discovery | min2/absdiff M1 finite pilot | median3 or clamp independently discovered |
| Correctness | M1 81-case finite verification | Signed/duplicate three-input exhaustive scope |
| Generalization | Signed finite-domain M1 tests only | Sealed inputs and genuinely distinct relation |
| Knowledge reuse | No accepted cross-task macro study | M4 inherited vs control |
| Evolution | Legacy parent/child replay pilot | Three persisted restart-safe generations |
| Adaptation | No validated policy advantage | R5 vs frozen-policy control |
| Efficiency | Partial M1 ledger only | Matched full-compute baseline study |
| Reliability | Existing test/CI and hash journal | Interruptions and atomic recovery |
| Research integrity | M1 development pilot with named omissions | Frozen protocols plus negative trials |

When a new PR lands, update the ledger using actual commit IDs, machine-checkable evidence and remaining counterexamples, not a release label alone.

## 14. Ordered, bounded implementation roadmap

**G0: M1 measurement closure** (independent research PR): add cost ledger `v0.1`, count fingerprints/witness costs, fixed-probe collision regression tests, optional pruning ablation, and two comparable search baseline arms before superiority claims. Finish minimal defensible pilot; document unresolved statistical limits.

**G1: M2 IR + signature/search foundation** (PR #2, independent of G0's statistical confirmation): add opt-in N-input contract, typed checks, interpreter/export, deterministic bounded search and legacy regressions. Pass full repository tests and both old M1 synthesis runs. **The PR must not claim M2 discovery.**

**G2: M2 independent three-input worlds** (new implementation PR): add opt-in world v0.3 schema, input tuple/term evaluator, precondition and postcondition, finite verification and non-vacuity handling; prove malformed spec/arity fail closed; add median3 and clamp worlds without reference-code ingestion.

**G3: M2 search benchmark** (new measured PR): freeze budgets, search grammar, probes and at least one new solved 3-input relation; archive failures, independent 3-input finite verification and cost ledger. If neither target is solved, report negative pilot and improve search only through an explicit research decision.

**G4: M3 semantic novelty**: independent admissibility + output existence/uniqueness + relation novelty, three verified relation families; reject UNKNOWN and superficial mutations.

**G5: M4 knowledge transfer**: typed, dependency-closed macros and distinct-task comparisons that include origin costs.

**G6: M5 lifecycle**: deterministic population/generation checkpoint recovery and immutable birth rules, interrupt/replay tests.

**G7: optional SMT, GCD, egcd**: separately authorized math and solver gates, never a forced dependency to release G1–G6.

Each PR has one falsifiable outcome, touched-file list, tests with RED/GREEN when behavior changes, immutable benchmark references, versioned contract notes, observed resource/costs, risk/rollback, and known limitations. Unmerged dependent PRs must be explicitly stacked or postponed. Never commit directly to main, self-approve, or merge without user authority.

## 15. Standard evidence packet and release acceptance

A proposed research artifact must include:
- Exact base/head SHA, original source files, setup commands and dependency versions.
- Declared experiment ID, task/world/hash, legal grammar, seeds, proof scope, stop conditions and holdout commitment.
- Machine-readable per-run cost ledger and all outcomes, including INVALID, FAIL, UNKNOWN and resource exhaustion.
- Directly runnable targeted tests, full repo tests, lint/schema checks, applicable CI runs, and adversarial negative results.
- Discrepancies between CPU/elapsed, candidate proposals, attempted shapes, signature work and verifier calls.
- Separation between what was implemented, independently verified, experimentally observed, failed/inconclusive, unproven and the next justified gate.
- Versioned migration plan and rollback strategy if a public contract changes.

**Reproduction from repository root** (commands are existing documented entry points; they do not reproduce future unimplemented milestones):

```bash
python -m cin validate
python -m pytest -q
python experiments/run_m1.py
python -m ruff check .
python -m ruff format --check .
```

No M2/M3/M4/M5/M6 gate is complete merely by writing this specification.

## 16. Research grounding, scope and unknowns

Foundational synthesis formulation: [SyGuS project](https://sygus.org/). For enumerative synthesis and observational pruning see the existing [ADR 0005](../adr/0005-cost-layered-observational-search.md) and [repository literature ledger](../research/LITERATURE.md). Current academic context includes [Frankel et al., *Syntax-guided synthesis with counterexample-guided E-graphs* (SMT 2025 workshop)](https://www.research.ed.ac.uk/en/publications/syntax-guided-synthesis-with-counterexample-guided-e-graphs-a-wor). These justify investigating alternatives, not an empirical claim that CIN is superior.

Open design decisions must be resolved experimentally: signature-fingerprint completeness versus cost; whether a bounded output codomain is an honest task contract; witness admission search expense; feasibility of relational uniqueness proofs; when CEGIS training feedback is worth its leakage risk; conditions under which macro extraction reduces *total* computation; and which crash-fault boundaries require durable checkpoints.

**Release semantics:** version 0.6 identifies this **mission specification**, not `cin` package v0.6, universal correctness, true open-ended intelligence or verified cross-task learning.
