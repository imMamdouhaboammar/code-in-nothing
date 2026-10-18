# CIN experimental public fitness and feedback-guided search: research decision

**Status:** Implemented experimental slice; scientific benefit not assumed. **Baseline:** `58bd9bbbe49437d087625db972e533b395f07250` (2026-10-18). **Evidence contract:** `cin.guided-ablation/v0.1`. Existing v0.6 math design remains a proposed research program.

## Observed repository baseline

`cin/search.py:candidate_stream` is cost-layered, typed, and task-blind. Its fixed observational probes may collapse programs that differ outside probes; this is a search heuristic, not a theorem. `cin/worlds.py:verify_program` independently checks a finite declared two-input domain and returns `PASS`, `FAIL`, `INVALID` or `UNKNOWN`. The M1 screening harness stops at the first failing public case and does not feed results into generation. `cin/governor.py` had candidate, verifier-operation, search-shape and probe counters but no distinct public-training or selection dimensions. The P1 lifecycle does not yet establish crash-resumable multi-generation evolution. These are code observations, not a new claim about general synthesis.

## Verified scientific sources and their limits

- La Cava et al., *A probabilistic and multi-objective analysis of lexicase selection and epsilon-lexicase selection*, https://pmc.ncbi.nlm.nih.gov/articles/PMC9453780/ : case-level errors can preserve specialists near Pareto front boundaries. Does not prove benefits for CIN's tiny typed grammar.
- Helmuth et al., *Lexicase Selection of Specialists*, https://arxiv.org/abs/1905.09372 : motivates retaining individual case errors rather than only a scalar.
- La Cava et al., *Epsilon-Lexicase Selection for Regression*, https://arxiv.org/abs/1905.13266 : epsilon relaxations concern continuous-error settings; CIN's current Boolean per-case relations do not justify importing epsilon thresholds.
- Barke, Peleg and Polikarpova, *Just-in-Time Learning for Bottom-Up Enumerative Synthesis*, https://arxiv.org/abs/2010.08663 : demonstrates guided enumerative synthesis in another setting; not evidence that a learning model is justified here.
- Solar-Lezama, *Introduction to Program Synthesis, Lecture 3: Bottom Up Explicit Search*, https://people.csail.mit.edu/asolar/SynthesisCourse/Lecture3.htm : observational equivalence based on finite examples can conflate programs that differ elsewhere, and context sensitivity matters.
- Alur et al., *Syntax-Guided Synthesis*, https://escholarship.org/uc/item/1g67m7hp : grammar and logical correctness specifications are distinct; CEGIS is a deliberate oracle interaction, not an implicit permission to leak verifier counterexamples into training.
- Polgreen, Reynolds and Seshia, *Satisfiability and Synthesis Modulo Oracles*, https://www2.eecs.berkeley.edu/Pubs/TechRpts/2021/EECS-2021-10.html : models oracle-guided feedback formally. CIN does not implement a newly authorized CEGIS channel.
- Helmuth and Kelly, *PSB2: The Second Program Synthesis Benchmark Suite*, https://arxiv.org/abs/2106.06086 : 25 harder general tasks, not directly runnable under CIN's current small two-argument IR/worlds.
- https://github.com/thelmuth/program-synthesis-benchmark-datasets : primarily original general synthesis benchmark datasets; no claim of PSB2 compatibility here.
- Boldi et al., *Informed Down-Sampled Lexicase Selection: Identifying Productive Training Cases for Efficient Problem Solving*, https://pubmed.ncbi.nlm.nih.gov/38271633/ : motivates case representativeness, but no safe inferred-training-case sampler is yet implemented.

## Alternatives and decision

| Alternative | Advantage | Important limitation | Decision |
| --- | --- | --- | --- |
| B0: task-blind cost-layered enumeration | Simple deterministic baseline | No candidate-error-driven generation | Retain unchanged |
| B1: identical enumeration plus complete public case scoring | Isolates overhead and measures fractional fitness | Cannot improve proposal order itself | Mandatory measurement control |
| B2: bounded graded selection and typed neighborhood expansion | Feedback explicitly changes which parent is expanded and next program ASTs | Can chase training bias, prematurely collapse search, and cost more | **Experimental opt-in** |
| B3: seeded lexicase parent selection | Can favor specialists on individual cases | Extra selection and ablation complexity | Defer until B2 evidence justifies it |
| Numeric error shaping | Potentially more nuanced than binary per-case error | Relation may allow multiple outputs; no authorized distance metric | Do not invent unique targets |
| Full CEGIS / learned probabilistic grammar | Can provide strong feedback for different synthesis settings | Trust boundary and large added mechanism | Reject for this slice |
| Probe-based observational equivalence pruning | Controls search explosion | Can discard out-of-probe behavior | Existing baseline only; not a proof |
| Direct exhaustive candidate checking alone | Strongest finite-domain verdict | More verifier work and no search guidance | Mandatory exclusive acceptance gate |

**Decision:** use a complete immutable public training panel; record `0/1/None` per-case errors and a satisfaction fraction only for valid complete nonvacuous evaluations. Keep independent verifier verdicts as the sole correctness authority. Seed deterministically and cap pool, grammar depth, node count, proposals, case count, and selection/mutation attempts. Record all evidence including unsuccessful seeds; never promote partial fitness.

`pass_fraction=3/5=0.6` is a descriptive score, not a smooth mathematical gradient. `1.0` means only full satisfaction of the supplied public panel, not proof. `UNKNOWN`, `INVALID`, and `VACUOUS` have null fitness, not silently assigned zero.

## Isolation, budget and interpretation

The training evaluator receives a copied frozen *public* world predicate and explicit public cases, the candidate and a verified input signature. It does not accept admission witnesses, proof logs, hidden transfer labels, or private counterexamples. The selection controller only receives complete matching training evidence; verifier results do not determine which parent it selects. World admission and inheritance remain outside the experiment.

`cin.guided-ablation/v0.1` reports candidate counts, search-shape attempts, fixed probe evaluations, public training-case operations, predicate *invocations*, selection and mutation attempts, verifier calls/cases and interpreter operations, plus wall-independent CPU time. Existing `cin.evidence/v0.1` is not rewritten. Legacy zero-default Cost dimensions remain compatible with its arithmetic.

**Known incomplete accounting:** predicate *internal* evaluation nodes, Python allocation and hashing, PR/CI setup, admission-witness work (not run), replay persistence, and peak RSS are not fully measured in the experimental ledger. `accounted_events=sum(cost dimensions)` is an explicitly **uncalibrated unit-weight proxy**, not physical operations or an adequate substitute for equal elapsed-time/CPU budgets. All arms get identical per-dimension cap vectors and proposal ceilings, but **this is not an equal-total-compute stopping rule**; B1/B2 can spend more total work than B0. Claims of compute efficiency or superiority therefore require a further stricter matched-total-cost experiment. Seed variance from a five-seed set should be shown descriptively; confidence intervals cannot rescue a small, convenience task sample.

The ablation B0 does direct finite verifier checks for its baseline candidates; it does **not** reproduce M1's earlier public screening filter. Run `experiments/run_m1.py` separately as the historical M1 regression.

## Predeclared protocol, falsification criteria, and scope

`experiments/run_guided.py` fixes MAX2, MIN2 and ABSDIFF, public cases `(-4,-1),(1,-4),(0,0),(-2,3),(3,-2)`, seed set `0,1,2,3,4`, arms B0/B1/B2, and default 250 proposals per trial. The verifier exhausts the declared world domains within its existing case bound. Record every trial, its counters, seed, hashes, scores, selected parents and independently verified success or `UNKNOWN`. The GitHub CI artifact stores the raw JSON without selecting successful seeds.

The primary research question is whether B2 gains **independently verified successes per total accounted computation** after fair charging. A secondary *mechanism* test requires B0 and B1 to enumerate identical candidates while B2 demonstrably generates different future candidates following training-selected parents. A single training-perfect candidate or changed selection ordering does not meet the primary endpoint. Current tests establish only the bounded mechanism and regressions, not statistically supported efficiency gains.

Stop or revise B2 when it gives fewer verified successes or costs more for similar results. Do not change CIN's default driver or claim maturity/adaptation benefits from this experiment.

## Reproduction

```sh
python -m pytest -q
python -m cin validate
python experiments/run_m1.py
python experiments/run_guided.py --seeds 0 1 2 3 4 --proposals 250 --output runs/graded-five-seed.json
```

Results are only verified after the exact branch/head CI and recorded experiment artifact complete; any missing artifact is a blocker, not a positive result.
