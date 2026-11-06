# Adaptive Open Discovery: versioned design and evidence

**Stage:** Exploratory. A v1 smoke run was executed before the v2 full benchmark. The P0 timeout and P2 tuple rule were revised after observing v1, and v2 must not be presented as independent confirmation. Negative, timed-out and unsupported outcomes must be recorded alongside successful ones.

## Question

When CIN can progressively widen its typed search grammar, macro arities, expression-size bounds and conditional-partition effort within measured host resources, does the previously observed program-reuse effect persist on unseen composite tasks, and which new tasks (if any) become provable?

An acceptable outcome is zero extra solved tasks, greater cost, or more hard timeouts. No parameter will be chosen post-run on the basis of a preferred outcome and described as confirmatory.

## Distinction between research freedom and machine safety

The adaptive experiment removes *fixed discovery gates* and lets its scheduler increase search complexity from one stage to the next. The scheduler does not pre-reject macros for low recurrence, MDL savings, or prior transfer utility. Macro calls of up to eight integer arguments may be tried. Stage ceilings, available primitives, finite CPU/memory limits and independent formal verification remain explicit, because an infinite computation on a laptop cannot be observed or reported.

Production CIN's existing defaults, schema and genome policy are unchanged.

## Manifest frozen before execution

- Repository baseline: experiment commit `5ff1cc7`, plus adaptive implementation under review
- Train: `max2`, `min2`, `absdiff`
- Heldout: `max3`, `min3`, `clamp3`, `median3`, `max4`; these are composition-related, not cross-family independent tasks
- Stress: `clamp3` with 20 synthetic distractor macros, `sum5`, `sum8`, each under the same adaptive schedule
- Primary arms: no inheritance vs. the automatically discovered full library from proved training programs
- Diagnostic arms: proper-subtrees-only, full-programs-only, and full library with 20 distractors on the stress tasks
- Task order and arm order: seeded shuffles, seeds 2 and 3, with each task paired across conditions. These are two scheduling repetitions on one host, not independent research cohorts

## Progressive profiles

The same profile schedule is available to every arm. Each stage is a separate supervised process and stops upon proof, a hard timeout, a memory overrun, or a process failure. Unsolved non-fatal stages continue to the next profile while global wall time permits.

| Stage | AST depth | AST nodes | Constants | Subterm depth | Predicate term depth | Macro arity cap | Macro tuple budget | Conditional split budget | Per-stage hard wall |
| --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | --- | ---: |
| P0 | 7 | 25 | 0,1 | 3 | 2 | 2 | original unary/binary enumeration | original 512 bound | 3s |
| P1 | 9 | 49 | -1,0,1 | 4 | 3 | 4 | 2,000 per macro | 2,048 | 3s |
| P2 | 12 | 96 | -2,-1,0,1,2 | 5 | 4 | 8 (the current typed IR limit) | no tuple count cap | unbounded within worker | 4s |

- Hard task envelope: 10 seconds of worker execution per arm at most, plus worker startup/teardown overhead
- Peak resident set cap: 400 MiB per worker, monitored from parent at 50ms intervals, with explicit `MEMOUT`
- Revision ledger: v1 smoke used 2s at P0 and 8,000 tuples/macro at P2; it demonstrated timeouts on previously provable cases, making the initial P0 window a poor reproduction of the earlier 3s soft-wall benchmark. V2 reserves 3s for P0 and removes P2 tuple-count pruning. The smoke file is retained in local runs, and all v2 outcomes remain exploratory.
- Soft inner CEGIS loop timer: 2 seconds per stage, 6 refinement rounds; hard worker supervisor provides the actual termination guarantee
- Work statistics: primitive expression/predicate enumerations, rejected macro combinations, probe evaluations, auxiliary scoring work, shapes attempted, Z3 calls and solver time, process wall/CPU time and peak RSS
- The three stage profiles vary multiple factors together and are a *progressive mechanism evaluation*, not a factorial experiment that can attribute changes to one individual setting
- A hard worker timeout may make internal counts unavailable. Such values will be stored as null, never as zero

## Controls and interpretation

1. Solve the three public training tasks without inherited macros, formally verify, then freeze the macro inventory before accessing heldout task specifications
2. Record discovery cost (normalization, type checks, deduplication, indexing), library hash and reproducible profile hash
3. Evaluate both main arms under an identical ordered profile sequence; stop each arm on independently proved success
4. Report a complete table of all eight registered tasks plus all stress tasks; compare heldout success and *actual total costs* across stages, including inherited training and mining costs
5. Run proper-subtree vs. complete-program ablation as an explicitly exploratory diagnostic, not as fresh heldout confirmation
6. Do not claim new general intelligence, speedup, or statistically reliable transfer from this small corpus

## Known limitations to inspect

- Observational equivalence on finite probes can discard a globally different candidate
- Conditional-tree grammar does not natively express every arithmetic-over-conditional program
- Increasing AST ceilings does not guarantee that the generator reaches all expressions under those ceilings
- Z3 results establish symbolic equivalence for the supported integer theory and preconditions; runtime resource validity remains separately bounded
- A good result on composition-related `max3`/`min3` is narrow transfer evidence
- Abstractions of greater than two input arguments may increase Cartesian enumeration sharply and be dominated by time and memory exhaustion

## Methodology note

The seeded paired and blocked experimental schedule follows the general randomization/control guidance summarized by Kassis et al., *Scientific Agent Skills: A Library of Procedural Knowledge for Research Agents* (2026), https://arxiv.org/abs/2609.00065. The paper is methodological background, not evidence that CIN succeeds.

## Observed adaptive experiment v2, 2026-11-06

**Status:** Completed exploratory study, local Apple Silicon macOS. The v1 smoke was run first, and its results motivated a P0 time adjustment and removal of the P2 macro-tuple quota. Consequently, the two v2 scheduling seeds are technical replications of an already inspected corpus, **not** a blind confirmatory study.

Run command:

```bash
uv run --extra dev python -m experiments.run_adaptive_open_discovery --output runs/adaptive-open-discovery-v2-2026-11-06.json
```

Full, exact JSON evidence:
- `experiments/evidence/adaptive-open-discovery-v1-smoke-2026-11-06.json`, SHA-256 `7b3f894e3ca591dca2fad6c24fa4c3ba0cbe2662766b515064140af785f28c43`
- `experiments/evidence/adaptive-open-discovery-v2-2026-11-06.json`, SHA-256 `6aa5724f42704e060c09a5a68ac24deecf4b428b3443c3afa170e145ed1dd6da`

V2 manifest hash: `209980d895cc9eb3f0cdab69276feac82f6b3b61ef6cfc0f9e53029e5475d1fa`. Source SHA-256 (the five active implementation files, content-based): `8fbd7c779e9846a5f1c657c71d0d0ef2644b3c81181f83318a8cbf65a1397e20`. The JSON also contains the parent Git revision, host/Python details, each stage hash, ordered task schedule, proof verdict, per-stage counters and raw library inventory.

### 1. Mechanism & Complexity

- Formally prove training `max2`, `min2`, `absdiff` with no inherited library; automatically collect all type-correct integer subtrees from the resulting proved programs.
- All three training proofs succeeded. Mining visited 22 subtrees, rejected 3 types, deduplicated 14, and retained **five** distinct macros, with 0.415 ms mining wall time and a 39-unit mining cost index. No frequency, compression or utility threshold filtered the library.
- The opt-in generator now accepts higher-arity inherited macros (up to the IR's current eight-input type boundary), can include nullary macros, and records attempted macro argument tuples. Tests demonstrate actual consumption of a synthetically supplied ternary macro. **The real learned five-macro library is derived from small two-input training programs; this experiment does not demonstrate discovery and transfer of a higher-arity macro.**
- P0 preserves the original search algorithm. P1 widens term/predicate depths, constants, branch attempts and callable macro arity. P2 removes the *macro tuple-count and branch-attempt quotas* while a separate supervisor enforces the 4-second process envelope and observed 400-MiB RSS ceiling. AST node/depth and currently supported primitives remain typed finite limits. There is no claim of an unconstrained mathematical search space.
- Lazy Cartesian enumeration can still be exponential in macro arity and candidate-bank size. The wider profiles frequently expired before a worker returned its internal counters. No new heldout tasks were proved by P1 or P2 within this envelope; all positive proofs occurred at P0.

### 2. Complete Benchmark Matrix

Seed 2 detailed ledger; seed 3 independently reorders the same paired tasks and has matching final proof/timeout classifications. Each process is timed separately, including spawn overhead. `work ≥`, `Z3 ≥`, and `CPU ≥` **include only completed stage records**; when a worker was hard-killed, its unknown partial work is **not** counted as zero. `0†` means all stages were interrupted and none returned a count. RSS is the highest **sampled** worker RSS in MiB. Full primitive/subterm, predicate, tuple, probe, scoring, coverage-shape, verifier call and verifier time counters remain in JSON.

| Task | Arm | Seed 2 | Seed 3 | Completed work ≥ | Z3 calls ≥ | Z3 ms ≥ | CPU ms ≥ | Process wall ms | Peak RSS MiB |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| max2 | train, no library | PROVED | same frozen training | 1,805 | 1 | 6.8 | not separately recorded | not used in heldout envelope | not recorded |
| min2 | train, no library | PROVED | same frozen training | 1,804 | 1 | 2.3 | not separately recorded | not used in heldout envelope | not recorded |
| absdiff | train, no library | PROVED | same frozen training | 29,280 | 3 | 9.5 | not separately recorded | not used in heldout envelope | not recorded |
| max3 | no inheritance | TIMEOUT | TIMEOUT | 412,544 | 6 | 22.4 | 502.8 | 7,661.7 | 67.36 |
| max3 | open inheritance | PROVED | PROVED | 125,079 | 2 | 10.7 | 1,478.4 | 1,631.3 | 66.58 |
| min3 | no inheritance | TIMEOUT | TIMEOUT | 240,621 | 6 | 21.1 | 455.4 | 7,608.0 | 67.19 |
| min3 | open inheritance | PROVED | PROVED | 214,265 | 3 | 16.9 | 2,375.7 | 2,524.1 | 66.89 |
| clamp3 | no inheritance | PROVED | PROVED | 2,181 | 1 | 3.2 | 15.3 | 151.2 | 65.30 |
| clamp3 | open inheritance | PROVED | PROVED | 14,260 | 1 | 4.0 | 223.7 | 368.6 | 65.91 |
| median3 | no inheritance | TIMEOUT | TIMEOUT | 303,788 | 6 | 20.8 | 476.2 | 7,632.5 | 67.33 |
| median3 | open inheritance | TIMEOUT | TIMEOUT | 0† | 0† | 0† | 0† | 10,010.2 | 66.52 |
| max4 | no inheritance | TIMEOUT | TIMEOUT | 424,334 | 6 | 27.7 | 880.3 | 8,044.7 | 66.75 |
| max4 | open inheritance | TIMEOUT | TIMEOUT | 206,886 | 2 | 9.7 | 2,801.9 | 9,962.3 | 66.55 |

Heldout proof coverage: no inheritance **1/5**; open inheritance **3/5**, for **both** order seeds. The complete work lower-bound index, including the same three training costs in both arms and an additional 39 mining units for inheritance, was 1,416,357 (baseline) vs 593,418 (inheritance) for seed 2; seed 3 was 1,416,357 vs 386,532. **These are censored lower bounds** because interrupted P1/P2 processes hide their work; they cannot establish net computational efficiency. Per-task process wall totals were 31.10s (baseline) vs 24.50s (inheritance) for seed 2 and 31.17s vs 24.69s for seed 3, excluding common training, compilation/launch and mining overhead. Equal stage opportunities do not imply equal CPU instruction counts.

### 3. Isolated Ablation

The ablation is diagnostic and post-hoc, with the same seeded stage resources, and cannot serve as fresh independent heldout validation.

| Task | Whole-program-only macros | Completed work ≥ | Wall ms | Proper-subtree-only macros | Completed work ≥ | Wall ms |
| --- | --- | ---: | ---: | --- | ---: | ---: |
| max3 | PROVED | 105,629 | 1,450.6 | TIMEOUT | 457,184 | 8,149.5 |
| min3 | PROVED | 180,931 | 2,255.1 | TIMEOUT | 285,261 | 8,061.2 |

The observed inheritance advantage comes from reusing **complete proved training programs** as callable subprograms. This study does not establish that mining proper subtrees alone yields beneficial transfer.

### 4. Distractor & High-Arity Stress

Seed 2, same P0/P1/P2 schedule. The values under `Completed work ≥` are particularly incomplete when all stages time out.

| Task | Arm | Final status | Completed work ≥ | Z3 calls ≥ | CPU ms ≥ | Wall ms | Peak RSS MiB |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| clamp3 | no inheritance | PROVED | 2,181 | 1 | 15.3 | 163.7 | 65.70 |
| clamp3 | 20 distractors | PROVED | 36,325 | 1 | 699.0 | 849.5 | 65.55 |
| clamp3 | inheritance + 20 distractors | PROVED | 86,887 | 1 | 1,927.7 | 2,078.0 | 66.16 |
| sum5 | no inheritance | TIMEOUT | 3,467,490 | 5 | 1,954.1 | 9,193.1 | 66.66 |
| sum5 | 20 distractors | TIMEOUT | 0† | 0† | 0† | 10,009.7 | 45.48 |
| sum5 | inheritance + 20 distractors | TIMEOUT | 0† | 0† | 0† | 10,009.3 | 46.67 |
| sum8 | no inheritance | TIMEOUT | 115,164 | 0 | 264.8 | 7,414.6 | 46.38 |
| sum8 | 20 distractors | TIMEOUT | 0† | 0† | 0† | 10,009.3 | 45.73 |
| sum8 | inheritance + 20 distractors | TIMEOUT | 0† | 0† | 0† | 10,010.3 | 47.25 |

The harmless `clamp3` task illustrates serious distractor overhead: approximately **5.2×** longer wall time with distractors alone and **12.7×** with both inheritance and distractors, compared with the no-library stress control. The five- and eight-input additive programs remain unproved. No `MEMOUT` occurred in the recorded benchmark; the supervisor's time and memory-interruption paths have separate direct automated tests.

### 5. Failure Boundaries & Known Unsoundness

- All reported `PROVED` outcomes carry independent `SYMBOLIC_PROVED` Z3 verdicts. Successful observational matches alone never qualify as proof. Training macro *bodies* inherit the status of their source programs under their declared arity and conditions; a mined fragment does not automatically prove a new external specification.
- Finite probe-signature deduplication is **not** symbolic equivalence, so the candidate bank can discard behaviorally distinct programs; this is a search-completeness risk.
- The decision-tree skeleton and typed IR do not express every possible function. Expanding size/arity/time can fail without invalidating the mechanism.
- Timeouts are right-censored. A line reading `work ≥ 0†` is an **unavailable count**, not a cheap run. For cost comparison, full per-stage wall and peak sampled RSS are the safest available resource measurements.
- `max3` and `min3` are closely related to the max/min training programs. Neither two task-order seeds nor repeated use of the public heldout corpus establishes statistical generalization to unseen task families.
- P2 has no per-macro tuple quota, but its finite IR/type grammar and supervised process budget remain. This is a deliberately *resource-bounded open search*, and is not a proof that CIN can explore every arbitrary program.
- The current adaptive widening has **not** improved the solved-task count beyond the prior whole-program-reuse pilot. Its defensible gain is a tested experimental execution path for higher arities and progressive searches with recorded hard limits and negative evidence.

**Validation at evidence finalization:** The frozen v2 raw benchmark was executed with the exact source tree committed at `b774853`. Subsequent code-scanning and review found that RSS sampling permission errors were silently ignored and that a just-completed worker might be misclassified as timed out at the deadline. Follow-up patches fail closed with `WORKER_FAILED` and a diagnostic when RSS cannot be observed, handle a departed-process sampling race, and recheck process completion before marking a hard `TIMEOUT`. This is an error-path change **after** the frozen benchmark, so the v2 source checksum intentionally identifies the earlier `b774853` revision. The recorded benchmark observed no RSS-access errors; no claim is made that the final review patch was included in that earlier run. Separate subprocess tests cover the post-review failure path. The full test suite, format checks, schema validation and GitHub CI must be rerun on the final patch.
