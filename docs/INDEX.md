# CIN documentation index

**Current date:** 2026-10-18  
**Runtime:** CIN-Lab package v0.1 includes M1 (`ca65b95`) and the additive, tested M2 N-input IR/search foundation (merged PR #2 at `981bffb`). This is not full M2 discovery or a runtime v0.6 release.  
**Integrated design:** v0.4 baseline and v0.5 math design. **v0.6** defines the evidence-gated research/engineering continuation; it is not a runtime version.

This is the starting point for developers, reviewers and researchers. **The executable source and existing tests are the authority on current behavior.** The v0.4 design governs proposed work only after an implementation phase explicitly adopts its contracts.

| Read | Purpose | Authority |
| --- | --- | --- |
| [Verified mathematical evolution v0.6](specs/2026-10-18-cin-verified-mathematical-evolution-v0.6.md) | Integrated architecture, measured-cost contract, maturity ledger, falsifiable M1–M6 phase gates | Proposed v0.6 research program, not runtime release |
| [Integrated specification](specs/2026-10-18-cin-integrated-system-spec-v0.4.md) | Goals, invariants, interfaces, transition model, proposed acceptance | Normative future design |
| [Mathematical evolution v0.5](specs/2026-10-18-cin-mathematical-evolution-v0.5.md) | Integrated deeper mathematical synthesis/verification design | Proposed, not implemented |
| [Math synthesis research](research/MATH-SYNTHESIS-RESEARCH.md) | Primary evidence, version traps and research hypotheses | Research interpretation |
| [Math benchmark protocol](research/MATH-BENCHMARK-PROTOCOL.md) | Formal task ladder, leakage/baselines, proof scope | Preregistration template |
| [Math gates](roadmap/MATH-PHASES.md) | M0-M8 dependency gates and honest deliverables | Proposed roadmap |
| [Math development plan](plans/2026-10-18-cin-deep-math-phases.md) | Detailed reviewable PR slices | Implementation plan |
| [Deep math coding-agent prompt](prompts/DEEP-MATH-CODING-AGENT.md) | Full reusable GitHub continuation prompt | Agent instructions; no execution implied |
| [ADR 0004](adr/0004-formal-math-complexity-and-proof-separation.md) | Formal math / verifier separation trade-off | Proposed architectural decision |
| [Phase P1 research & architecture](research/2026-10-18-cin-p1-research-and-architecture.md) | Discovery, IR search relevance, and 3-vector architecture evaluation | Research & architectural evaluation |
| [System architecture](architecture/SYSTEM.md) | Components, ownership, data flow, state and deployment | Architecture proposal plus runtime map |
| [Evolution protocol](architecture/EVOLUTION.md) | Individual growth, world evolution, reproduction, maturity, stop | Protocol proposal |
| [Contracts](architecture/CONTRACTS.md) | Existing v0.1 functions and future APIs, status semantics, compatibility | Versioned interface contract |
| [Security and operations](architecture/SECURITY.md) | Trust boundaries, governor, sandbox and evidence handling | Risk controls and phase prerequisites |
| [Research map](research/LITERATURE.md) | Primary sources, what they support, what they do not | Evidence synthesis |
| [Experimental protocol](research/EXPERIMENTS.md) | Hypotheses, baselines, budget accounting, holdout and metrics | Pre-registration proposal |
| [Phases and gates](roadmap/PHASES.md) | Delivery sequence, stop/go criteria and explicit non-goals | Product and research roadmap |
| [Next implementation plan](plans/2026-10-18-cin-next-phases.md) | Reviewable engineering steps and focused tests | Plan; work not executed |
| [Phase P1 research & architecture](research/2026-10-18-cin-p1-research-and-architecture.md) | Discovery, IR search relevance, and 3-vector architecture evaluation | Research & architectural evaluation |
| [Review ledger](reviews/2026-10-18-design-review.md) | Evidence, correctness gaps, contradictions and decisions | Repository inspection |
| [Domain vocabulary](../CONTEXT.md) | Unambiguous naming without implementation details | Canonical terminology |
| [ADRs](adr/0001-isolated-verification.md) | Trade-offs considered and frozen architectural decisions | Decision history |
| [Existing v0.3 spec](specs/2026-10-18-cin-technical-design.md) | Historical original design and original pilot hypotheses | Superseded where v0.4 is explicit |
| [Original v0.1 implementation plan](plans/2026-10-18-cin-lab-implementation.md) | Historical prototype plan, not an active task tracker | Historical |
| [Pilot results](../experiments/RESULTS.md) | Actual observed initial and frozen-world runs | Observed experiment evidence |

## Documentation rules

1. A change in active behavior requires code/tests changes, not only prose.
2. Proposed module names, APIs and performance targets are labeled **DESIGNED** until implemented and verified.
3. Bounded domain PASS does not imply universal correctness or held-out generalization.
4. A world-domain expansion is not a distinct functional task and cannot meet a two-family transfer requirement.
5. Preserve current schema IDs (`cin.genome/v0.1`, `cin.world/v0.1`) and CLI compatibility unless a phase explicitly versions and tests replacements.
6. External papers motivate experiments. They do not constitute evidence that CIN already performs those experiments.
