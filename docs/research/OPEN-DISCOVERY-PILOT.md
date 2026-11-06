# Open-discovery transfer pilot

**Status:** Exploratory design, recorded before executing the new pilot. No confirmatory claim

## Question and possible negative result

Can a program-synthesis learner reuse integer-valued subprograms discovered from its own formally proved training programs to solve unseen registered tasks at a fixed reported work threshold? A valid negative outcome is unchanged or worse held-out coverage, work, or latency with inheritance enabled.

## Freedoms in the discovery arm

- No task-name guidance or manually authored `max2` / `min2` macro bodies
- No MDL minimum savings, frequency, minimum AST size, or demonstrated transfer-benefit prerequisite for discovery
- Collect all integer-valued subtrees, including whole programs, deduplicate by normalized canonical form, and preserve provenance. Keep even inefficient macros to expose the actual branching cost
- Discovery never reads holdout specifications, reference oracles, task names, or verdicts
- Holdout use is evaluation-only after a frozen library is built. Both arms run the same synthesis engine and grammar with the library toggled on/off

Only type-correct pure CIN-IR programs are executable. Independent Z3 checks and finite resource safeguards remain in place. A subtree is inherited syntax from a verified program, not an independently proved new task specification.

## Frozen exploratory manifest v0

- Training: `max2`, `min2`, `absdiff`
- Heldout: `max3`, `min3`, `clamp3`, `median3`, `max4`
- Training and holdout are disjoint by named task ID. Composite families overlap by semantic components, so this is **compositional transfer**, not cross-family generalization
- Stress: two generated arithmetic tasks with 5 and 8 inputs, plus 20 syntactically valid unrelated distractor macros; show every failure and timeout
- Single Mac host, local experimental run, seeds 0 and 1 for order-balanced arms; cohort size too small for inferential statistics
- Per-run synthesis ceilings: 6 CEGIS rounds, 3 seconds soft wall limit checked between rounds, common allowed AST grammar/depth/nodes. Individual calls may exceed soft time limit
- Primary reported threshold: 200,000 combined observed enumerations, probe evaluations, auxiliary scoring steps, and verifier calls per heldout attempt. Report every actual overrun and exclude its success from under-threshold solved count
- Training and macro discovery costs are included in inherited-arm total; baseline includes identical training cost to isolate inheritance. The work threshold is an **outcome eligibility check**, not a runtime-enforced hard cap. Verifier complexity is additionally reported in invocations and milliseconds. Do not call this an equal CPU-operation budget

## Execution and interpretation

1. Run training tasks using the same CEGIS solver without a library; only admit formal `SYMBOLIC_PROVED` expressions
2. Mine every normalized, typed integer subtree from those programs; preserve zero-utility candidates
3. Freeze the macro set before importing holdout task objects
4. Execute holdout pairs in deterministic rotated order, one arm with the frozen library, one without it
5. Report training cost, discovery cost, per-task work and proof verdicts, transfer arm elapsed time/RSS, heldout failures, distractor overhead and 5/8-input failures
6. Scientific advantage requires a later larger sealed corpus, rigorous shared resource governor, randomized independent cohorts and confidence analysis. This exploratory pilot can establish mechanism and discover failure boundaries only

## Observed exploratory pilot, 2026-11-06

Command: `uv run --extra dev python -m experiments.run_open_discovery_pilot --output runs/open-discovery-pilot-2026-11-06.json`

- Host: local Apple Silicon macOS, Python 3.12.13 via uv, source based on `ffaa0fe` plus this uncommitted experiment patch at execution time
- Training formal proof: `max2`, `min2`, `absdiff` all `PROVED`
- Discovered: **5** unique integer subprograms (`max2` whole solution, `min2` whole solution, `absdiff` whole solution, shared subtraction, argument identity); the Boolean comparator was excluded by type checking
- Training work units: `max2=1805`, `min2=1804`, `absdiff=29280`; inherited discovery examined all typed candidate nodes in 0.39ms
- Two task-order seeds, `0` and `1`, gave identical proof statuses and work-unit counts, with different elapsed timings. They are scheduling replicates on one machine, not independent cohorts

### Complete registered-task census, seed 0

Work units combine enumerated primitive expressions/predicates, public probe executions, scoring steps, attempted shapes and verifier calls, each counted once in this index. **They are not equal-cost CPU instructions or a runtime-enforced budget.** The 200,000 threshold determines eligible successes only

| Task | Role | No inheritance | Work | Open inheritance | Work |
| --- | --- | --- | ---: | --- | ---: |
| max2 | training | PROVED | 1,805 | training input | 1,805 |
| min2 | training | PROVED | 1,804 | training input | 1,804 |
| absdiff | training | PROVED | 29,280 | training input | 29,280 |
| max3 | heldout | EXHAUSTED | 412,544 | PROVED | 111,421 |
| min3 | heldout | EXHAUSTED | 240,621 | PROVED | 193,048 |
| clamp3 | heldout | PROVED | 2,181 | PROVED | 12,475 |
| median3 | heldout | EXHAUSTED | 303,788 | EXHAUSTED | 240,149 |
| max4 | heldout | EXHAUSTED | 424,334 | EXHAUSTED | 179,212 |

`max3` and `min3` meet the work-index threshold in the inherited arm and fail in the baseline. `clamp3` succeeds in both arms but inherits **5.7×** more counted work (and around 16× more solver wall time) when the full ungated library is available. `max4` and `median3` remain unsolved in both. This is small compositional transfer, not cross-family scientific generalization.

### Mandatory distractor and input-arity stress

| Task | No library | Work | 20 unrelated affine macros | Work |
| --- | --- | ---: | --- | ---: |
| clamp3 | PROVED | 2,181 | PROVED | 28,765 |
| sum5 | EXHAUSTED | 3,467,490 | TIMEOUT (7s) | interrupted, unavailable |
| sum8 | SYNTHESIS_FAILED | 115,164 | TIMEOUT (7s) | interrupted, unavailable |

All per-run probe counts, enumerations, auxiliary search steps, shapes, Z3 call counts and time, elapsed time and worker peak RSS are in the raw local JSON. The worker-terminated runs cannot expose partial counters yet; do not interpret the missing counters as zero.

### Post-hoc mechanism ablation

After observing the initial results, a follow-up diagnostic isolated complete verified training programs from their proper subtrees. This was **post-hoc**, and it reused the same holdout tasks

| Heldout | Whole-program macros only | Work | Proper subtrees only | Work |
| --- | --- | ---: | --- | ---: |
| max3 | PROVED | 95,447 | EXHAUSTED | 451,232 |
| min3 | PROVED | 165,112 | EXHAUSTED | 279,309 |

This narrows the positive finding to **automatic whole-program reuse**. The currently mined proper subtrees alone did not yield a heldout win. The full work logs and evidence are in `experiments/evidence/open-discovery-pilot-2026-11-06.json` and `experiments/evidence/open-discovery-pilot-2026-11-06-v2.json`. In the second run, `sum5` baseline work increased from 3.47M to 5.09M while remaining `EXHAUSTED`, showing that some solver/search trajectories are not stable across reruns.

**Supported finding:** the learner can automatically mine typed pieces of its own formally proved programs and use them in the existing synthesizer to change some previously unseen composite-task outcomes. **Still unproven:** statistically reliable generalization, a net speedup, or a standalone benefit from proper-subtree abstraction. The holdout specification and public examples are available to the solver during evaluation, but were excluded from library construction.

## Risks

- Current candidate generator expands unary/binary macros; discovering macros of higher arity does not imply they can yet be consumed during synthesis
- The solver's observational signature pruning can drop useful subterms; equal signatures on probes are not formal equivalence
- Broad macro collection increases branching and may reduce performance
- The current CEGIS time ceiling checks between rounds, so measured elapsed time may exceed the soft limit
- Proof validity covers supported Z3 integer semantics under declared preconditions, not arbitrary Python programs or interpreter resource guarantees
