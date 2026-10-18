# Research evidence and design implications

**Review date:** 2026-10-18. These are external primary academic or official technical sources; none demonstrates the CIN research hypothesis directly. Paper results should not be transferred uncritically between reinforcement learning, program synthesis and evolving source code.

## Evidence map

| Reference | Demonstrates in its own setting | Useful CIN design transfer | Important limitation / misconception |
| --- | --- | --- | --- |
| [Hillis, Co-evolving Parasites (Physica D, 1990)](https://doi.org/10.1016/0167-2789(90)90076-2) | Adversarial co-evolution of sorting-network hosts and test-case parasites outperforms static fitness evaluation; parasites prevent premature convergence by continuously generating novel challenges | Motivates CIN's paired world/organism evolution: the world specification (formal task) acts as the adversarial parasite; organism search must satisfy an independently evolving formal contract, not a fixed oracle | Hillis's parasites are unconstrained adversaries; CIN worlds must remain formally admissible (non-vacuous, independently verifiable). Adversarial pressure without admissibility gating produces unsolvable challenges. The sorting-network domain has no notion of formal proof — correctness was empirical. |
| [Bengio et al., Curriculum Learning (ICML 2009)](https://doi.org/10.1145/1553374.1553380) | Ordering training examples from easy to hard accelerates convergence and improves local minima quality in non-convex optimization; the strategy is a continuation method | Motivates the sequencing of formal worlds by admitted difficulty; a CIN curriculum that admits only feasible, increasingly challenging tasks before exposing the organism to hard ones may reduce wasted evaluation budget | Bengio et al. study gradient-based learning on neural networks; CIN uses exhaustive grammar enumeration, not gradient descent. The continuation-method analogy holds in spirit but not mechanically. "Easy" in CIN must be formally defined — not heuristic — to avoid leaking task structure to the search. |
| [Mouret & Clune, MAP-Elites (2015)](https://arxiv.org/abs/1504.04909) | Search archive preserving high-performing solutions with different behavioral descriptors | Keep diverse specialized software lineages instead of only one fitness maximum | Descriptor choices define diversity; does not generate correct software by itself |
| [Wang et al., POET (2019)](https://arxiv.org/abs/1901.01753) | Joint generation of environments and solutions, with transfers across environments | Separate world evolution and organism evolution; allow stepping-stone transfers | Demonstrated on environment/learning domains, not general code generation |
| [Real et al., AutoML-Zero (ICML 2020)](https://proceedings.mlr.press/v119/real20a.html) | Evolution of learning algorithms from basic math operations with expensive search | Model-free symbolic/evolutionary search can discover nontrivial algorithmic structures | Search space and computational resources strongly constrain discovery |
| [Dennis et al., PAIRED (NeurIPS 2020)](https://papers.neurips.cc/paper_files/paper/2020/hash/985e9a46e10005356bbaf194249f6856-Abstract.html) | Feasible difficulty-curriculum construction using regret rather than maximal failure | World fitness must consider feasibility/learnability; avoid impossible challenges | Regret in reinforcement learning is not identical to verified software correctness |
| [Ellis et al., DreamCoder (PLDI 2021)](https://doi.org/10.1145/3453483.3454080) | Inductive program synthesis and reusable library acquisition | Learn reusable abstractions from verified programs; require transfer measurements | Uses learned neural guidance; CIN cannot import that machinery under the model-free constraint |
| [Bowers et al., Stitch (POPL 2023)](https://arxiv.org/abs/2211.16605) | Extracting compact reusable abstractions from DSL program corpora | Candidate P3 abstraction mining and grammar compression | Compression does not prove semantic usefulness on withheld functions |
| [Zhang et al., Darwin Gödel Machine (2025)](https://arxiv.org/abs/2505.22954) | Empirical archive-guided self-modification with coding benchmarks | Trace meta-modification, experimental gates and archive branching | DGM expressly uses a foundation model to generate modifications; cannot be claimed as model-free precedent |
| [Beukman et al., Refining Minimax Regret (2024)](https://arxiv.org/abs/2402.12284) | Investigates learning stagnation under basic regret-based environment generation | Watch for curriculum stagnation and challenge-selection pathologies | RL-specific theory; should inspire a CIN ablation, not be used as a CIN theorem |
| [Mead et al., Dynamic Environment Generation (2026)](https://arxiv.org/abs/2601.14957) | Investigates environment-generator credit assignment/regret in UED | Treat difficulty and challenge reward quality as testable design choices | Not a software-program-synthesis evaluation |
| [cvc5 official SyGuS example](https://cvc5.github.io/docs/cvc5-1.4.2/examples/sygus-fun.html) | Declarative grammar + semantic constraints used to synthesize max/min | Optional independent formal witness checking for P2/P6 | A solver is an evaluation aid; using its witness as organism output would contaminate model-free growth claims |
| [python-jsonschema official docs](https://python-jsonschema.readthedocs.io/en/stable/validate/) | Draft 2020-12 schema validation and schema integrity checking | Validate schema evolution with `Draft202012Validator.check_schema` and `iter_errors` | Syntax validation alone cannot prove non-vacuity or intended semantics |

## Research synthesis by subsystem

### Formal synthesis, not free intelligence

AutoML-Zero and SyGuS establish feasibility of algorithm search under specified grammars, operations and objectives. They do **not** imply that a small universal seed will discover arbitrary software efficiently. CIN's first genuine question is whether *the learned abstractions and inherited policies improve later search*, not whether a MAX2 function can be found by enumeration.

### Foundational co-evolution and curriculum design

**Hillis (1990)** is the direct intellectual ancestor of CIN's paired world/organism structure. Hillis showed that static fitness functions stagnate: sorting-network populations converged to mediocre local optima when evaluated against fixed test suites, but discovered substantially better networks when evaluated against an adversarially co-evolving parasite population. The core insight — that an independently improving evaluator prevents premature convergence — maps directly onto CIN's world evolution design. The critical design difference is the admissibility gate: Hillis's parasites were unconstrained; CIN worlds must pass an independent finite-domain witness search (`admit_world`) before they can exert selection pressure. Adversarial pressure from an inadmissible world is not harder — it is unsolvable noise.

**Bengio et al. (2009)** formalize the intuition that training order matters: presenting examples in easy-to-hard sequence improves convergence and final solution quality by acting as a continuation method on a non-convex objective. In CIN terms, the admitted world sequence constitutes a curriculum. Worlds that are formally admissible but whose witness search terminates quickly are "easier" in a well-defined sense; scheduling them before structurally harder worlds reduces wasted candidate evaluations. The analogy breaks at the mechanistic level — CIN uses exhaustive typed enumeration, not gradient descent — so the continuation-method justification applies to search budget allocation, not to parameter optimization. "Easy" must be operationalized formally (e.g., witness-search depth) rather than heuristically to avoid inadvertently leaking task structure into the enumeration order.

### Co-evolution and educational pressure

POET and PAIRED motivate paired evolving agents/tasks and a useful-difficulty frontier. CIN must adapt those ideas to formally constrained function specifications. A valid task generator must avoid unsatisfiable/vacuous targets and distinguish semantic novelty from parameter randomization. A curriculum that becomes arbitrarily hard but makes no transferable capabilities is a failure.

### Library learning without neural models

DreamCoder couples induced libraries with neural recognition; CIN may reuse the **library learning concept** but not DreamCoder's pretrained/learned neural search as an unacknowledged dependency. Test Stitch-style syntactic extraction against a trivial subexpression-dedup baseline, then verify resulting macros in a distinct family, not only on the originating programs. Prefer direct in-process AST rewrites before adding e-graphs, external solvers or NumPy dependencies.

### Self-improvement and auditability

DGM motivates self-modification experiments, archival lineages and validation before promotion. Unlike DGM, CIN must generate modifications with a model-free search mechanism. Changes in proposal policy count as meta-growth only if they pass a blinded task-panel replay under equal compute, without changing verifier or scoring code.

## Research hypotheses and plausible counter-explanations

| Hypothesis | Rival explanation | Discriminating experiment |
| --- | --- | --- |
| Heredity improves future code synthesis | Descendants merely start closer to solution of the **same** task | Cross-family withheld tasks; inherited vs fresh seeds at equal budget |
| World evolution creates richer skills | Expanded numeric domains merely check stronger generalization of MAX2 | Semantic-equivalence filters and different functional task families |
| Adapted driver improves exploration | Policy simply overfits the training world set | Blind policy comparison on new task panel, paired seeds and budget |
| Diverse archives help | MAP-Elites adds storage overhead without better solutions | Same-budget quality-diversity vs single-best/archive-random controls |
| Learned abstractions matter | Frequent syntax subtrees compress but do not improve search | Macro-enabled vs macro-disabled matched tasks with learning costs charged |

## Decisions from current evidence

1. **Use simple typed search first.** There is no evidence that a neural model is necessary or permitted for CIN's current scope.
2. **Require semantics-first world novelty.** Broader numerical input ranges are robustness tests, not new task families.
3. **Insist on private, independent evaluation.** Learned code and worlds must not author their own success oracle.
4. **Do not overbuild infrastructure.** A single-process scheduler with durable local storage suffices until a particular benchmark demonstrates another need.
5. **Track negative results.** A failed attempt to show improvement is an informative research outcome; do not conceal it by changing endpoints after the fact.

## Known literature gaps

The listed publications are cross-domain inspiration, not an exhaustive survey of evolutionary program synthesis. Before implementing P3/P4, run a targeted systematic search for comparable evolutionary DSL compression and program-synthesis benchmarking, document inclusion criteria, and decide whether a classical genetic programming baseline already answers the same question. No paper above is evidence that CIN can reach self-sustaining open-ended general software engineering.
