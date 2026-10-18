# ADR 0008: Finite in-process epochs and conservative budget reservation

**Status:** Proposed in [PR #5](https://github.com/imMamdouhaboammar/code-in-nothing/pull/5), dependent on unmerged P1-01 [PR #4](https://github.com/imMamdouhaboammar/code-in-nothing/pull/4).  
**Date:** 2026-10-18

## Scope and decision

The first P1-02 slice introduces `cin/governor.py` and an **opt-in** `FiniteScheduler` without changing the legacy `Experiment` CLI, world schemas, verifier verdicts, generated grammar, five genes, or historical experiments.

- The single-process governor owns immutable nonnegative `Cost` limits, per-actor spending, cohort spending, outstanding reservations, and terminal reasons. A single-use grant reserves a ceiling before work and settles measured actuals afterward; unused capacity returns to the available total. Overspend at settlement terminally fails closed; a denied prospective reservation makes no state change.
- The scheduler runs the existing task-blind generator and finite-world verifier across bounded epochs, with `max_epochs`, `proposals_per_epoch`, `max_candidate_evaluations`, `plateau_grace_epochs`, and `plateau_consecutive_epochs` enforced as actual stop rules. A verified starting seed is not counted as newly acquired capability. A new discovered candidate must independently pass twice; no target program is manually installed.
- World admission receives a capped proposal count. Optional verifier-side `AdmissionStats` exposes **only counters**, not witness expressions. The admission candidates and verifier/interpreter/probe/shape work are charged even when admission returns `UNKNOWN`. The old `admit_world` interface remains compatible when stats are omitted.
- Signature probe accounting counts task-independent observation points from `candidate_stream`. Cost ceilings for verifier operations and probe work are conservatively reserved based on the existing interpreter case bounds and the generator's existing finite shape cap. Only actual observed work is finally charged. These are in-process bounds, not crash-safe durability guarantees.
- The scheduler is an explicitly separate experimental API. It returns a deterministic summary and caches terminal output, so calling `run()` after completion cannot restart the organism. It does **not** publish a new `BIRTH` event, add a second source of lineage truth, or pretend domain extension is semantic novelty.

## Why this shape

Prefer a typed, small Python in-memory governor over a database-backed event coordinator until P1-03 defines atomic checkpoint and child-publication transactions. Keep world admissions and search implementations responsible for their private internals; expose measured scalar work through optional stats. A scheduler cannot inspect the witness itself.

Rejected now: distributing actor processes, adding a solver, inventing abstractions, exposing private admission witnesses to cost metrics, and changing existing `cin.world/v0.2` semantics.

## Measured evidence and limitations

Read [PR #5 GitHub Actions](https://github.com/imMamdouhaboammar/code-in-nothing/actions) for the final HEAD's test matrix and lint status. Tests cover multi-epoch termination, candidate budget across epochs, plateau stop, bounded negative/UNKNOWN admission, unmutated verified seed, deterministic run, separated actor accounting, single-use grants, and terminal immutability.

**Not demonstrated:** complete end-to-end cost normalization. Current counters do not yet bill all declarative formula evaluation, static type validation, failed lookups, persistence, CPU/memory, or interruption/restart work. The scheduler supports only one active organism and **does not** generate or persist multiple generations. This must not be treated as full P1-02 or P1 acceptance.

Next targeted PR: connect P1-02 counters into a fuller governor/experiment integration, strengthen cost ceilings with explicit operation-based limits, and implement a real parent/offspring scheduling state model under the unchanged five-gene lifecycle. P1-03 then owns checkpointed state, atomic evidence/birth publication, crash injection, exactly-once child IDs and budget-preserving resume. Only after these gates pass may work advance to independent three-input-world verification.
