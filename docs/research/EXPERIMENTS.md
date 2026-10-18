# CIN preregistration and experimental protocol

**Status:** Experiment design, not an executed or registered confirmatory study. Freeze this protocol and task manifests *before* any study that will support claims. The v0.1 pilot reports are observational mechanism demonstrations only. See [pilot results](../../experiments/RESULTS.md).

## 1. Research questions and estimands

- **RQ1 / inheritance:** Does validated cross-task inheritance increase solved novel functions at the same total interpreter/proposal/admission budget?
- **RQ2 / worlds:** Does semantic world co-evolution yield more distinct verified capabilities than fixed worlds or domain-range mutation alone?
- **RQ3 / driver:** Does replay-gated driver adaptation reduce total compute cost to solve held-out tasks compared with a frozen mutation policy?
- **RQ4 / quality diversity:** Does maintaining a behaviorally diverse archive improve task-family coverage at equal resources?

The main unit of replication is an independently seeded **cohort run**, not the individual candidate proposal or individual task tested within the same evolving population. Report task-level outcomes nested within the cohort without treating them as statistically independent.

## 2. Study stages

**Engineering feasibility stage:** fast runs show budgets, lineage, admission, terminal archival and reproducibility. These runs are not significance studies.

**Exploratory stage:** freeze experimental arm descriptions and reporting code, run multiple seeds, estimate variance, failure rates and total cost. Use observations to design and preregister the confirmatory study; changes after exploration require a new cohort manifest.

**Confirmatory stage:** publish prior to running the comparison: exact task manifest and hash, family split, candidate grammars, seeds/seed strategy, primary estimand, budgets (including world validation), evaluation version, conditions, exclusion policy and statistical procedure. Keep held-out tasks sealed until final once-per-cohort assessment.

## 3. Matched experimental arms

| Arm | World progression | Organism growth | Inheritance | Driver adaptation |
| --- | --- | --- | --- | --- |
| C0 | Fixed family/task pool | Random typed sampling | No | No |
| C1 | Fixed task pool | Evolving grammar search | No shared abstractions | No |
| C2 | Fixed task pool | Hybrid individual/generation | Verified hereditary macros | No |
| C3 | Semantic co-evolving tasks | Hybrid individual/generation | Verified hereditary macros | No |
| C4 | Semantic co-evolving tasks | Hybrid individual/generation | Verified hereditary macros | Gated policy variants |

For an isolated world-evolution effect, compare C2 vs C3; for policy adaptation, compare C3 vs C4. C0/C1 measure the simpler search alternatives. A fixed-world baseline must have an equal opportunity to consume its allocated compute, not a lower budget just because it has fewer admission events. Account for time spent choosing worlds as part of full resource cost.

### Existing demo is not any complete C2/C3/C4 arm

The flags `--no-world-evolution` and `--no-inheritance` make structural controls for one seed; they do not implement semantic-world co-evolution, multi-run independent policy learning or matched-budget inference. Distinct spec hashes produced by MAX2 domain expansion must not count as distinct semantic functions.

## 4. Task corpus and blinded evaluation

Proposed pilot task families supported by an expanded and versioned IR: `arithmetic`, `comparisons`, `piecewise_composition`. Start with formal relations generated without using answer code in the organism. Balance families and complexity descriptors; hash the complete corpus, domain bounds, oracle definitions and sampling seeds.

For task novelty use immutable `semantic_task_id` derived from normalized relation + proof scope, accompanied by a validator that detects equivalent tasks under the considered theory/domain. If semantic equivalence cannot be proven in available resources, label `UNKNOWN` and exclude from novelty claims rather than forcing a decision.

Training feedback may expose task specifications, binary/typed verdicts and bounded counterexamples. **Sealed transfer** includes unseen tasks and evaluation domains that growth/world selection never sees; no per-task feedback from it is returned to active actors. Trial confirmatory size: at least 20 held-out tasks balanced by family, *subject to a pre-run power/precision analysis*; do not treat 20 as a universal statistically adequate number.

## 5. Budgets and denominators

Log these separately for every arm and cohort:

1. Candidate proposals **including rejects/duplicates**, and actual candidate interpreter node-operation count.
2. World proposals, rejected/unknown admissions, private witness proposals and verifier operation counts.
3. Regression replays, heritability replays, policy A/B validations, sealed final checks (whether inside research budget or reported as separate evaluation overhead).
4. CPU time, wall time, peak RSS and versions as supporting system-level diagnostics, not the sole normalization measure.
5. Population cap, world cap, AST size/depth/bits and generator attempts.

Suggested first fairness budget: constant aggregate interpreter-operation cap per cohort and separately fixed maximum number of admitted/rejected world attempts. Report both solved tasks at capped total cost and actual full overhead. If the world admission engine is computationally expensive, its cost cannot be hidden behind the organism's proposal counter.

## 6. Metrics and analysis

| Metric | Definition / denominator | Claim bound |
| --- | --- | --- |
| `heldout_family_pass_rate` | Number of independently passed withheld semantic tasks divided by frozen withheld tasks | Generalization under defined task split |
| `distinct_solved_tasks` | Unique independently verified relations after semantic equivalence filtering | Function coverage, not spec-hash count |
| `cost_per_new_task` | Total governed operations incl. candidate & world admission divided by new semantic tasks solved | Efficiency, undefined if zero tasks |
| `transfer_reuse_rate` | Eligible inherited macros replayed in >=2 genuinely distinct task functions divided by eligible inherited macros | Heritability, not mere genome copying |
| `macro_search_benefit` | Difference in matched heldout solve cost with/without macros; count macro discovery cost | General usefulness of abstraction |
| `functional_diversity` | Predeclared functional behavior descriptor cells occupied by verified distinct functions | Diversity, not code length |
| `maturity_certified_rate` | Certified organisms / all terminal organisms in the frozen cohort | Operational maturity; not intelligence |
| `regression_rate` | Rejected regressive promotions / attempted promotions | Gate failure characteristics |
| `unknown_rate` | Unknown evaluations / all evaluations, by reason | Incomplete proof visibility |

Prioritize a predeclared primary endpoint (recommended `distinct_solved_tasks` at equal full-operation budget, with held-out family pass rate as confirmatory co-primary only if study design supports multiplicity control). For between-arm comparisons, plot per-cohort paired differences and confidence/uncertainty intervals; report dispersion and zero-success cohorts. Select effect size threshold in preregistration, not after seeing the winner. Avoid post-hoc best-seed reporting.

## 7. Stop/go tests and falsification

- **Engineering gate:** All lifecycle events, budgets and versions are replayable; invalid worlds and tampered certificates cannot be promoted. Failure blocks comparative research.
- **Novelty gate:** At least two admissible task relations are different on common inputs and verified independently. Range-only expansion fails.
- **Reuse gate:** Removing a learned macro must worsen a held-out outcome or measured search cost under matched conditions. Mere syntax compression fails.
- **Co-evolution gate:** C3 vs C2 results across independent cohorts measure if new worlds actually help. If no measured difference, retain simpler fixed worlds.
- **Adaptation gate:** C4 vs C3 tests changed driver. If gain disappears on fresh tasks or budget-equivalent replay, discard adaptation policy.
- **Maturity gate:** Independent one-shot holdout assesses frozen criteria; zero leakage incidents; no back-filled certifications.

## 8. Reproducibility recipe

1. Record source revision (or exact source archive hash), Python/dependency versions and platform.
2. Validate all schemas and exact five-gene seed before experiment.
3. Store frozen task and holdout manifest hashes; holdout access restricted to final evaluation.
4. Pin every random seed/state and source of nondeterminism. Run sequential execution first.
5. Log proposal order, world admission search, verifier checked count, costs, all verdicts and lineages.
6. Re-run independently with the same manifest; compare canonical outcomes and decision chains, not timing fields.
7. Publish full distributions, exclusions, negative/unknown outcomes and raw artifacts for independent replication subject to sealed-set access restrictions.

## 9. Results statement template

> Under [source hash, cohort/task/grammar/evaluator version], arm [C*] solved [N] previously unseen semantic tasks out of [M] at [total accounted operations] across [K] independent seeds. Compared with [control], the estimated paired difference was [estimate and interval]. The test was [preregistered/exploratory]. Neither universal correctness nor general autonomous coding capability is inferred.

Do not populate brackets until those exact observed results exist.
