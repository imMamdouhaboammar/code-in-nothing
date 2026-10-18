# ADR 0007: Manifest-bound completed-run replay before checkpointing

**Status:** Proposed in [PR #4](https://github.com/imMamdouhaboammar/code-in-nothing/pull/4).  
**Date:** 2026-10-18  
**Baseline:** `main` at `653ef4efa7acf25395cc99d5fac21bc1cf2ee563`.

## Context

Before P1, `Archive` persisted a hash-linked JSONL event stream, but lacked a versioned record of which public experiment inputs and resource settings generated it. The one-epoch `Experiment` could not independently reproduce a saved run. A valid chain alone cannot establish scientific reproducibility or authentication.

P1-01 needs an independently checkable baseline before scheduler, recovery, and new mathematical worlds are allowed to advance.

## Decision

1. Write an exclusively created `manifest.json` **before** admission or candidate evaluation. Store the validated public five-gene genome, declared world, nonnegative seed, effective candidate/epoch policy, evolution/inheritance switches and exact runtime/verifier version strings. Never persist verifier-private witness implementations, sealed evaluations or generated Python as an oracle.
2. Bind the manifest digest to the first `COHORT_MANIFEST` journal event. Reject unknown versions, bad policy types, missing/truncated files, broken hash links, mismatched manifest digests and incomplete terminal pairs.
3. Normalize scientific event payloads by dropping **only** incidental `resources.cpu_ms` from `GROWTH_EVIDENCE`. Preserve every operation count, event kind/order, input hash and verdict.
4. Reproduce a **completed** run in a fresh temporary archive by rerunning the existing typed synthesizer and independent finite-world verifier with the recorded configuration. Compare normalized complete traces. Disagreeing traces cause an explicit divergence error, never success.
5. Preserve v0.1 legacy journal verification. Legacy archives without manifests cannot retroactively claim independently reproducible runs.

An integrity digest is not a signature. Anyone able to modify both the manifest and journal can recompute hashes; the reexecution gate detects behavioral divergence but cannot authenticate a maliciously rewritten, internally consistent history.

## Alternatives

- **JSONL alone:** rejected because it does not bind the run to its immutable public configuration and does not reexecute the verifier.
- **Introduce SQLite/checkpoints immediately:** deferred to P1-03. SQLite transactions can address atomic state publication once finite scheduler and birth transitions are specified, but adding a second state store to a single-epoch pilot now would not prove restart or exactly-once birth. Primary reference: [SQLite atomic commit](https://sqlite.org/atomiccommit.html).
- **Compare generated Python output:** rejected. Generated Python is an export, not the bounded CIN-IR executor or independent proof mechanism.

## Evidence and limits

[RED CI 39159431105](https://github.com/imMamdouhaboammar/code-in-nothing/actions/runs/39159431105) recorded seven new failed tests against the absent API. [GREEN CI 39160027507](https://github.com/imMamdouhaboammar/code-in-nothing/actions/runs/39160027507) passed the full OS/Python matrix after implementation and formatting correction. [CodeQL 39160027581](https://github.com/imMamdouhaboammar/code-in-nothing/actions/runs/39160027581) succeeded.

These tests establish completed-run reproduction and bounded artifact validation on the declared finite-world pilot. They **do not** establish interrupted-run recovery, durable checkpoint atomicity, accounted cross-actor compute, three persisted generations, universal mathematical proof or positive search-policy gains.

## Next gates

P1-02 must enforce per-actor and global budgets for generator, shape/signature work, screening, admission/witness search, independent verification and replay; produce an explicit multi-epoch scheduler with stop idempotence. P1-03 then owns crash-safe atomic journal/checkpoint/birth transitions and recovery. Neither is implied by this ADR.
