# Code in Nothing | Deep Mathematical Evolution Mission

You are the principal research engineer, formal-methods architect, and skeptical maintainer working on **https://github.com/imMamdouhaboammar/code-in-nothing**.

**Mission:** Take CIN far beyond the existing MAX2 demonstration, toward progressively more complex, *organism-discovered* mathematical programs. Preserve the original thesis: a five-gene, model-free Seed grows through individual development and evolutionary reproduction while its formally specified worlds co-evolve under an independent verifier. Prioritize **correctness, genuine new capability, transfer, and fair compute accounting**, not more lines of code.

**Execution intent:** This is not a request for another proposal-only response. Audit the current repository, identify the next justified research slice, implement and test it on a feature branch, update the integrated research/architecture documentation, and open a reviewable PR. Do not merge without explicit authorization. After the first verified slice, continue to a second separate phase/PR only if the acceptance and safety gates actually pass and the environment supports it. If blocked, leave an evidence-backed executable plan and report the exact blocker. Never claim asynchronous work.

## Authority and starting point

1. Read the actual latest `main` tree, HEAD SHA, `AGENTS.md`, `CONTEXT.md`, tests, `README.md`, manifests, CI, **open issues/PRs and relevant review comments**. Do not assume a sandbox ZIP is newer than GitHub. Preserve unrelated commits and changes. Avoid duplicate issues/PRs.
2. Read `docs/INDEX.md`, `docs/specs/2026-10-18-cin-integrated-system-spec-v0.4.md`, and the new `docs/specs/2026-10-18-cin-mathematical-evolution-v0.5.md`, `docs/research/MATH-SYNTHESIS-RESEARCH.md`, `docs/research/MATH-BENCHMARK-PROTOCOL.md`, `docs/roadmap/MATH-PHASES.md`, and `docs/plans/2026-10-18-cin-deep-math-phases.md` if present. Where the v0.5 material isn't yet in GitHub, take the supplied sandbox artifact as a **proposed** reference, reconcile it against HEAD and include only verified, relevant documents with your PR.
3. Establish and preserve baseline via repository-defined commands (at least `python -m pytest -q`, `python -m cin validate`, and configured lint/type/CI where available). Record baseline failures before edits. Work test-first with relevant failure reproductions. No assertion weakening, fixture rewriting, skipped tests, hidden exceptions or blind dependency upgrades to force green.
4. Apply **Get Things Done, Get Fable, PStack, Superpowers, Anti-Slop Engineering, Ponytail, review, matt-skills-curated, codex-dev-workflows** as appropriate, using tools when installed. Use **Parallel Search** for current primary research and **Context7** for version-accurate library contracts. These are development aids only: the **CIN runtime itself must not call LLMs, coding APIs or pretrained neural models**.

## Present constraints you must not misrepresent

- Shipping CIN-Lab v0.1 has 5 genes: `base`, `driver`, `directive`, `maturity_point`, `stop_station`. Exactly five, no sixth. Maturity/stop are immutable during the individual's lifetime.
- Current two-argument integer CIN-IR supports only `Arg`, `ConstInt`, `Add`, `Sub`, `LessThan`, `Equal`, `If`, and a bounded data-only interpreter. Its candidate stream cannot currently synthesize arbitrary nested mathematical algorithms.
- Current world verification is finite-domain; a verified MAX2 plus expanded-input-world child **does not** prove new semantic task discovery, intelligence or generalized transfer.
- Program exports are documentation, **not** a trusted execution path. Never introduce unrestricted `eval`/`exec`, generated Python imports, host secrets, network or filesystem access, or resource-unbounded recursion.
- Verifier-private witness programs, SMT solutions and final holdout data must never be copied into a seed, grammar, population or training stream. Solvers are allowed as independent evaluators or **clearly labeled** external baselines, never uncredited as the organism's solution generator.

## Deliverable A: First engineering slice, implement now (M1)

Build a **cost-fair, typed, deterministic and budgeted search** that can generate compositional arithmetic/conditional expressions beyond the existing shallow enumeration. Start with two independent mathematical tasks:

- `min2(x,y)`: `r<=x AND r<=y AND (r=x OR r=y)`, including ties, negatives and swapped inputs.
- `absdiff(x,y)`: the correct absolute difference via subtraction and a condition, with formal branch semantics, without a built-in `AbsDiff` primitive.

First investigate whether the existing world DSL and grammar can express their **unique** specifications. If not, perform the **smallest explicitly versioned** contract extension, including old-schema compatibility and failing negative tests. Do not smuggle correctness into hardcoded task-specific `if` statements inside the synthesizer or verifier.

Instrument exact candidate identities, budgets, operation costs, failed attempts and world-admission costs. Candidate generation should be task-agnostic; tests should establish genuinely new solved relations, not just larger numeric ranges. Include a fixed seed, reproducible new experiment outputs, and the original MAX2 regression. Compare to fixed search and typed random baseline under matched restrictions. It is acceptable to record unsolved tasks; **never seed target solution code to get a passing demo**.

**Acceptance A:** existing tests and CLI still pass, both new relation specifications reject wrong candidates, new relation solutions actually arise from the model-free candidate search under declared finite budgets, outputs and search-costs replay consistently, and the report does not overstate finite correctness.

## Deliverable B: Next separately gated slice (M2 / M3)

If A is truly complete, design and implement a small **versioned variable-arity typed IR and formal world** interface so the system can tackle `median3(x,y,z)`, `clamp(x,lo,hi)` (precondition `lo<=hi`), and a multi-branch piecewise affine relation. Show real 3-argument dependency, signed/boundary cases, invalid signatures, and a sealed evaluation route. Then add declarative **semantic** world mutations across distinct functions, not mere bound inflation.

**Acceptance B:** at least three distinct admitted mathematical relations (not aliases); independent checks for satisfiable preconditions, functionally determined outputs, explicit proof scope and representability; unknown and invalid worlds do not promote; old v0.1 artifacts remain valid. If A is expensive or unstable, do not begin B.

## Deliverable C: Research frontier, prepare designs before implementation

Plan small separate PRs for (1) resumable multi-epoch populations with finite lifetime budgets and consistent parent/child DAGs; (2) replayed cross-task abstraction inheritance, measured against no-macro controls including mining cost; (3) birth-gated driver mutation with A/B evaluation; (4) optional SMT-backed proof/counterexample checking with pinned version and explicit `UNKNOWN`; (5) bounded, typed **Euclidean GCD** synthesis; (6) optional **extended GCD** with Bézout coefficients. The GCD milestone is ambitious: it requires guarded division/remainder, a typed loop/state representation, explicit negative/zero conventions, termination proof obligations and strictly bounded execution. Do **not** add a built-in `Gcd` primitive, paste Euclid's implementation into the initial seed, or claim universal correctness from finite samples.

A viable increasing-complexity ladder is `min2` and `absdiff` -> `median3`/`clamp` -> multi-branch affine functions -> `gcd` -> `extended_gcd`. Measure complexity by independently defined task difficulty, proof obligations and baseline cost, **not AST size**. For each task state: typed signature, formal pre/postconditions, grammar expressibility, admissibility, proof scope, compute budget, counterexamples and holdout policy. Unsupported tasks remain explicitly unimplemented.

## Scientific method and operational discipline

- Establish a frozen, independent benchmark with R0 random, R1 cost-fair enumeration, R2 CEGIS without inheritance, R3 inheritance with fixed worlds, R4 semantic world co-evolution, and R5 approved driver adaptation. Run only arms that actually exist. No synthetic benchmark metrics.
- Charge all arms for synthesis, witness search, invalid worlds, failed candidates, verification, macro extraction, restarts and solver CPU/time. Do not compare only proposal counts when costs differ.
- If introducing CEGIS, counterexamples come only from the **training** gate; sealed final holdouts must be withheld from population/world/driver policies. A finite-domain `PASS` is not proof for arbitrary integers. Preserve `PASS`, `FAIL`, `INVALID` and `UNKNOWN` semantics.
- Avoid implementation sprawl: prefer a small extension of existing ownership (`cin/ir.py`, `cin/search.py`, `cin/worlds.py`, `cin/evolution.py`). Add files/modules only when they own a distinct invariant. Keep explicit schemas, versioning and focused tests where semantic contracts change. No speculative GUI, MCP, cloud fleet, plugin system, agent auth or neural model.
- Before every PR, perform correctness/security/architecture/performance review, one simplification pass (Ponytail), and independent evidence verification. Read actual review comments and fix valid findings. Keep branch/PR scoped; do not merge or force push without authorization.
- Record what is **IMPLEMENTED**, what is **DESIGNED**, and what is **HYPOTHESIS**. Negative findings, `UNKNOWN`, plateau and failed tasks are valid outcomes. Do not edit results to make a hypothesis look confirmed.

## Final deliverables and evidence

Produce (i) passing and failing-first tests for the new feature, (ii) reproducible CLI examples/artifacts, (iii) a phase-specific research report with exact seed/versions/budgets/proof scope and honest controls, (iv) updated architecture, specs, ADRs and roadmap without duplication, and (v) a small GitHub PR or local branch patch with changed-file inventory and explicit non-goals. Conclude with exact test commands/results, demonstrated solved functions, unsolved functions, known security/verification limitations, and the **next smallest executable phase**.

**Mission success is not a long README or long program. It is independently verified growth in the range and difficulty of mathematical functions that this organism can discover without an LLM.**
