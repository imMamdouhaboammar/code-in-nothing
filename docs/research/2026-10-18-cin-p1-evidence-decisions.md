# P1 scientific baseline and research decisions (2026-10-18)

**Scope:** Live `main` at `653ef4efa7acf25395cc99d5fac21bc1cf2ee563`; implementation under [PR #4](https://github.com/imMamdouhaboammar/code-in-nothing/pull/4). Earlier pilot reports are retained verbatim. Documentation of future capability is not observed runtime evidence.

## Evidence ledger

| Claim | Classification | Source / scope | Missing gate |
| --- | --- | --- | --- |
| Five-gene invariant, bounded interpreter, independent finite-world verifier | IMPLEMENTED; previous tests GREEN | `cin/contracts.py`, `cin/ir.py`, `cin/worlds.py`, `tests/test_contracts.py`, `tests/test_ir.py`, `tests/test_worlds.py` | No universal proof |
| Task-blind typed cost-layered search, opt-in 1..8-input IR | IMPLEMENTED; previous tests GREEN | `cin/search.py`, `tests/test_math_search.py`, `tests/test_multi_input_ir.py` | No 3-input independent-world admission |
| M1 min2 / absdiff | OBSERVED finite-domain pilot | `experiments/run_m1.py`; 81/81 domain checks each; proposal counts in `docs/research/2026-10-18-m1-math-synthesis-evidence.md` | No matched total-cost advantage claim |
| Hash-linked event journal | IMPLEMENTED, limited | `cin/archive.py`; original `tests/test_evolution.py` | Incomplete run configuration and restart semantics before PR #4 |
| Manifest-bound completed-run rerun | IMPLEMENTED on unmerged PR #4, CI-verified | `cin/archive.py`, `cin/evolution.py`, `tests/test_cohort_replay.py`; [CI](https://github.com/imMamdouhaboammar/code-in-nothing/actions/runs/39160027507) | Not crash recovery, scheduler, governor |
| Crash/restart-safe three generations | DESIGNED; NOT IMPLEMENTED | `docs/roadmap/PHASES.md`; `docs/plans/2026-10-18-cin-next-phases.md` | P1-02 and P1-03 |
| Mathematical novelty, hereditary macro transfer, policy adaptation and SMT proof | HYPOTHESES / DESIGNED | v0.6 integrated research spec | P1 plus later independent gates |

The earlier [P1 architecture research](2026-10-18-cin-p1-research-and-architecture.md) uses a weighted monolith score (3.70/10). This is a heuristic design preference, **not a measured experiment, validated statistical scale, or implementation proof**. The present bounded single-process workload and existing ADR 0003 are sufficient reasons not to distribute.

## Primary-source comparison and engineering decisions

| Mechanism, primary source | What it establishes | CIN applicability and limitation | Decision / falsification test |
| --- | --- | --- | --- |
| [Bottom-up synthesis, MIT CSAIL](https://people.csail.mit.edu/asolar/SynthesisCourse/Lecture3.htm); [equivalence reduction research (2018)](https://par.nsf.gov/servlets/purl/10100598) | Grammar enumeration and observational equivalence reduce redundant terms over chosen inputs | CIN's fixed probes can collapse programs that differ elsewhere. Search successes do not imply completeness | **EXPERIMENT LATER:** compare task-independent structural canonicalization and existing fixed probes to unpruned cost-layered search under fully metered equal budgets. Count lost valid representatives |
| [SyGuS 2013](https://www.cis.upenn.edu/~alur/SyGuS13.pdf); [SyGuS language 2.1](https://arxiv.org/abs/2312.06001) | Bounded grammar/correctness constraints and CEGIS counterexample refinement | A counterexample can accelerate learner filtering, but any verifier data released to training must be explicitly public and billed. Never release sealed holdout or witness source | **EXPERIMENT LATER:** compare no-CEGIS and public-training-only CEGIS with identical final independent verifier and total search/checking costs |
| [cvc5 documentation 1.3.2](https://cvc5.github.io/docs/cvc5-1.3.2/api/python/base/synthresult.html) | The Python `SynthResult` distinguishes `hasSolution()`, `hasNoSolution()`, and `isUnknown()` | External solver output cannot be counted as CIN's own model-free generated program. Solver time/UNKNOWN needs independent accounting | **DEFER:** optional separate solver baseline, only after proof-domain translation tests; UNKNOWN is never PASS |
| [egg/equality saturation (POPL 2021)](https://arxiv.org/abs/2004.03082); [official source](https://github.com/egraphs-good/egg) | Congruence/equivalence classes can compact large rewrite spaces | New Rust bridge/e-graph dependency is speculative without evidence structural normalization is insufficient | **REJECT FOR NOW:** benchmark smaller canonicalization first; reconsider only after demonstrated bottleneck |
| [DreamCoder (PLDI 2021)](https://people.csail.mit.edu/asolar/papers/EllisWNSMHCST21.pdf) | Library induction can improve program synthesis across multiple domains | Its neural recognition component and evaluated tasks differ materially from CIN's no-model architecture; positive transfer cannot be presumed | **EXPERIMENT LATER:** typed abstraction reuse versus ablation on functionally distinct held-out tasks, including extraction/replay cost and negative-transfer failures |
| [SQLite atomic commit](https://sqlite.org/atomiccommit.html); [SQLite WAL guide](https://sqlite.org/wal.html) | Atomic transactions and defined recovery semantics; WAL durability depends on configuration | CIN's current JSONL/hash journal is not crash-atomic for births, checkpoints and budget charge | **DEFER to P1-03:** compare single-store SQLite transaction to safely transactioned archive under crash injection; no WAL assumption without power-loss semantics tests |

## Cost-normalized benchmark contract before M1 claims

Predeclare inputs (grammar/version, task-family definitions, signed domains, seed/cohort splits, hardware/runtime, case/bit/node limits, and the blinded evaluation set). Each arm must meter search tree construction, rejected shapes, signature/probe evaluations, screen cases, independent verifier calls and interpreter operations, admission witness search, replay, and any macro or policy preparation. Record CPU time as an auxiliary environment-dependent measurement rather than a substitute for operation counts. Keep unknown, invalid, exhausted, failed and passed separate. No candidate sees the verifier-private witness or sealed evaluation tasks.

A development `PASS` over 81 signed input pairs means only that the declared finite domain was exhausted. If matched controls win or all runs exhaust the budget, preserve the negative/inconclusive outcome and do not redesign the threshold afterward.

The new P1-01 scientific trace **does not yet meter** the above costs completely. It establishes a reproducible input/evidence boundary; it must not be presented as closure of H1 or complete resource governance.

## Dependency-ordered next actions

1. **P1-02:** red tests for finite epochs, per-actor/governor work accounting including world admission and replay, terminal idempotence, and cross-actor budget separation.
2. **P1-03:** crash injection at child publication, acceptance, journal/checkpoint commit and post-stop. Require no duplicate birth, budget reset or reopened terminal actor after resume.
3. **P1 complete gate:** at least three persisted valid generations; exact parent DAG; equivalent interrupted/uninterrupted normalized scientific outcome and immutable five-gene policy. Only then move to multi-input world `cin.world/v0.3`.
4. **Independent M1 closure:** run fixed, matched search controls and publish total cost distributions separately; this may proceed in its own branch with the existing verifier unchanged.

**Reproduction:** `python -m cin validate`, `python -m pytest -q`, `python experiments/run_m1.py`, `python -m ruff check .`, `python -m ruff format --check .`. On PR #4, `tests/test_cohort_replay.py` exercises manifest and rerun cases. CI links evidence for code changes; documentation alone is not proof.
