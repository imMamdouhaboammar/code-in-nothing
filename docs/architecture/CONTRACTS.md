# CIN contracts, data, and compatibility

**Authority:** Existing signatures below are observed in v0.1. Proposed ports are **not** shipped APIs. [Integrated specification](../specs/2026-10-18-cin-integrated-system-spec-v0.4.md).

## 1. Shipping schemas and actual code

| Object | Existing source | Version | Key constraints |
| --- | --- | --- | --- |
| Seed Genome | `schemas/seed-genome.v0.1.schema.json`, `cin/contracts.py` | `cin.genome/v0.1` | Five exact genes, weighted driver spec, typed starting IR, valid stop bounds |
| World | `schemas/world-spec.v0.1.schema.json`, `cin/contracts.py` | `cin.world/v0.1` | Finite two-integer domain, independent precondition, result-related postcondition |
| Growth evidence | `schemas/growth-evidence.v0.1.schema.json` | `cin.evidence/v0.1` | Proposal/candidate/spec hashes, verifier version, per-gate outcome, resources, replay metadata |
| Typed IR | `cin/ir.py` | implicit v0.1 | Closed `Arg`, `ConstInt`, `Add`, `Sub`, `LessThan`, `Equal`, `If` typed expression set |

`cin/contracts.py` uses `jsonschema.Draft202012Validator.iter_errors` and semantic follow-up checks. The underlying package supports schema meta-validation using `Draft202012Validator.check_schema`; adding meta-validation to a future schema migration is recommended but not a claim of current behavior.

Actual callable interfaces (Python):

```python
load_genome(path: str | Path) -> dict
load_world(path: str | Path) -> dict
validate_genome(genome: dict) -> dict
validate_world(world: dict) -> dict
check_tree(node: dict, base: dict) -> str
run_ir(node: dict, x: int, y: int, limits: Limits = Limits(), ops_counter: list[int] | None = None) -> int
render_python(node: dict, base: dict) -> str
verify_program(program: dict, world: dict, base: dict, limits: Limits = Limits(), max_cases: int = 4096) -> Verdict
admit_world(world: dict, base: dict, max_proposals: int = 1000, max_cases: int = 4096) -> Admission
expand_domain(world: dict, delta: int = 1) -> dict
spawn_verified(parent: dict, artifact: dict, certificates: list[dict], child_id: str, worlds: list[dict] | None = None) -> dict
Experiment(...).run() -> dict
Archive.append(kind: str, payload: dict) -> str
Archive.terminal_archive(organism_id: str, summary: dict) -> str | None
Archive.verify_chain(path: str | Path) -> bool
```

Return values are currently dictionaries/dataclasses, not a stable public REST/API schema. CLI exposed today: `python -m cin validate` and `python -m cin demo --seed INT --max-evals INT --output DIR [--no-world-evolution] [--no-inheritance]`. Invalid input and pre-existing output location exit nonzero. `python -m cin demo` does not spawn a long-running daemon.

## 2. Current verification semantics

`Verdict(status, checked, counterexample, reason, operations)` returns `PASS` only after enumerating admitted precondition-satisfying domain points (unless limits fail). `FAIL` includes the first counterexample; `INVALID` covers invalid worlds/AST and empty preconditions; `UNKNOWN` includes interpreter budget overrun. `Admission(status, spec_hash, witness_hash, reason, candidates_checked)` returns `ADMITTED`, `REJECTED` or `UNKNOWN`. An `ADMITTED` witness hash does **not** expose its implementation to the organism.

Current world precondition/postcondition grammar is a closed boolean DSL (`and`, `or`, `gte`, `lte`, `eq`) over integer `x`, `y`, and `result`; precondition cannot contain `result`, postcondition must mention it. This basic check is not a mathematical proof that `result` is uniquely constrained. Future stronger semantics must be versioned and tested.

`spawn_verified` currently requires a program in the parent's skills and PASS certificate records for two distinct `world_hash` values, plus the actual two worlds so it can independently re-admit and replay. Both worlds can be the *same function on distinct domains*: therefore the existing gate proves replay at two specifications, **not** cross-task abstraction transfer.

## 3. Target contracts and status taxonomy (not implemented)

Future boundary payloads should be immutable, schema-versioned JSON documents. IDs label entities; hashes bind artifact content.

| Contract | Core fields | Producer | Independent consumer |
| --- | --- | --- | --- |
| `WorldProposal/v1` | `world_id`, `parent_hash`, `typed_spec`, `family`, `generation_operator`, `budget` | World generator | World admission |
| `AdmissionCertificate/v1` | `spec_hash`, `status`, `scope`, `witness_hash`, `verifier_version`, `cost`, `reason` | Verifier | Scheduler and archive |
| `Candidate/v1` | `program_hash`, `parent_hash`, `organism_id`, `operator`, `ir_version` | Growth | Verifier |
| `GrowthDecision/v1` | `candidate_hash`, `semantic_task_id`, `verdict_ref`, `regression_refs`, `resource_ref`, `status` | Promotion authority | Organism state machine |
| `InheritanceBundle/v1` | `parent_ids`, `skill_refs`, `dependency_closure`, `proof_refs`, `genome_hash` | Reproduction gate | Genesis |
| `MaturityDecision/v1` | `cohort_id`, `organism_id`, `policy_hash`, `holdout_manifest_hash`, `metric_summary`, `status` | Sealed evaluator | Controller/archive |
| `StopDecision/v1` | `entity_id`, `entity_kind`, `stop_policy_hash`, `reason`, `budget_snapshot` | Governor/lifecycle | Archive |

Proposed `UNKNOWN` is reserved for exhausted or inconclusive verification, distinct from `FAIL` with counterexample, and from `INVALID` for malformed policy/spec/data. Authentication is not implied by a `verifier_signature` field when it stores only a digest. Do not treat a self-computed SHA-256 as nonrepudiation.

## 4. Resource accounting contract

Define `Budget` by a pinned immutable upper-bound manifest. Required meters: proposal count, verified candidate interpreter operations, world admission witness candidate count and operation count, finite-domain points, wall/CPU time diagnostics, and governor termination reason. Record *all* search attempts, including `UNKNOWN`, failed admission, regressions and duplicated programs. Resource ceilings are owned by governor, not programmable `directive` alone.

Do not compare experiments solely by `max_evals`: two proposals can have very different AST size and cost, and world witness search is currently excluded from `candidate_evaluations` in the v0.1 report. Future comparisons must account for it.

## 5. Protocol upgrade rules

1. Freeze schema/IR/verifier/grammar versions in the cohort manifest.
2. Add a new contract version for any semantic change (especially new ops/types, world formula operators or maturity definitions).
3. Migrations are explicit and preserve the original artifact and hash; do not rewrite archived proofs in place.
4. All older `PASS` records retain their *old* finite-domain scope, even if newer solvers prove wider assertions.
5. Before reading untrusted persisted data into a trusted worker, validate schema and semantic constraints; reject unknown discriminators.
6. On any unexpected input/output shape, fail closed with a typed error and preserve evidence. Never silently convert unknown statuses to PASS.
7. External signature schemes, content storage and OS isolation require separate design decisions and validation.

## 6. Positive/negative test minimums

- Preserve `tests/test_contracts.py`, `tests/test_ir.py`, `tests/test_worlds.py`, `tests/test_evolution.py`, `tests/test_search.py`, `tests/test_cli.py`.
- Reject sixth gene, invalid node, disallowed primitive, unbounded input, empty world, self-referential precondition and missing-result postcondition.
- Reject forged inheritance certificate, mismatched content digest, world ID collision, duplicate terminal event and evaluator budget overflow.
- In later phases reject semantic world duplicates, policy updates without replay, holdout leaks, late events after stop, resume divergence and partial commit replays.

No data-plane change is justified solely to make documentation examples prettier.
