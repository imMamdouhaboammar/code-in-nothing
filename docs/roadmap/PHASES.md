# CIN phased research and engineering roadmap

**Status:** Approved research direction, proposed implementation order; no delivery dates.  
**Source of requirements:** [Integrated specification v0.4](../specs/2026-10-18-cin-integrated-system-spec-v0.4.md).  
**Implementation checklist:** [Next-phase plan](../plans/2026-10-18-cin-next-phases.md).

**Deep mathematical synthesis extension:** [v0.5 math roadmap](MATH-PHASES.md) and [integrated math spec](../specs/2026-10-18-cin-mathematical-evolution-v0.5.md) define research targets only, not additional implemented milestones.

## Dependency map

```mermaid
flowchart LR
    P0[P0 Existing pilot] --> P1[P1 Durable multi-epoch lifecycle]
    P1 --> P2[P2 New formal task semantics]
    P2 --> P3[P3 Hereditary abstraction reuse]
    P3 --> P4[P4 Driver adaptation]
    P2 --> P5[P5 Preregistered evaluation]
    P3 --> P5
    P4 --> P5
    P5 --> P6[P6 Conditional proof/runtime expansion]
```

The gates are sequential where there is a real dependency. Parallel work on documentation, tasks and baselines is allowed, but do not use a label such as `P3` to imply earlier gates have passed.

## P0: Preserve the existing working pilot

**Current status: implemented and tested at documentation baseline.** The five-gene schema, typed IR, finite-domain world checking, one acquisition of MAX2, one derived world domain extension, replay-gated child, hash-chain log and CLI exist. See [results](../../experiments/RESULTS.md).

**Gate:** `python -m pytest -q`, `python -m cin validate`, normalized fixed-seed replay, no changes to `examples/` schemas unless versioned. **Claim permitted:** one bounded model-free program-synthesis and mechanical reproduction path. **Claim forbidden:** general coding, novel semantic world evolution, self-improving search policy.

## P1: Deterministic multi-epoch evolution with durable evidence

**Goal:** Run more than one epoch/generation while preserving finite budgets, immutable contracts and exactly-once terminal events.

**Scope:** scheduler owning epoch state, configurable selection, population bound, pause/crash/replay at transaction boundaries, versioned run manifest, per-actor governor counters. Preserve current CLI; add opt-in experimental commands only if tested.

**Acceptance:** (a) 3 generations can be created from allowed evidence with exact parent DAG and no duplicate IDs; (b) 20-epoch/budget stop policies enforced, not only parsed; (c) stop and resume produces same normalized outcomes as uninterrupted run; (d) a crash after promotion before birth does not double-create child; (e) world admission candidate work is metered. Negative tests: forged child event, restart budget reset, after-death mutation, duplicate event, invalid epoch.

**Non-goals:** genuinely new world functions, learned policies, cloud workers, general APIs. **Claim permitted:** controlled multi-generation lifecycle and durable replay.

## P2: Semantic world co-evolution

**Goal:** Generate and independently admit *different function relations*, not only different domains.

**Scope:** versioned formal task normal form, finite relation templates and task-family descriptors, equivalence/differentiation checks, world ancestry, unknown/not-admitted handling and world population diversity controls. Initial relations may include max/min/bounded addition, provided all are expressible by the IR and independently verified.

**Acceptance:** at least 3 admitted formal tasks spanning at least 2 demonstrably distinct semantic families under a shared comparison domain; failed/unknown world proposals remain unadmitted; input-range expansion never increments distinct-function count; witness implementation never returned to organism; budget comparison against fixed-world conditions. Negative tests: tautological postcondition, impossible relation under fixed grammar and budget (`UNKNOWN` not impossibility), duplicate semantics with new ID, result-dependent precondition, over-budget domain.

**Non-goals:** learned abstractions and unbounded integers. **Claim permitted:** independent evolution of formally distinct challenge worlds.

## P3: Cross-task hereditary abstractions

**Goal:** Produce verified reusable macros and demonstrate that inherited abstractions help solve genuinely different functions.

**Scope:** typed macro representation and dependency closure, extraction from accepted programs, safe application/composition, all affected-task regression replay, child inherited library and parent hash chains, macro-enabled vs macro-disabled comparison.

**Acceptance:** an abstraction appears as a dependency in accepted solutions for >=2 functionally distinct tasks; child retains exact artifact ancestry; removing it changes held-out solve cost or success at matched budget; no replay regression; rejected/unknown abstractions do not propagate. Negative tests: circular macro dependency, stale certificate, collisions, mismatched type, cross-domain replay failure and false family claim.

**Non-goals:** neural policy and self-generated arbitrary Python. **Claim permitted:** verified cross-task software knowledge transfer with measured search effect.

## P4: Restricted growth-driver adaptation

**Goal:** Learn which typed mutation operators to prioritize, without allowing the driver to redefine success or budgets.

**Scope:** versioned bounded policy parameters, approved mutation of offspring policy only, blinded head-to-head replay on tasks not used for policy selection, policy ancestry, rollback, compare against fixed uniform and hand-tuned policies. Start with deterministic score/bandit updates; no trained neural model required.

**Acceptance:** reproducible policy change is behaviorally effective, externally checked for no correctness regression, passes limited held-out efficiency test under accounted budget, and has a reversible ancestry record. Negative tests: policy attempts to change evaluator weights/holdout access, negative weights, changing active stop policy, selection data leak and overfitted policy.

**Non-goals:** altering the verifier, automatically modifying arbitrary host source. **Claim permitted:** bounded search-strategy adaptation under independent governance.

## P5: Rigorous comparative research

**Goal:** Evaluate H1-H3, including possible negative results, with matched-resource controls and holdout.

**Scope:** freeze corpus, grammar versions, canonicalization, training/holdout split, C0-C4 arms, resource ledger, independent evaluation, descriptive and confirmatory statistics according to preregistered plan, openly preserved failure cases.

**Acceptance:** preregistered protocol before test release, measured cost in every arm, independent seeds with distributions/intervals, zero holdout leakage, correct task-family denominators, independent replay of all reported effect sizes. Any null/negative result is reported without changing endpoints. Negative tests: cross-arm budget mismatch, premature holdout access, missing failed proposals, incorrectly counted MAX2 domain variants.

**Non-goals:** promised positive performance, benchmark leaderboard claims without equivalent protocols. **Claim permitted:** evidence either for or against specific CIN hypotheses at stated scope.

## P6 (conditional): Richer proofs and execution models

**Entry condition:** P5 reveals a concrete bottleneck that cannot be addressed safely with simpler current design, and a threat-model review approves the expansion.

Possible directions: optional SMT/SyGuS proof over supported theories, guarded new CIN-IR primitives, richer typed data domains, independent OS-sandbox workers for proposed arbitrary source, longer-term multi-actor execution. Each is an **independent proposal**, not a bundled rewrite.

**Gate:** solver UNKNOWN/timeout distinct from proof, new grammar soundness tests, interpreter isolation and resource ceilings proved with malicious generated inputs. **Claim forbidden:** “general autonomous software engineer” from richer opcodes alone.

## Prioritized dependency-ordered work packages

| Priority | Work package | Owner boundary | Delivery evidence |
| --- | --- | --- | --- |
| 1 | `P1-01` immutable cohort manifest + normalized replay | Controller | identical scientific event sequence under restart |
| 2 | `P1-02` scheduler + finite lifecycle + governor | Scheduler/governor | multi-epoch stop/budget and failure tests |
| 3 | `P1-03` durable journal/checkpoint | Archive | crash injection & no duplicates |
| 4 | `P2-01` semantic relation normalizer/novelty oracle | Worlds/verifier | distinct-function and duplicate tests |
| 5 | `P2-02` admissible world mutation/curriculum | Worlds | independent witness/unknown/budget tests |
| 6 | `P3-01` macro representation and replay | Growth/verifier | functional reuse and cycle prevention |
| 7 | `P3-02` inherited macro ablation | Research controller | matched-cost heldout evidence |
| 8 | `P4-01` driver variants and gated adaptation | Growth/controller | policy A/B and rollback evidence |
| 9 | `P5-01` frozen controlled study | Research controller | preregistration + reproducible report |

## Stop or simplify triggers

- P1 is not stable: stop new research features until resume/resource accounting is correct.
- P2 cannot produce nontrivially distinct solvable tasks: keep fixed worlds and publish limitation rather than claim co-evolution.
- P3 macro benefit disappears after full discovery costs: retire macro mechanism or narrow the claim.
- P4 fails on heldout tasks: retain simpler fixed policy.
- More abstractions/dependencies/services than accepted new capabilities: remove architecture layers before adding more.
- No measured case for hosted worker / Rust / neural model: keep the Python monolith.

The next engineering action is `P1-01`, not expanding grammar or building UI. See [P1 plan](../plans/2026-10-18-cin-next-phases.md).
