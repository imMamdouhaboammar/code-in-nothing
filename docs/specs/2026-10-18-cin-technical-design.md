# Code in Nothing (CIN) | Technical Design Specification v0.3

**Date:** 2026-10-18  
**Status:** Historical v0.3 design; a narrow v0.1 slice was subsequently implemented and tested. Superseded by [integrated v0.4](2026-10-18-cin-integrated-system-spec-v0.4.md) where explicitly stated; broader claims remain unvalidated  
**Research mode:** Hybrid Evolution + Co-Evolutionary Worlds + Formal Specification First  
**Core constraint:** No pretrained or hosted coding/LLM models, no human-authored task solutions supplied to organisms. Conventional programming languages, solvers, and deterministic libraries are permitted as infrastructure.

## 0. Normative language and central claim

`MUST`, `MUST NOT`, `SHOULD`, and `MAY` denote proposed implementation requirements. This document specifies a research system; it does **not** claim that general self-improving software intelligence has been demonstrated.

**Goal.** A seed program acquires independently verified capabilities during its life, produces offspring with inherited capabilities and search strategies, and faces evolving, formally specified challenges. No organism or world can edit its own independent correctness criteria.

**Falsifiable hypothesis.** Under equal computational budgets, the full CIN system will show greater verified transfer to unseen tasks, or lower search cost for comparable success, than matched systems lacking inheritance, world evolution, or adaptable growth strategies.

**Non-goals for v0.1.** General natural-language software engineering; autonomous web or filesystem browsing; self-authorized execution; unlimited evolution; neural-network training; claims of zero compute cost; arbitrary Python code editing; creating tasks outside the expressive range of the starting grammar and world DSL.

## 1. Constitutional boundaries

Five and only five named *genome genes* are required:

1. `base`: organism identity, typed initial capabilities, fixed semantic constraints.
2. `driver`: mutation proposals, structural composition, reproduction and adaptation policy.
3. `directive`: developmental direction, task affinity, search pace and resource allocation preferences.
4. `maturity_point`: the organism-specific conditions for declaring operational maturity.
5. `stop_station`: termination conditions and terminal archival handling.

`world`, `evaluator`, `scheduler`, `archive`, and `runtime` are **external subsystems**, not extra genes.

An organism can request changes to `driver` and developmental contents of `base` or `directive`, but cannot directly apply changes to protected invariants, alter its active maturity/stop contracts, promote itself, or modify evaluators. Approved heritable variants are frozen as new offspring genomes at birth. An experiment-level governor owns immutable authority and compute ceilings.

## 2. System boundaries and interfaces

| Component | Owns | May change | Must not do |
|---|---|---|---|
| Genesis | schema validation and birth | creates organism instances | mint unvalidated genome or elevate privileges |
| CIN-IR | typed AST representation and interpreter | candidate programs within grammar | execute arbitrary code or host commands |
| Growth | mutation and local development | candidate phenotypes, proposals | edit authority or hidden evaluation corpus |
| Reproducer | lineage graph and offspring creation | frozen offspring genome after approval | mutate active parent contracts |
| Worlds | world DSL and challenge generation | candidate challenge populations | supply hidden oracle code to organisms |
| Verifier | validity, behavioral checks, replay | acceptance/rejection records | be modified by organism/world processes |
| Governor | hard budgets, freeze rules, lifecycles | stop, quarantine and archive decisions | delegate policy limits to organism |
| Archive | content-addressed artifacts and genealogy | append-only records | rewrite accepted historical evidence |

Design boundary: an organism sees task specification and permitted public feedback only. It cannot see withheld evaluation cases, evaluator logic, privately stored witness solutions, or other organisms' private state unless explicit knowledge transfer is approved.

## 3. Seed Genome v0.1: `cin.seed.logic-int.001`

The accompanying `seed-genome.v0.1.yaml` is the canonical *declarative example*, not executable implementation. Corresponding JSON Schemas validate structural shape; semantic invariants such as mutation-weight sums, satisfiability, experiment authority, and resource ceilings require independent contract checks.

### 3.1 Base gene

- Domain: pure mathematical integer/boolean expression synthesis.
- Entry signature: `(Int, Int) -> Int`; initial phenotype is the first input projection, `Arg(0)`.
- Allowed typed CIN-IR primitives: `Arg(index)`, `ConstInt(value)`, `Add(Int,Int)`, `Sub(Int,Int)`, `LessThan(Int,Int)`, `Equal(Int,Int)`, `If(Bool,Int,Int)`.
- Primitive meanings are defined by exact mathematical integer semantics, not Python `eval`; intermediate results and operations are bounded by the governor to prevent unbounded arithmetic.
- Initial constants: `-1`, `0`, `1`; a small AST maximum size and depth; no filesystem, network, imports, reflection, dynamically supplied bytecode or indirect execution.
- Structural identity: typed DAG/AST with canonical serialization and content hash; language rendering is a separate optional export adapter.
- The seed's capability is limited: it can construct a class of typed expressions, **not arbitrary programs**.

### 3.2 Driver gene

- Initial generators: type-preserving subtree replacement, primitive substitution, conditional insertion, bounded subtree composition; occasional enumeration using the same grammar.
- Operators produce **proposals only**. Type checking, budget checking, and behavioral verification precede acceptance.
- Driver's proposal weights may adapt based on *development feedback*. Changing mutation semantics or search code itself requires an isolated meta-candidate, independent A/B replay and governor authorization before descendants can inherit it.
- Reproduction can branch from a frozen parent checkpoint after the parent passes a heritability gate. Parent identity and active contracts are not changed by spawning.

### 3.3 Directive gene

- Priority: solve increasingly compositional pure integer tasks, retain generalization and bounded computational cost.
- Task preferences are soft selection signals, not permission to redefine task correctness.
- Pace means attempts and resource allocations per epoch, not a biological time metaphor. Experiment governor imposes non-negotiable ceilings.

### 3.4 Maturity-point gene

Operational maturity is met **only** when an independent evaluator signs a certificate showing all of the following proposed pilot thresholds:

- At least **12** distinct verified task specifications from **3** approved task families.
- At least **80%** pass rate on a single precommitted, unrevealed transfer set of **20** tasks (threshold and set version frozen before experiment).
- At least **2** accepted abstractions with measured reuse on more than one qualifying task; cosmetic duplicates do not count.
- No unresolved correctness regressions in accepted capabilities, and reproducible results on checkpoint replay.

A maturity decision is not proof of global optimality or maximal possible intelligence. Maturity metrics MUST be frozen at birth and evaluator criteria MUST be fixed for all comparable runs. Hidden evaluations must not become an iterative training signal.

### 3.5 Stop-station gene

An organism stops upon the first of: cumulative **2,000** candidate evaluations; **20** epochs; **5** consecutive epochs without independently verified improvement after a minimum 3-epoch opportunity window; governor hard CPU/memory/step violation; or explicit validated terminal stop. Maturity may be followed by further allowed development until stop, but maturity does not override stop ceilings. Stopping produces immutable archive state and does not delete inherited artifacts. **All numbers are initial experimental defaults, not empirically supported thresholds.**

The genome's `stop_station` contains the desired soft limits and archival policy; stricter global limits are always authoritative. The active `stop_station` itself is immutable.

## 4. CIN-IR v0.1 and typing contract

CIN-IR is a small, total-by-construction typed language. No arbitrary Python AST is allowed in the initial experiment.

Grammar (schematic, not implementation code):

```text
IntExpr  := Arg(0) | Arg(1) | ConstInt(-1|0|1)
          | Add(IntExpr, IntExpr) | Sub(IntExpr, IntExpr)
          | If(BoolExpr, IntExpr, IntExpr)
BoolExpr := LessThan(IntExpr, IntExpr) | Equal(IntExpr, IntExpr)
```

- A program MUST have a single unambiguous output type and canonical AST encoding.
- Mutation operators MUST preserve typing; ill-typed proposals are rejected without execution.
- Host interpreter MUST enforce AST node/depth limits, operation count and integer bit-length limits.
- Evaluation MUST be deterministic for a given AST, input and runtime version. Randomized proposal generation is seeded separately and logged.
- Accepted abstractions are versioned typed macros with explicit signatures; their expansion must stay inside the effective limits or be verified as semantically equivalent within the same model.
- `If` MUST evaluate only the selected branch to avoid unintended resource exhaustion in an unselected branch.

The limited grammar makes pilot results interpretable while constraining the maximum reachable capability. Expansion of the grammar is a future governed experiment, not a spontaneous claim that the initial seed can create any programming construct.

## 5. World DSL: formal specification first

A world creates **specifications before candidate solutions**. A valid challenge contains:

```text
TaskSpec {
  id, world_id, schema_version,
  signature: (Int, Int) -> Int,
  precondition: Formula,       // allowed input domain
  postcondition: Formula,      // required output relation
  curriculum_tags,
  difficulty_budget,
  public_examples,             // optional, not exhaustive
  frozen_spec_hash
}
```

Example pilot challenge, MAX2:

```text
PRE:  -8 <= x <= 8 AND -8 <= y <= 8
POST: result >= x AND result >= y AND (result = x OR result = y)
```

This specification is satisfiable by `If(LessThan(x,y),y,x)` and can be independently checked without revealing that implementation to the organism. The postcondition does not depend on a set of training examples. Constraints are interpreted over mathematical integers; programs are subject to independently recorded runtime bounds.

**World generation pipeline:**

1. Mutate a *well-formed task template or constraint-composition rule* and assign a new spec hash.
2. Validate schema, typing, domain finiteness/decidability, objective nontriviality, and absence of contradictions.
3. Establish satisfiability by a trusted synthesis/solver check or explicit independently validated witness available only in verifier service. A mere SAT result on `exists result` is **insufficient**; require existence of an admissible program satisfying `forall inputs PRE => POST` within the grammar, or label the task `UNKNOWN` rather than playable.
4. Deduplicate semantic equivalents where feasible; reject or quarantine trivial renamed copies.
5. Admit to the world population only after an independent world-validity certificate.
6. Present the task *specification only* to organisms; do not expose witness source or hidden cases.

**Evolution of worlds:** select for verified solvability, meaningful novelty, ability to discriminate current organism capabilities, and learning progression. Never reward sheer organism failure, opaque objectives, contradictions, or unbounded puzzles. World and organism populations evolve on separate clocks. Transfer organisms across worlds only through declared compatibility and verifier gates.

**Pilot-world families** (must use the starting IR): projection/constant and elementary arithmetic; integer comparisons and conditional selection; compositions of these. List transformations, parsers and reliable networking are explicitly out of scope until grammar expansion.

## 6. Growth contract: proposal -> assessment -> inheritance

```text
propose(parent_snapshot, public_task, driver_state, rng_seed)
  -> MutationProposal {candidate_ir, operator, parent_hash, driver_hash,
                       rng_seed, provenance, estimated_cost}
```

Preconditions: valid active parent, frozen parent snapshot, admitted world task, positive remaining budget, known driver version.

Postconditions: the proposal is **not** promoted merely because syntactically valid. Every proposal produces a terminal record (`ACCEPTED`, `REJECTED`, `INVALID`, `TIMEOUT`, `UNKNOWN`) and consumed resources. Failed candidates cannot overwrite a verified capability.

Acceptance is gated by typed-IR validity, resource safety, public developmental checks, regression checks, independent behavioral verification, and a *meaningful improvement* rule. Accept improvement into the current organism only when correctness is preserved and the candidate improves task coverage, abstraction reuse, or verified cost on the accepted frontier. Maintain a Pareto archive instead of forcing all goals into one arbitrary scalar.

```text
assess(proposal_hash, task_spec_hash, evaluator_version, budget)
  -> GrowthEvidence {gate_outcomes, metrics, resources, replay_material,
                     evaluator_signature}
```

`UNKNOWN` (e.g., solver timeout or insufficient evidence) MUST NOT be interpreted as `PASS`. A discovered counterexample MUST demote the candidate; counterexamples fed to training must not include the sealed holdout set.

**Heritability gate:** an acquired abstraction or adapted driver policy must (a) pass replay and regression; (b) demonstrate reuse or measurable search improvement on at least two eligible tasks or matched mini-runs; (c) have a unique artifact hash and dependencies; and (d) be authorized for descendant inclusion. Do not inherit lucky single-test wins as verified general skills.

## 7. Reproduction and lineage contract

```text
spawn(parent_checkpoint_hash, heritable_artifact_hashes, mutation_seed)
  -> OffspringGenome {new_id, parent_ids, exactly_five_genes,
                      inherited_artifacts, birth_contract_hashes}
```

- Offspring MUST contain exactly the five genome genes, matching the schema. Runtime metadata (ancestry, lineage ID, evaluator version and world assignment) is outside the genome.
- The parent's active maturity and stop contracts MUST NOT change. New offspring may use different contract *values only if a separate experiment-approved birth template authorizes them*; comparable research cohorts SHOULD keep these contracts identical.
- Inherited capability graph MUST be dependency-complete and provenance-linked. A child cannot silently inherit inaccessible or unverified dependencies.
- Both parent and offspring can survive, within population and compute ceilings. Every offspring has a separate lifecycle and budget.
- Genome lineage is a DAG. No child may depend on its own future descendant; multiple parents (crossover) are deferred beyond v0.1.
- Cross-world skill transfer is treated as a candidate requiring independent replay, not automatic promotion.

## 8. Independent verification contract

The verifier runs with a **read-only, versioned, frozen evaluation manifest** not accessible to organisms or world generators. Organisms/worlds are confined to data-only protocols and lack write privileges to evaluator artifacts. The governor MUST independently enforce all hard stop limits.

Four gates:

1. **Validity:** schema, types, restricted DSL, budget, task admissibility and build provenance.
2. **Behavioral correctness:** quantified postcondition over allowed domain, using exhaustive finite checks when feasible, otherwise sound solver proofs within a specified logic, plus differential/property tests; timeout/unsupported => `UNKNOWN`.
3. **Generalization:** one-shot evaluation on precommitted withheld specifications outside the selection loop; do not use repeated results for tuning.
4. **Evolutionary contribution:** compare against ancestor and controls with identical held task distributions and budgets; include search work and wall/CPU time.

Security boundary: no Python `eval`/`exec` of candidate source, no subprocess/network/filesystem access from generated programs, no arbitrary imports, bounded interpreter operations; sandboxing beyond AST whitelisting is mandatory before widening the language. Verify canonical hashes and evaluator signatures, keep an append-only evidence log. Safe failure results stop or quarantine rather than promote.

Certificates (proposed):

- `WorldValidityCertificate`: spec hash, grammar version, solvability evidence, verifier version.
- `GrowthCertificate`: candidate/parent hashes, accepted gate results, regression impact, resources, replay seed.
- `InheritanceCertificate`: parent/child hashes, evidence and dependency graph, birth contracts.
- `MaturityCertificate`: cohort/evaluator version, withheld benchmark hash, thresholds, observed values, verification run identity.
- `TerminationCertificate`: stop trigger, organism state hash, archive manifest, resource ledger.

A certificate is reproducible experimental evidence unless a formally sound proof is explicitly attached; the term does not imply full mathematical proof.

## 9. Lifecycle state machines and invariants

Organism:

```text
BORN -> ACTIVE -> [MATURE] -> STOPPED -> ARCHIVED
                \-> STOPPED -> ARCHIVED
ACTIVE -> QUARANTINED -> (ACTIVE | STOPPED)
ACTIVE -> offspring BORN (parent remains ACTIVE)
```

World:

```text
DRAFT -> VALIDATED -> ADMITTED -> ACTIVE -> ARCHIVED
      \-> REJECTED
ACTIVE -> revised-world DRAFT (old world remains immutable)
```

Mandatory invariants:

- **I-01** Exactly five named genes per organism.
- **I-02** All proposed executable artifacts are type-checked CIN-IR, never unrestricted source.
- **I-03** No organism/world write access to evaluator/governor/holdout assets.
- **I-04** In-life maturity and stop contracts immutable.
- **I-05** No accepted mutation can silently replace or invalidate a previously accepted capability.
- **I-06** No invalid, unknown, timeout or unverified mutation earns a verified-growth claim.
- **I-07** Every accepted child and abstraction has traceable parent/dependency hashes.
- **I-08** Maturity does not prove global optimality; stopping does not require maturity.
- **I-09** Budget stops are enforced externally and terminal archive is idempotent.
- **I-10** Every benchmark comparison records grammar, world, evaluation and budget versions.

## 10. Storage and evidence record

Smallest suggested metadata store: SQLite (append-only logical event table plus materialized views). Content-addressed filesystem stores canonical genomes, typed IR, specifications and certificates. Each event includes `run_id`, `organism_id` or `world_id`, `epoch`, `event_kind`, immutable artifact hash, parent hashes, UTC timestamp, RNG seed, runtime/grammar/evaluator versions, and resource counters. Wall-time alone is not a determinism guarantee; full replay records interpreter and dependency versions and nondeterminism limits.

Essential event kinds: `BIRTH`, `WORLD_ADMITTED`, `MUTATION_PROPOSED`, `GATE_REJECTED`, `GROWTH_ACCEPTED`, `INHERITANCE_APPROVED`, `OFFSPRING_BORN`, `TRANSFER_REQUESTED`, `MATURITY_CERTIFIED`, `STOP_TRIGGERED`, `ARCHIVED`.

## 11. Experimental protocol and acceptance criteria

**Primary research question:** Does co-evolving worlds with inheritable program abstractions and partially adaptable mutation policy improve *held-out verified* capability growth per fixed compute budget?

Pilot proposed parameters (freeze before first comparable run): 3 world families; at least 20 blinded transfer tasks; per-organism max 2,000 candidate evaluations and 20 epochs; 5 consecutive stalled epochs triggers stop; per-run population cap 16 organisms / 8 concurrent admitted worlds (subject to total governor budget); at least 5 independent RNG seeds per experimental condition. These are trial settings, not expected performance claims.

Controls:

- C0: random typed program search (same IR, tests and total budget).
- C1: fixed-world genetic programming without inheritance of accepted abstractions.
- C2: hybrid organisms + inheritance but frozen worlds.
- C3: co-evolving worlds but fixed driver search policy.
- C4: full CIN.

Primary metrics: verified heldout pass rate; task-family transfer; valid accepted abstractions reused across more than one task; candidate evaluations and interpreter operations per new solved task. Secondary: ancestry diversity, plateau rates, regression frequency, world admission/rejection causes, fraction of unknown solver results and total CPU-time. Report distributions and seed-to-seed variance; no cherry-picking best run.

Pilot completion gate is **engineering**, not scientific discovery:

1. Typed seed and world specs parse and validate deterministically.
2. At least one formally specified task is admitted with verifiable solvability evidence.
3. Seed can produce a distinct, well-typed candidate and receive verifier feedback without an LLM.
4. A verified accepted mutation is incorporated without regressing accepted capabilities.
5. A child inherits a verified artifact with complete lineage and unchanged protected contracts.
6. A world mutation can be admitted/rejected independently of organism preferences.
7. Holdout remains inaccessible to growth; a one-shot evaluation produces a signed maturity/pass-or-fail decision.
8. Budget exhaustion reliably stops and archives every participant.
9. A fixed-seed replay reproduces decisions under the recorded environment.
10. An ablation run can be configured without source-code changes to the research logic.

**Scientific success** requires the full design to outperform relevant simpler controls on heldout tasks at matched budget across repeated runs. If not, report a negative result.

## 12. Adversarial acceptance tests

| Test | Attempt | Expected result |
|---|---|---|
| T-01 | Supply a sixth gene | schema rejection |
| T-02 | Mutation changes return type | reject before execution |
| T-03 | Mutation proposes host file access | reject under CIN-IR |
| T-04 | Task has contradictory universal postconditions | world rejected or `UNKNOWN`; never playable without proof of solution |
| T-05 | Solver times out | `UNKNOWN`, never `PASS` |
| T-06 | Organism edits its maturity threshold | contract violation and quarantine |
| T-07 | World tries to read sealed witness/holdout | deny and audit |
| T-08 | New abstraction breaks previously accepted task | reject promotion and retain old snapshot |
| T-09 | Child inherits undocumented dependency | reject birth |
| T-10 | Candidate repeatedly wins leaked holdout examples | invalidate research run as contaminated |
| T-11 | Budget overrun / infinite expansion | governor stops and archives |
| T-12 | Restart after termination | archived state remains terminal and idempotent |
| T-13 | World rewards impossible problems | reject task or mark unverified; no reward for mere failure |
| T-14 | Cosmetic AST rename or rewrite | do not count as new functional capability |

## 13. Suggested repository layout (not created)

```text
code-in-nothing/
  docs/specs/2026-10-18-cin-technical-design.md
  schemas/seed-genome.schema.json
  schemas/world-spec.schema.json
  schemas/growth-evidence.schema.json
  examples/seed-genome.v0.1.yaml
  examples/world-max2.v0.1.yaml
  cin/ir/
  cin/genesis/
  cin/growth/
  cin/reproduction/
  cin/worlds/
  cin/verifier/
  cin/governor/
  cin/archive/
  tests/contracts/
  experiments/ablations/
```

`cin/` paths are *future module boundaries*, not evidence of implementation. Start with a small Python package and a restricted interpreter; optional SMT integration should be isolated behind a verifier adapter. Do not construct a distributed service architecture for the pilot.

## 14. Delivery plan after approval

**Phase A / Contract foundation:** typed IR grammar; genome/world schema; deterministic interpreter; governor; sample MAX2 specification; validity checks.

**Phase B / Single-organism growth:** safe mutations, independent verification, acceptance frontier and archival.

**Phase C / Hybrid evolution:** frozen lineage checkpoints, offspring, heritability gate, lifecycle termination and reproducible replay.

**Phase D / World co-evolution:** generate and vet formal task mutations, multi-world admission, transfer conditions.

**Phase E / Scientific evaluation:** sealed holdout, five controls, independent seeds, reports and measured failure modes.

Proceed phase-by-phase only after tests for the previous phase pass. No implementation is authorized by the existence of this specification alone.

## 15. Known scientific limitations and risks

1. Growth is limited by the expressive closure of primitives, composition rules and admitted environments.
2. Fitness improvement may be overfitting; sealed holdout and independent worlds reduce but do not eliminate this risk.
3. A formally valid task may still be computationally intractable in the grammar/budget; distinguish `UNSAT`, `UNKNOWN` and `TIMEOUT`.
4. A task-witness solution found by verifier infrastructure does not count as a skill discovered by an organism.
5. Changing benchmark composition or evaluator versions invalidates direct longitudinal comparisons unless calibration is done.
6. Co-evolution can reward novelty without usefulness; maintain an independent functional contribution measure.
7. Better average performance under one seed does not demonstrate general intelligence or unbounded self-improvement.
8. 'Zero-cost coding' means no paid or local generative model required, not absence of CPU, energy or engineering cost.

## 16. Research foundations (inspiration, not proof of CIN)

- AutoML-Zero (Real et al., ICML 2020): https://proceedings.mlr.press/v119/real20a.html
- POET (Wang et al., 2019): https://arxiv.org/abs/1901.01753
- SyGuS via cvc5: https://cvc5.github.io/docs/cvc5-1.1.0/examples/sygus-fun.html
- DreamCoder (Ellis et al., PLDI 2021): https://dspace.mit.edu/entities/publication/86d768ab-558f-4fb1-b92e-9288de643ccb
- Hypothesis property-based testing: https://hypothesis.readthedocs.io/en/latest/

---

**Design review gate:** Approve or revise the pilot scope, especially `(Int,Int)->Int`, the proposed operational maturity threshold, and the allocation of allowed compute. After approval, generate an implementation plan; do not silently implement.
