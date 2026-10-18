# CIN Deep Math: Implementation and Research Plan

> **For agentic workers:** Implement the earliest unmet gate in a reviewable PR, verify it, and only then consider the next gate. Use test-first logic for new behavior. This is a **plan**; nothing below is implemented simply because it is listed.

**Goal:** Evolve progressively more capable mathematical programs without code-model dependencies and demonstrate distinct, independently verified mathematical functions across generations.

**Architecture:** Extend the existing CIN-IR and grammar through *versioned* contracts, separating organism proposals, world-spec proposal/admission, verifier-private witnesses, archive and final sealed research evaluation. The first PR improves the current two-input typed synthesis and introduces `min2`/`absdiff` without changing public schema semantics. Later PRs add typed multi-argument programs, semantic world evolution, learned abstractions and verified bounded Euclid.

**Tech stack:** Existing Python 3.11+, PyYAML, jsonschema, pytest, ruff. Optional proof solver only after the solver boundary and version are independently verified and benchmarked. No web API, hosted/local LLM dependency, GUI or unrestricted generated Python runtime.

**Spec:** [v0.5 integrated math specification](../specs/2026-10-18-cin-mathematical-evolution-v0.5.md), [benchmark](../research/MATH-BENCHMARK-PROTOCOL.md), [roadmap](../roadmap/MATH-PHASES.md), [v0.4 laws](../specs/2026-10-18-cin-integrated-system-spec-v0.4.md).

## Global constraints

- Exactly 5 genes; `maturity_point` and `stop_station` immutable in an individual's active life.
- No witness/solver solution or sealed holdout may drive organism candidate generation.
- No `exec`/`eval`, generated Python imports, network, unconstrained host calls or privileged file writes.
- Keep existing v0.1 CLI, example genomes/worlds, output reports, journals and tests valid.
- Admit an exact finite-domain `PASS` only for its declared domain; `UNKNOWN` and `INVALID` never promote growth.
- Count all program synthesis, world admission, counterexample checking and macro-mining costs in scientific comparisons.
- Explain each semantic schema/IR change and test compatibility; no automatic maturity claims.
- Use latest code and open PR/issue state from GitHub as ground truth; do not treat this sandbox ZIP as repository HEAD.

## Review focus

1. **Depth:** ASTs that meet static depth but violate runtime cap must be rejected; program nodes remain typed throughout.
2. **Duplicate search:** same AST discovered twice must not consume a distinct accepted capability, and behaviorally equivalent ASTs must not be claimed universally equivalent from sampled data.
3. **Mathematical edges:** signed inputs, ties, zeros and piecewise boundaries are checked separately.
4. **Budget parity:** verify world witness cost and failed trials don't disappear from R0-R5 accounting.
5. **Attribution:** solver search and hidden proofs may verify but never be counted as organism-discovered source.

---

### Task M1-01: Freeze v0.1 behavior and new mathematical task fixtures

**Observed files:** `cin/ir.py`, `cin/search.py`, `cin/worlds.py`, `cin/evolution.py`, `tests/`, `examples/`, `pyproject.toml`.

**Proposed files:** `tests/test_math_worlds.py`, `examples/world-min2.v0.1.yaml`, `examples/world-absdiff.v0.1.yaml` if existing v0.1 formula grammar expresses their intended semantics, otherwise add v0.2 explicitly with negative compatibility tests; `experiments/math-baseline.md` for actual run commands/outcomes.

**Interfaces:** Consume `validate_world`, `verify_program`, `candidate_stream`; produce two positive formal task fixtures and named failing synthesis tests.

- [ ] Inspect actual `main`, existing tests and open PRs; capture working-tree status and baseline `python -m pytest -q`, `python -m cin validate`, `python -m ruff check .` if configured/installed.
- [ ] Add focused failing tests for signed negative absdiff, ties, wrong branch, vacuous/impossible predicates, wrong input type, and verifier proof-scope reporting.
- [ ] Decide whether current DSL can uniquely specify `absdiff`. If not, create a versioned schema/validator in the **same minimal PR** rather than smuggling unverifiable behavior into a YAML fixture.
- [ ] Prove tests fail before implementation; run full test suite after each coherent change. Existing MAX2 examples and hashes must remain valid.

**Gate:** Exact `min2` and `absdiff` contract tests distinguish correct code from wrong but superficially plausible code. No invalid world can return `PASS`.

### Task M1-02: Cost-fair model-free search

**Observed ownership:** `cin/search.py` for proposal generation, `cin/ir.py` for typing/evaluation. **Proposed:** `tests/test_math_search.py`; no separate search-framework hierarchy unless required.

**Interfaces:** Preserve existing `candidate_stream(parent, base, seed, max_proposals)` or create a small explicitly versioned optional alternative; return existing `Proposal` and valid typed IR trees. No solver results enter candidate generation.

- [ ] RED tests: nested conditional + arithmetic branches are eventually considered within a bounded cost; deterministic seed replay; no duplicate canonical ASTs; strict operator/max_nodes/max_depth/proposal ceilings; no generated `Gcd`, arbitrary input index or new unexpected operator.
- [ ] Implement bottom-up size/cost-fair enumeration plus parent composition, using stable ordering and bounded caches. Avoid O(all previous AST pairs) blowup without accounting; instrument invalid and duplicate proposals.
- [ ] Prove GREEN: synthesize new `min2` and `absdiff` from the seed against independent finite-domain contracts; record proposal count, interpreter ops and elapsed CPU diagnostics honestly.
- [ ] Run baseline MAX2 and existing CLI unchanged; compare against original search and typed random baseline at equal declared budgets. If not solved, preserve failure and write a defensible narrower next step, never paste target solution into generator.

**Gate:** Two distinct valid functions, no regression and reproducible evidence. Rollback: disable new search strategy using a versioned selection path, not broken protocol shims.

### Task M2: Typed multi-argument world/IR migration

**Proposed interfaces:** `Signature(params: tuple[Param,...], returns: CINType)` and versioned `cin.ir/v0.2`, `cin.world/v0.2` schemas. Existing v0.1 signatures unchanged. **Likely touched:** `cin/ir.py`, `cin/worlds.py`, `cin/contracts.py`, `cin/search.py`, `tests/test_math_signatures.py`, `tests/test_math_worlds.py`.

- [ ] RED: third argument accepted only for v0.2 typed world; invalid indexes, duplicate names, wrong returns and unsigned legacy-world migrations fail cleanly; v0.1 remains unchanged.
- [ ] Implement typed argument-list interpreter adapter and semantics-preserving renderer; no arbitrary untrusted Python execution.
- [ ] Demonstrate `median3` and `clamp` across signed, tie, boundary and duplicate cases within an explicit finite-domain cap; publish total costs and failed runs.

**Gate:** old v0.1 fixtures plus new versioned 3-input tasks pass; 3-input function behavior is real, not a hardcoded condition in the verifier. Rollback: retain v0.1 dispatch until versioned migration proven.

### Task M3: Semantic world generator and admission

**Proposed files:** `cin/math_worlds.py` *only if* `cin/worlds.py` gets a second distinct responsibility; `tests/test_math_world_evolution.py`. **Interfaces:** `propose_worlds(parent_spec, registry, limit)` produces typed declarative worlds; independent `admit_world` receives the proposal; new family counting uses relation semantics.

- [ ] RED: same MAX2 relation across numeric bounds is NOT new family; impossible, nonunique, vacuous and reference-code-injected specs are rejected/unknown; unknown admission leaves population unchanged.
- [ ] Implement finite declarative transformations and verifier-private uniqueness checks; clear cost accounting.
- [ ] Show >=3 admitted semantically distinct relations and unchanged baseline. Do not use an organism solution to define a success target retroactively.

**Gate:** new families and valid failed/unknown accounting. Rollback: freeze generator, preserve accepted immutable specs.

### Task M4: Independent inheritance and reproducible populations

**Proposed files:** add `cin/scheduler.py`/`cin/governor.py`/transactional store only once true multi-generation needs demonstrated; tests under `tests/test_math_lineage.py` and `tests/test_checkpoint.py`.

- [ ] RED: crash/resume exact budgets, double birth, tampered parent hash, missing macro dependency, expired organism and missing certificate all fail safely.
- [ ] Add proof-backed typed macro extraction with dependency-closure replay and cost accounting, then persistent multi-epoch scheduling. Keep genome five genes.
- [ ] Demonstrate same macro in **two distinct tasks** and measure gains/losses against macro-off baseline including discovery cost; do not call same-task domain widening transfer.

**Gate:** correct 3+ generation ancestry, deterministic recovery, verified reuse and complete budget ledger.

### Task M5: Independent proof scope adapter (conditional)

**Proposed files:** an optional verifier-only adapter and differential tests. Choose and pin current cvc5 base API only after checking actual source/version; do not assume Pythonic API supports SyGuS.

- [ ] RED: finite `PASS` is not labeled universal; solver `unknown`/timeout/unsupported theory fail closed; a false inequality gets counterexample; no solver witness reaches a candidate/offspring.
- [ ] Implement bounded theory translation with audit of each IR operator; check finite-domain agreement on overlapping tasks.
- [ ] Record solver version/time and proof scope; keep finite verifier a valid no-solver default.

**Gate:** counterexample correctness and explicit proof tags; no unverified universal claim.

### Task M6: Iterative mathematical algorithms (conditional research)

**Prerequisite:** M2-M5 complete, separate sandbox/termination review. **Proposed:** versioned `Mod`, guarded division, typed bounded `While`/recursion, later tuple state. Never add a built-in target algorithm.

- [ ] RED: division by zero, step exhaustion, loop nontermination, overflow, invalid state, negative input, `gcd(0,0)`, and Bézout invalid coefficients.
- [ ] Introduce guarded finite-state semantics with separate termination obligation and resource governor. Use exact versioned interpreter/checker rules.
- [ ] Attempt GCD from original/macro seed with verified finite scope and baseline comparisons. Only then try extended GCD in a different PR.

**Gate:** GCD program actually generated by organism search, not copied/admitted by oracle, correct under declared scope and resource limits. A failed attempt is an acceptable report.

### Task M7: Preregistered ablation study

**Proposed files:** study manifest/schema, frozen research script and reports, plus tests for leaked holdouts/version mismatch/unequal accounting.

- [ ] Freeze R0-R5 design, grammar, budget, task split and seed list before test. A pilot sample is *not* confirmatory evidence.
- [ ] Execute matched controls; include every rejected/unknown candidate, invalid world, solver time, macro mining and retries.
- [ ] Report primary and secondary outcomes with uncertainty, all failed cohorts and exact domain/theory proof claims; preserve raw evidence.

**Gate:** reliable reproduction and measured advantage or negative result. Do not claim general intelligence from one success.

## Handoff and review

For each phase, require a small PR, summary of actual changed files, negative and positive tests, reproducible commands, verified baseline preservation, scientific claim bounds, threat boundaries and follow-up decision. Peer review should explicitly challenge proof scope, oracle leakage, complexity theater, test integrity and needless dependencies. Do not merge or write to `main` merely because tests are green.
