# CIN Next Phases Implementation Plan

> **For agentic workers:** Use the host's task-by-task implementation workflow. Steps use checklist syntax. This is a **future implementation plan**: no tasks below have been executed by the documentation-only change.

**Goal:** Advance the working v0.1 synthesis pilot into a reproducible multi-generation system, then demonstrate semantically novel evolving worlds, hereditary abstractions and blinded matched-budget tests.

**Architecture:** Extend the current Python modular runtime incrementally. Keep CIN-IR as data, the verifier independent from mutation/world search, and experiment state versioned and finite. Add persistence or new packages only when focused tests prove a need.

**Tech Stack:** Existing Python 3.11+, stdlib, PyYAML, jsonschema and pytest. SQLite via stdlib is a candidate for P1 persistent state; cvc5/NumPy are **not** dependencies or requirements for the first two phases.

**Spec:** [`docs/specs/2026-10-18-cin-integrated-system-spec-v0.4.md`](../specs/2026-10-18-cin-integrated-system-spec-v0.4.md).

## Global constraints

- Preserve exactly the five genes with frozen active maturity/stop contracts.
- No LLM, pretrained code generator, arbitrary generated-Python execution, remote services, or host modification.
- Independent verifier owns verdict and admission semantics; `UNKNOWN` is never promoted.
- All budgets include world admission and replay, not only candidate-generation count.
- Preserve existing CLI and v0.1 archived evidence scope, unless explicitly introducing a versioned replacement.
- Any change needs focused failing tests before implementation; then run complete `python -m pytest -q` and `python -m cin validate`.
- Do not interpret this plan as permission to push Git changes or release experimental code automatically.

## Review focus: failure modes to pin before implementation

1. Crash just after accepted growth and before offspring write: restart must not produce duplicate offspring or reset budget.
2. Different `world_id` with equivalent MAX2 relation: unique semantic task count must remain one.
3. World admission consumes witness compute and fails to find a witness: the budget is charged and verdict is `UNKNOWN`.
4. Inherited macro dependency graph contains a cycle or changed verifier version: reject birth until valid replay.
5. Holdout accessed by driver/world generation before final assessment: abort compromised research cohort; do not promote apparent improvements.

---

### Task 1: Reproducible multi-epoch state and ledger (P1-01 / P1-02)

**Proposed files:** `cin/scheduler.py`, `cin/governor.py`, `tests/test_scheduler.py`, `tests/test_governor.py`.  
**Existing integration:** `cin/evolution.py`, `cin/ir.py`, `cin/worlds.py`, `cin/__main__.py`.

**Inputs:** `validate_genome()`, `admit_world()`, `verify_program()`, `candidate_stream()`, `Archive`.  
**New interfaces (proposed):** `Scheduler.step(cohort: Cohort) -> list[Event]`; `Governor.reserve(actor_id: str, proposed: Cost) -> Grant`; `Governor.charge(grant: Grant, actual: Cost) -> BudgetSnapshot`; `Governor.stop_reason(actor_id: str) -> str | None`.

- [ ] Write a failing test for deterministic 3-epoch progression with `max_epochs`, proposal-per-epoch, total candidate and verifier budgets, plateau handling and terminal idempotence.
- [ ] Write negative tests for missing actor, invalid epoch, duplicate birth, exhausted governor grant, late mutation after stop, witness-work omission and stop policy tampering.
- [ ] Run `python -m pytest -q tests/test_scheduler.py tests/test_governor.py` and record expected missing interface failures.
- [ ] Implement a sequential one-worker scheduler that owns epoch state and calls existing modules without changing verifier semantics; charge all known operations, use immutable per-actor budgets.
- [ ] Re-run focused tests and full suite, require all PASS and unchanged v0.1 demo outputs under existing flags.

### Task 2: Durable checkpoint and restart (P1-03)

**Proposed files:** `cin/checkpoint.py`, `tests/test_checkpoint.py`.  
**Existing integration:** `cin/archive.py`, `cin/evolution.py`, `cin/__main__.py`.

**Inputs:** scheduler state, canonical artifact hashes and authoritative append events.  
**New interface (proposed):** `CheckpointStore.commit(epoch_state: dict, events: list[dict]) -> str`; `CheckpointStore.restore(manifest_hash: str) -> dict`.

- [ ] Add failing tests for crash at before-commit, after-event and before-child-publication boundaries; assert no duplicated event/child and no revived terminated actor.
- [ ] Add corruption, missing artifact, mismatched manifest, incompatible schema, partial write and consumed-budget reset tests.
- [ ] Run `python -m pytest -q tests/test_checkpoint.py`; observe missing features.
- [ ] Introduce the minimum durable single-writer checkpoint mechanism; SQLite stdlib transactions are a reasonable implementation if atomicity cannot be proven with JSONL. Preserve original journal for prior runs.
- [ ] Run focused tests, fixed-seed interrupted/uninterrupted comparison and full suite. Record matching normalized decisions, not necessarily identical CPU timing.

### Task 3: Semantically distinct world admissions (P2-01 / P2-02)

**Proposed files:** `cin/world_generation.py`, `tests/test_world_generation.py`.  
**Existing integration:** `cin/worlds.py`, `cin/contracts.py`, `cin/ir.py`, formal world schema versioned if needed.

**Inputs:** immutable world spec, grammar, verifier call and world budget.  
**New interfaces (proposed):** `propose_world(parent: dict, rule: str) -> dict`; `distinguish_tasks(left: dict, right: dict, proof_scope: Scope) -> NoveltyVerdict`; `admit_semantic_world(proposal: dict, budget: Budget) -> Admission`.

- [ ] Add failing tests where `max(x,y)` and `min(x,y)` are distinguished on common inputs; range-expanded MAX2 and renamed MAX2 are not novel.
- [ ] Add tests for contradictory/vacuous preconditions, result not constrained, unknown witness, malformed grammar, and finite-domain overflow; assert admission cannot happen without witness and novelty verdict.
- [ ] Run the new focused tests and record expected missing behavior.
- [ ] Implement a minimal relation-template generator and equivalence/counterexample gate; preserve old `admit_world` behavior under its existing API.
- [ ] Verify focused tests, full suite, and an explicit pilot generating >=2 genuinely different admitted functional relations within budget.

### Task 4: Typed hereditary macro composition (P3-01 / P3-02)

**Proposed files:** `cin/abstractions.py`, `tests/test_abstractions.py`.  
**Existing integration:** `cin/search.py`, `cin/evolution.py`, `cin/ir.py`.

**Inputs:** accepted program ASTs with scope certificates and verified skill dependencies.  
**New interfaces (proposed):** `extract_macros(programs: list[VerifiedProgram]) -> list[Macro]`; `resolve_macro_closure(macros: list[Macro]) -> MacroBundle`; `verify_macro_use(bundle: MacroBundle, target: World) -> Verdict`.

- [ ] Write failing tests for shared AST subexpressions, nested macro type constraints, deterministic hashes and dependency closure.
- [ ] Add tests rejecting circular/self references, stale certificates, changed limits and a claimed new family that is really MAX2 again.
- [ ] Observe focused missing-interface failures; implement simplest AST-level macros, without e-graphs or neural search.
- [ ] Verify macro use in two different semantic task relations and show whether search cost on withheld tasks improves against a macro-disabled control with extraction cost included.
- [ ] Run full suite and report both positive and negative metrics; no proof of benefit if improvement absent.

### Task 5: Gated driver policy experiments (P4-01)

**Proposed files:** `cin/driver_policy.py`, `tests/test_driver_policy.py`.  
**Existing integration:** `cin/search.py`, `cin/evolution.py`, scheduler and governor.

**Inputs:** frozen operator list, observed training rewards, fixed policy test panel and budgets.  
**New interfaces (proposed):** `propose_policy(parent: DriverPolicy, training: PolicyEvidence) -> DriverPolicy`; `compare_policies(candidate: DriverPolicy, baseline: DriverPolicy, panel: TaskPanel) -> PolicyDecision`.

- [ ] Add tests for immutable active policy, normalized valid weights, fixed-seed reproducibility, no evaluator/stop mutation, budget parity and rollback.
- [ ] Run focused tests in RED state; implement a bounded deterministic/tabular search policy update, gated only at offspring birth.
- [ ] Evaluate candidate vs fixed baseline on blinded tasks, account for adaptation itself and all verifier operations; do not promote a policy without proof of non-regression.
- [ ] Run full suite; report any absence of improvement without forcing positive metrics.

### Task 6: Preregistered matched-budget experiment (P5-01)

**Proposed files:** `cin/research.py`, `tests/test_research.py`, `experiments/study-protocol.md`, generated run reports outside source (unless curated).  
**Existing integration:** all prior interfaces and CLI as needed.

**Inputs:** frozen corpus, cohort manifests, C0-C4 arm definitions, sealed task set and resource ledger.  
**New interface (proposed):** `run_study(plan: StudyPlan) -> StudyReport`.

- [ ] Write tests that reject missing budget fields, leaking the sealed set, mixing evaluator versions, biased denominators and counting range-only world mutations as new semantic tasks.
- [ ] Run focused RED tests; implement only the orchestration needed for fair arms and normalized results, with explicit `NOT_EVALUATED` when holdout is untouched.
- [ ] Freeze research hypotheses and task hashes before running study arms; release holdout once per cohort under separate access.
- [ ] Report all seeds and failures, uncertainty intervals, total operations including world admission and macro-learning overhead; do not change endpoints after results.
- [ ] Verify full suite, reproduction on a separate clean install, archive chain and stated limitations.

## Deferred decisions with defined seams

- A proof-capable external solver is optional and only justified when finite-domain tests are the limiting factor. Its `UNKNOWN` result is explicit and its witness stays verifier-private.
- SQLite vs carefully transactioned JSONL is an implementation choice for Task 2; choose based on crash tests and cost, not on framework fashion.
- New grammar/type families are versioned proposals, not a prerequisite for proving world semantics under the existing integer IR.
- An OS-sandbox worker is a **blocking prerequisite** if generated code becomes arbitrary Python, not an optional hardening after that feature ships.

**Next action:** Start Task 1 with failing scheduler/governor tests. Each task is an independently reviewable deliverable; do not implement all phases in one PR.
