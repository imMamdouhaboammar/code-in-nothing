# Code in Nothing: Integrated System Specification v0.4

**Status:** Accepted research direction and proposed implementation contracts. **Not** a claim that v0.4 is implemented.  
**Date:** 2026-10-18  
**Baseline runtime:** CIN-Lab v0.1 (`cin/`); [pilot outcomes](../../experiments/RESULTS.md).  
**Audience:** research engineers, formal-methods reviewers, maintainers and autonomous coding agents.  
**Canonical vocabulary:** [CONTEXT.md](../../CONTEXT.md).  
**Review/implementation order:** [Roadmap](../roadmap/PHASES.md) and [phase plan](../plans/2026-10-18-cin-next-phases.md).

## 1. Mission and falsifiable scope

Code in Nothing (CIN) investigates whether small, model-free software organisms can acquire new **verified** capabilities during their lifetimes, transmit proven capabilities to offspring, and improve future discovery efficiency under independently governed, co-evolving formal challenge worlds. It does not claim that arbitrary code can arise without computational cost, a search grammar, information, or a measurable objective.

**Research hypothesis H1:** With an identical total candidate/interpreter-operation budget, a hybrid inherited-capability system with independently admitted changing task families achieves better withheld-task transfer or lower cost per newly solved functional task than suitable non-inheritance and fixed-world controls.

**Research hypothesis H2:** A separately validated mutation-policy adaptation improves out-of-sample search efficiency relative to fixed-policy search, with no regressions on retained capabilities and no verifier leakage.

**Research hypothesis H3:** Worlds that evolve semantic challenge structure produce broader verified functional coverage than domain-range expansion alone. Failure of any hypothesis is an acceptable research result.

### Goals

- Exactly five seed genes, with growing phenotypes and traceable ancestry.
- Explicit birth, growth, reproduction, plateau, maturity, stop and archive states.
- Two genuinely independent evolutionary actors: organisms and worlds.
- Formal-specification-first evaluation with a verifier neither actor may rewrite.
- Model-free candidate generation and bounded resource use; no external or pretrained coding model dependency.
- Reproducible, preregistered tests distinguishing functionality, diversity, transfer and search cost.
- An auditable, minimally complex research runtime before any distributed product platform.

### Non-goals for next stages

Natural-language autonomous programming; self-selected external goals; unfettered host command execution; human-equivalent cognition; continuous cloud operation; a GUI; automated repository modification; agent login; network tool use; neural-network training; unconditional performance gains; zero total compute cost. These require separate approvals, threat models and evidence.

## 2. Existing implementation vs future design

| Capability | CIN-Lab v0.1 observed/source | v0.4 target |
| --- | --- | --- |
| Five exact genes | Implemented schema and tests | Preserve invariant through schema migrations |
| Typed source grammar | `cin/ir.py`, fixed `Int` and `Bool` trees | Versioned type system and semantics, expand only with evidence |
| Program proposals | `cin/search.py`, deterministic bounded enumeration/variation | Explicit operator policies and stochastic reproducible population scheduling |
| Formal verification | Exhaustive declared finite `x,y` domains | Proof-scope-tagged finite and optional SMT-backed checking |
| World admission | Bounded private witness search in `cin/worlds.py` | Multiple admissibility checks, family-level semantic novelty, independent oracle |
| World evolution | Expand same MAX2 domain only | Admitted transformations to new function families |
| Hereditary capability | One child after replay on two world specs of same function | Inheritance tested for cross-task reuse, separate semantics from range checks |
| Multiple generations | Not implemented | Persistent population and world scheduler |
| Driver evolution | Declared in YAML, not operational | Versioned policy proposals, A/B tests, restricted inheritance |
| Maturity evaluation | `NOT_EVALUATED` | Sealed, independent verdict with defined denominator |
| Archive | In-process JSONL SHA-256 chain | Durable artifacts, resume/replay and optional independent anchoring |
| Worker isolation | Data-only IR inside trusted host process | OS-isolated worker for any future richer execution |
| Scientific superiority | Not established | Matched-budget, multi-seed controls with uncertainty |

**Observed pilot:** one MAX2 function accepted after 85 candidate proposals, two admitted variations of the same semantic world, one offspring. None of those facts establishes distinct learned abstractions, different tasks, open-ended evolution or maturity certification. The frozen-world control also finds MAX2 after 85 proposals but creates no child due to the two-spec inheritance rule. This is a *mechanism demonstration*, not a fair scientific comparison.

## 3. Inviolable system laws

| ID | Rule | Enforcement authority |
| --- | --- | --- |
| CIN-I01 | Seed genome has `base`, `driver`, `directive`, `maturity_point`, `stop_station`, exactly. | Schema and genesis |
| CIN-I02 | Organism/world growth cannot change a live evaluator, benchmark, or system governor. | Trusted control plane |
| CIN-I03 | Mutation is merely a proposal until it has independently verified evidence. | Promotion gate |
| CIN-I04 | A program's certificate states domain, semantics, interpreter, grammar and limits. | Verifier |
| CIN-I05 | `UNKNOWN`, timeout, invalid specification and empty precondition never count as a PASS. | Verifier |
| CIN-I06 | Accepted capabilities may not silently regress; replacements must replay all affected contractual tasks. | Promotion gate |
| CIN-I07 | An inherited capability must have a traceable originating artifact, dependency closure and admissible replay. | Reproduction gate |
| CIN-I08 | World novelty is determined from behavioral semantics, not mere change in ID, constants or input range. | World gate |
| CIN-I09 | Holdout tasks and final maturity verdicts are not feedback sources for selection. | Evaluation steward |
| CIN-I10 | A child's new genome retains externally imposed stop and maturity rules, and a parent cannot relax them in situ. | Genesis and reproduction |
| CIN-I11 | Every organism/world has finite budgets and explicit terminal events; no infinite growth guarantee. | Resource governor |
| CIN-I12 | All scientific comparisons count *all* candidate search, admission witness work, verifier operations and failed experiments. | Metrics owner |
| CIN-I13 | No generated source runs with unrestricted host privileges. | Interpreter and isolation gate |
| CIN-I14 | An active experiment keeps pinned program semantics and scoring versions; changes start a new comparable cohort. | Experiment controller |

## 4. Five-gene Seed Genome contract

`api_version: cin.genome/v0.1` remains the shipping schema for the next design stage. The examples in [`examples/seed-genome.v0.1.yaml`](../../examples/seed-genome.v0.1.yaml) and `schemas/` are authoritative for what v0.1 parses **today**. The following semantics extend it without silently changing accepted fields.

| Gene | Canonical role | Evolving parts | Fixed constraints |
| --- | --- | --- | --- |
| `base` | Biological identity analogy; program signature, CIN-IR grammar and starting phenotype | Child birth program/capabilities, approved grammar version at new birth only | Active typing, purity, allowed op set and execution limits |
| `driver` | Propose variations, compose/reuse accepted programs, select proposal distributions | Search heuristics through externally checked policy variants | May not alter verifier, holdout or resource governor |
| `directive` | World focus, exploration/exploitation bias, target rates and quotas | May differ at offspring birth after legitimate search-policy experiments | Per-run ceilings and externally fixed objectives |
| `maturity_point` | Fixed success contract specifying task coverage, families, transfer and reuse | None during organism life; future policy migration only across new cohorts | Evaluation stewardship, evidence and versioning |
| `stop_station` | Finite lifetime ceilings, plateau and terminal archiving | None during organism life; new cohorts may use versioned policy | Hard governor cannot be overridden by organims |

The actual `driver.mutation_operators` and `adaptation` settings are currently declarative: the search algorithm does not execute weighted adaptive operators. They **must not** be described as implemented mutation-policy learning.

Genome ID and lineage ID are distinct. `seed_id` identifies the birth seed artifact; organism identity and parent hashes belong to runtime records, not additional genes. A child may start with an approved inherited phenotype without redefining the external maturity target.

## 5. Two evolving populations and three control authorities

- **Organism population** proposes typed candidate programs, tests provisional capabilities, archives successful artifacts and spawns approved offspring.
- **World population** proposes *formally specified* tasks and transformations, maintains world family diversity and supplies bounded learning challenges.
- **Independent verifier** owns spec validation, solvability/admission, behavior, regression and transfer certification.
- **Research controller** pins cohorts, experimental arms, RNG seeds, budgets, holdout schedules and metric definitions.
- **Resource governor** cancels/caps work and controls worker isolation; not itself under evolution.

The three independent authorities are verifier, controller and governor. They are logically separate responsibilities; v0.1 does **not** isolate them as separate services or processes.

The primary system design is in [architecture/SYSTEM.md](../architecture/SYSTEM.md); the full growth protocol is in [architecture/EVOLUTION.md](../architecture/EVOLUTION.md).

## 6. Formal world design: specification before examples

World evolution always starts with a **machine-checkable intended relation** between inputs and result, never by treating a self-generated solution as unchallengeable ground truth.

A candidate world includes immutable `world_id`, `family_id`, `spec_version`, typed signature, finite input domain or SMT theory, precondition, postcondition, generator ancestry, verifier metadata and admission budget. A proposed world is not admitted until it passes:

1. **Syntactic and semantic validity:** recognized types/operators; well-formed, non-vacuous precondition; result materially constrained; finite or solver-declared domain.
2. **Independent witness:** valid reference implementation/witness proven or exhaustively checked within admitted scope; a search miss is `UNKNOWN`.
3. **Challenge novelty:** counterexamples or semantic descriptors distinguish the task from its parent's function, not just range labels.
4. **Learnability:** challenge difficulty is bounded enough for at least a reference method; the world cannot promote itself for making organisms fail on impossible tasks.
5. **Population diversity and budget:** cap duplicates, unbounded families and computationally explosive admission.

The verifier's witness must not flow into organism or world proposal inputs. A witness obtained by exhaustive grammar search demonstrates search-space admissibility **only** under that grammar and budget; it does not establish general solvability or task utility. For genuinely novel family claims require independent functional differentiation from existing admitted tasks under a common input domain or an appropriate equivalence proof.

Initial design families: pure integer arithmetic, order/comparisons, and function composition. List/string and reliability worlds are deferred until the IR actually represents those semantics. Generation policies initially transform verified integer relations (for example max, min, bounded addition) under a grammar of safe relational templates, with formal admission and exact versioned task identities. Re-labeling MAX2 as a new family fails the novelty gate.

## 7. Promotion and reproduction contracts

### Proposed public domain interfaces

These are **DESIGNED** interfaces. They are not imports that exist in `cin/` today. Current public functions are catalogued in [CONTRACTS.md](../architecture/CONTRACTS.md).

```python
class EvolutionPort(Protocol):
    def propose(self, organism_id: str, world_id: str, budget: Budget) -> Iterator[Candidate]: ...
    def evaluate(self, candidate: Candidate, world_id: str) -> Verdict: ...
    def promote(
        self, candidate: Candidate, certificates: tuple[Certificate, ...]
    ) -> GrowthDecision: ...
    def spawn(
        self, parent_ids: tuple[str, ...], inheritance: InheritanceBundle
    ) -> BirthDecision: ...


class WorldPort(Protocol):
    def propose_world(self, parent_world_id: str, budget: Budget) -> WorldProposal: ...
    def admit(self, proposal: WorldProposal) -> Admission: ...


class EvaluationPort(Protocol):
    def verify(self, program_hash: str, spec_hash: str, budget: Budget) -> Verdict: ...
    def certify_maturity(self, organism_id: str, cohort_id: str) -> MaturityDecision: ...
```

No skeleton adapters or abstractions should be committed until the first phase's tests require them.

### Promote if and only if

- Hash of candidate IR matches archived content; interpreter/static type limits pass.
- The verifier returns `PASS` on the exact immutable world specification.
- Every previously retained binding to affected specifications is regression-checked.
- There is evidence of a genuine contribution: new semantic task, proven improved behavior, or measured cost reduction. Mere re-verification on an expanded range is transfer robustness but not a new capability.
- Resource budgets and event log accounting cover rejected as well as accepted proposals.

### Reproduce if and only if

- Parent and target birth artifacts are immutable and lineage is linked by content hashes.
- Each inherited skill has a real certificate; dependency closure is included and rechecked.
- Inheritance across **two world spec hashes of the same task** remains allowed as v0.1 *mechanical demonstration only* but cannot count toward the v0.4 cross-family inheritance claim.
- Mutation of a driver policy requires separate head-to-head replay and regression checks. A declared `adaptation` field is not evidence of actual adaptation.
- Birth does not reuse or mutate the parent's active maturity or stop contracts.

### Terminal outcomes

`ADMITTED`, `REJECTED`, `UNKNOWN` apply to world admission; `PASS`, `FAIL`, `INVALID`, `UNKNOWN` to candidate verdicts; `PROMOTED`, `REJECTED`, `DEFERRED` to growth; and `CERTIFIED`, `NOT_CERTIFIED`, `NOT_EVALUATED` to maturity. None of these statuses can be inferred from an arbitrary human-readable `reason` field. Version every future protocol status enum change.

## 8. Lifecycle state machines

See [EVOLUTION.md](../architecture/EVOLUTION.md) for transitions and failure semantics. An organism is born, enters active growth, may be provisionally evaluated, promoted, fork offspring, mature, plateau, stop and archive. Spawning is a *side effect of a verified reproduction decision*, not a prerequisite for calling the parent mature. A child is never allowed to rewrite its parent's record.

A world is proposed, validated, admitted/unknown/rejected, active, potentially forked, retired and archived. No admitted world may retroactively edit an earlier challenge; all changes create new versioned specs.

## 9. Evidence, identity, replay and storage

Content identity: canonical JSON-encoded IR/spec/genome hashes; do not equate `world_id` or `organism_id` to proof of integrity. Version canonicalization to prevent two runtimes hashing semantically equal content differently. Store at least:

- Immutable manifest: source/tree revision, Python/dependency versions, schema/IR/grammar versions, interpreter/governor limits, RNG algorithm/state, hardware and budget definitions.
- Artifact graph: seed, world, candidate, accepted capability, policy, certificate, offspring genome, parent references, and event sequence.
- Verdict: admitted domain/theory, checked input count, solver/witness method, counterexample/unknown reason, operation count, version and proof scope.
- Events: proposals, rejections, promotions, world fork admission, inheritance, maturity assessment, stop, archive and budget use (including admission work).

**Current behavior:** JSONL single-process hash chain, no persistent scheduler recovery, no cryptographically authenticated signature or independently anchored journal. **Future proposal:** SQLite transactional event store + content-addressed blobs only when resumable multi-generation experiments require it. Signatures/anchoring require a separate threat-model decision. Raw candidate code is not executable outside the data-only interpreter.

## 10. Security and operational contract

- Treat all seed/world docs and generated expressions as untrusted data; do not deserialize executable Python or `eval`/`exec` source.
- Permit only a typed closed operator set with no imports, file I/O, sockets or dynamic reflection; static checks alone do not replace runtime quotas.
- Enforce maximum AST depth/nodes, interpreter ops and bit widths; enforce total allocations, evaluator CPU time, candidate counts, epoch/world/population caps externally when implemented.
- All richer execution must be in a separately permissioned OS sandbox with no network by default, read-only inputs, process/time/memory limits and no host secrets. Until that exists, reject arbitrary generated Python.
- Keep sealed holdout datasets, witness implementations and evaluation keys outside the runtime's organism/world-readable store.
- Hash chaining protects accidental changes and detects unprivileged journal corruption, **not** a malicious privileged host able to rewrite the entire chain.
- No auto-push, autonomous deployment, external actuation or persistent daemon is authorized by this design.

Full threat matrix, recovery and governance: [SECURITY.md](../architecture/SECURITY.md).

## 11. Experimental verification design

**Pre-registration (proposed):** Freeze task corpus, grammar/evaluator hashes, random seeds, budgets and analysis scripts before comparative runs. Make held-out transfer inaccessible to evolution. Use >=5 independent seeds for engineering pilots; size any serious confirmatory study using measured variance and a power or precision plan, not arbitrary five-run significance claims.

Matched controls:

- **C0:** Random typed search under the same grammar/complete accounting.
- **C1:** Fixed task families, no hereditary shared abstractions.
- **C2:** Heritable organisms, frozen worlds.
- **C3:** Co-evolving semantic worlds, fixed driver.
- **C4:** Full co-evolving worlds + heritable abstractions + validated driver changes.

Primary outcomes: held-out task-family pass rate, newly solved *semantic* functions per full operation budget, generalization across unseen input distributions, and new task solve-cost with an explicit denominator. Secondary: archive functional diversity, admission rejection/unknown rates, regression, plateau, survival and total energy/CPU diagnostics. Account for world witness search, retries and validation. Never count two ranges of MAX2 as two learned functions.

**Falsification rule:** If C4 does not improve the preregistered primary outcome against relevant controls within uncertainty, report the negative result. If ablations do not share budgets and capability schemas, do not infer causal advantage. Maturity must be certified on a sealed transfer set by an evaluator whose policy was frozen before the run. Detailed protocol in [EXPERIMENTS.md](../research/EXPERIMENTS.md).

## 12. Roadmap, acceptance and delivery seams

| Milestone | Deliverable | Gate | Claim allowed |
| --- | --- | --- | --- |
| P0 | v0.1 existing pilot and docs audit | Reproducible 35-test baseline and replay | Bounded mechanism demonstration |
| P1 | Multi-epoch scheduler and durable lifecycle | Crash-resume, total budget and event invariants | Multiple controlled generations |
| P2 | Formal semantic world generator | Novel admissible tasks, differentiating tasks and unknown handling | Functional world diversification |
| P3 | Hereditary reusable program abstractions | Reuse across different functional task families with replay | Cross-task capability inheritance |
| P4 | Versioned driver adaptation and controlled policy selection | No regression or leakage, measured A/B search gain | Bounded meta-adaptation |
| P5 | Frozen benchmarks and matched-budget ablations | Sealed holdout, reproducible multi-seed comparisons | Evidence for/against H1-H3 |
| P6 (conditional) | Stronger solver and worker isolation | Proven research bottleneck and threat-model approval | Expanded proof domains or code execution scope, **not** unrestricted autonomy |

The phases are **dependency-ordered**, not calendar commitments. P5 cannot be claimed while P2/P3 remain merely theoretical. A test passing in P1 does not license the P4 claim. See [PHASES.md](../roadmap/PHASES.md) for concrete gates and [implementation plan](../plans/2026-10-18-cin-next-phases.md) for exact proposed files and focused tests.

## 13. Architecture choices and rejected complexity

**Chosen:** typed CIN-IR, finite formal worlds, independently owned verifier contracts, modular single-runtime scheduling, immutable artifacts, explicit lifecycle transitions, eventual isolated workers where the executable surface expands.

**Rejected for now:** generic LLM API, locally downloaded coding model, self-modifying Python interpreter, microservices, web control plane, Kubernetes, message brokers, complex agent prompt hierarchy, Rust rewrite, large vector DB, SMT proof on every candidate, unbounded world proliferation. Introducing any of these requires a demonstrated missing capability, cost/benefit comparison and new ADR.

A learned numeric search policy using NumPy may be tested in P4 only if simpler deterministic and tabular policies fail to deliver equivalent gains. NumPy does not by itself supply novel program semantics or free intelligence.

## 14. Traceability and research provenance

| Requirement group | Current module / sample | Proposed owner | Tests/gate |
| --- | --- | --- | --- |
| Genome schema | `cin/contracts.py`, `schemas/seed-genome.v0.1.schema.json` | Genesis | `tests/test_contracts.py`, P1 |
| Typed execution | `cin/ir.py` | CIN-IR | `tests/test_ir.py`, all phases |
| Growth proposals | `cin/search.py` | Growth | `tests/test_search.py`, P3/P4 |
| World validity | `cin/worlds.py` | Worlds + independent verifier | `tests/test_worlds.py`, P2 |
| Verified reproduction | `cin/evolution.py` | Lifecycle / reproduction gate | `tests/test_evolution.py`, P1/P3 |
| Evidence archive | `cin/archive.py` | Artifact/evidence store | `tests/test_evolution.py`, P1 |
| CLI | `cin/__main__.py` | Research operator | `tests/test_cli.py`, P1 |
| Scientific measurement | `experiments/RESULTS.md` | Research controller | P5 preregistered study |

Research review and primary references are curated in [LITERATURE.md](../research/LITERATURE.md). Key architectural records: [ADR-0001](../adr/0001-isolated-verification.md), [ADR-0002](../adr/0002-typed-formal-first.md), [ADR-0003](../adr/0003-single-process-first.md).

## 15. Known gaps, open decisions and explicit assumptions

- **DESIGNED:** semantic-equivalence canonicalization and independently constructed oracle for new tasks. Current `worlds.py` checks a fixed finite DSL and admits via private grammar search; it cannot certify general functional novelty.
- **DESIGNED:** multi-epoch scheduler's exact RNG snapshot and crash-resume semantics. P1 contract below specifies deterministic transitions but storage choice remains reversible until evidence.
- **DESIGNED:** adaptation policy learning method. Begin with simple bandit/score-weight updates, gated at offspring birth, without assuming neural models.
- **RESEARCH HYPOTHESIS:** broad task-family transfer and actual improvement per compute budget, which may fail under fair controls.
- **UNKNOWN:** which small grammar expansion most improves reusable abstraction learning without exploding search cost. Measure first.
- **UNKNOWN:** whether solver-based validation is tractable on generated task families; any integration records `SAT`, `UNSAT`, `UNKNOWN` distinctly and tags proof scope.
- **LIMITATION:** no embedded separate OS sandbox, even though generated CIN-IR presently has no I/O operators. P6 is a blocker for free-form code execution.
- **OPERATING ASSUMPTION:** experiments run locally and offline, one trusted user/process, until persistent multi-operator scheduling is expressly approved.

## 16. Definition of an accepted v0.4 design artifact

- All current-vs-proposed claims agree with the source tree and observed reports.
- Exactly five genome genes; world is external; verifier cannot be modified by evaluated actors.
- Every proposed promotion, inheritance and world admission state has an owner, failure semantics and an independent test seam.
- Lifecycle, budget, storage and recovery obligations are measurable.
- Research hypotheses are falsifiable with frozen controls/holdout and full accounting.
- The next implementer can start at P1 without inventing basic interfaces or changing the deployed v0.1 contracts.
