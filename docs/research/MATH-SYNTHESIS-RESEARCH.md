# Model-free mathematical synthesis: research-to-design evidence map

**Date:** 2026-10-18. **Status:** Literature review and engineering interpretation, not CIN experimental results. **Design:** [v0.5](../specs/2026-10-18-cin-mathematical-evolution-v0.5.md). Prioritize primary research and official project documentation. Confirm external solver and dependency versions against the target `pyproject.toml`/lockfile before introducing an adapter.

| Source | Established observation | What CIN can test | Incorrect inference to avoid |
| --- | --- | --- | --- |
| [Alur et al., Syntax-Guided Synthesis](https://web.eecs.umich.edu/~weimerw/2022-481F/readings/Alur13.pdf); [SyGuS definition](https://sygus-org.github.io/) | SyGuS separates a grammatical search space from semantic constraints | Formally specify a constrained program grammar and check candidates | Grammar expressivity guarantees finding all desired algorithms under finite budget |
| [SyGuS-Comp 2018](https://arxiv.org/abs/1904.07146) | Publicly analyzed benchmarks and systems for program synthesis | Derive comparative task families and use solver-baseline controls | SyGuS competition ranking transfers directly to CIN's research objective |
| [cvc5 project](https://github.com/cvc5/cvc5); [Python SyGuS example](https://github.com/cvc5/cvc5/blob/main/examples/api/python/sygus-fun.py) | SMT solving and SyGuS APIs can support constraint-based synthesis and proof queries | Use solver as independent counterexample/proof oracle, or fully credited baseline | cvc5-generated implementation is organically evolved by CIN |
| [cvc5 Pythonic interface](https://github.com/cvc5/cvc5/blob/main/docs/api/python/pythonic/pythonic.rst) | The Pythonic interface documents missing SyGuS support | If needed, use tested base `cvc5.Solver` APIs, not guessed Pythonic equivalents | Every cvc5 Python API wrapper exposes the same features |
| [Frankel et al., counterexample-guided E-graphs (2025)](https://www.pure.ed.ac.uk/ws/portalfiles/portal/564446902/FrankelEtalSMT2025Syntax-GuidedSynthesis.pdf) | Explores synthesis-time e-graph enumeration against equivalence blow-up | Measure observational duplicates, then try e-graph pruning as controlled ablation | Equality on a sampled set proves equivalence for all integers |
| [egg equality saturation](https://arxiv.org/abs/2004.03082) | E-graphs compactly represent equal expressions under rewrite systems | Optional post-baseline canonical simplification | Rewriting is automatically sound for all arithmetic semantics or resource bounds |
| [DreamCoder](https://people.csail.mit.edu/asolar/papers/EllisWNSMHCST21.pdf) | Learns reusable program abstractions, with neural guidance in its complete architecture | Isolate and test a *symbolic-only* library learning step | CIN may reuse DreamCoder's performance claims without its neural/search components |
| [Stitch](https://github.com/mlb2251/stitch) | Reusable program abstraction discovery via compression | Small macro-library baseline before bespoke abstraction mining | Source compression alone equals cross-task transfer gain |
| [POET](https://arxiv.org/abs/1901.01753) | Evolves environments jointly with adapted agent solutions | Typed world co-evolution with controlled admission | Harder numeric ranges are necessarily new semantic families |
| [PAIRED](https://arxiv.org/abs/2012.02096) | Regret-related adversarial environment construction in RL | Compare challenge productivity against trivial impossible-world generation | Adversarially generated tasks are automatically valid or worth learning |
| [MAP-Elites](https://arxiv.org/abs/1504.04909) | Quality-diversity archives cover multiple high-performing behavioral niches | Keep diverse proven program behaviors instead of selecting only largest score | Arbitrary AST hashes represent meaningful functional diversity |
| [AutoML-Zero](https://proceedings.mlr.press/v119/real20a.html) | Evolutionary search over primitive operations can discover bounded ML algorithm structures | Test model-free search policy baselines for small mathematical DSL | A small successful search proves open-ended general programming intelligence |

## Synthesis recommendations, in research order

1. **Typed cost-fair enumeration** first: instrument novelty/dedup and compare against the existing candidate stream. Measure full cost; don't introduce a framework yet.
2. **CEGIS training feedback**, but only after formal training/holdout split. Cached observational signatures are a search heuristic, not a correctness proof.
3. **Reusable macros** from verified solutions. Reject abstractions whose dependency chain fails replay or whose savings vanish after the mining cost is counted.
4. **World transformations** must alter the mathematical relation itself and pass uniqueness/feasibility checks. Do not use a stochastic world generator that merely randomizes problem labels.
5. **Solver proof checks** for linear integer arithmetic are plausible after the basic grammar handles median/clamp; modular arithmetic, loops and termination have distinct obligations and cannot be treated as LIA tautologies.
6. **E-graphs, SMT adapters, stochastic policy adaptation** belong behind measurements demonstrating necessity and independent ablations.

## Critical open questions (experiments decide)

- How many candidates become observational duplicates on retained training sets, and are expensive equivalence checks worth it?
- Does semantic world novelty produce useful curriculum progression rather than unsolvable challenges?
- Do verified macros accelerate a *new task family* or only replay their source task?
- Can progressively deeper programs be searched under finite total budgets without losing simple-task performance?
- Do GCD/extended-GCD goals require changing representation and evolution mechanism rather than merely raising `max_ast_depth`?

## Correctness and limitations

Exhaustive enumeration of a *declared finite domain* is deterministic evidence for that finite domain. For infinite integer domains, proof requires a sound encoding and solver/theorem result under explicit assumptions; timeouts and solver `UNKNOWN` are not success. For loop algorithms, partial function equivalence isn't enough: resource safety and termination must be separately established. None of the cited sources proves this project can meet the proposed targets, and benchmark results must not be copied across different grammar/proof assumptions.
