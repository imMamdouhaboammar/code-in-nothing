# CIN v0.4 design and repository review

**Date:** 2026-10-18  
**Review scope:** Current v0.1 code, shipping schemas, CLI, pilot results and proposed v0.4 documentation. No runtime algorithm changes were authorized for this system-design phase.

## Grounded baseline

- `python -m pytest -q` passed **35 tests** at the start of this documentation phase.
- `python -m cin validate` returned VALID for the example seed/world.
- `experiments/sample-full/report.json` records 85 candidate proposals, 1 accepted functional capability, 2 world specs of the same task, 1 offspring, `NOT_EVALUATED` maturity and `NOT_RUN` sealed transfer.
- The source tree has no Git metadata in the current sandbox. This is not a GitHub PR or a code-merge review.

## Architecture review findings

| Severity | Evidence from code | Assessment | Planned disposition |
| --- | --- | --- | --- |
| High (research validity) | `cin/evolution.py` uses `expand_domain()` to create the second world; child creation requires two spec hashes | Two spec hashes do not establish two semantic capabilities or cross-task macro reuse | P2 novelty gate and P3 inheritance+macro distinction; report v0.1 as mechanism only |
| High (research validity) | `cin/evolution.py` candidate budget and `admit_world()` private witness search are accounted separately | Published proposal count undercounts total search cost if interpreted as all-compute cost | P1 governor accounting; P5 matched full-operation budget |
| High (future security) | `cin/ir.py` executes data-only IR inside normal host Python process | Closed opcode set is useful, but runtime has no OS isolation for arbitrary source | Keep arbitrary source banned; P6 OS worker before expanding execution |
| Medium | `cin/evolution.py` performs one search/offspring cycle; YAML declares epochs, plateau and policy adaptation | Declared driver/stop settings outrun implemented scheduler behavior | P1 multi-epoch scheduler; P4 actual policy learning; docs explicitly distinguish status |
| Medium | `cin/worlds.py` checks postcondition *mentions* `result` and admits private grammar witness | Syntactic mention does not establish unique function or general semantic novelty | P2 normalize and distinguish task relations before novel-family claims |
| Medium | `cin/archive.py` uses append-only JSONL in one process, SHA-256 chain, no checkpoint | No persistent crash/restart or privileged-host tamper resistance | P1 transactional checkpoints and explicit log limitations |
| Medium | `cin/worlds.py` exhaustive finite-domain checking | PASS is only domain-relative, not a proof over unbounded Int values | Version proof scope; optional solver only when evidence justifies |
| Low | `examples/seed-genome.v0.1.yaml` and world header previously said illustrative/design-only | Misleading now that exact examples power the runnable demo | Correct header comment, preserve data and schema IDs |
| Low | Legacy v0.3 design originally said nothing had been implemented | Conflicts with current v0.1 code | Add historical note pointing to v0.4/runtime map |

No source change is proposed solely to silence these findings. Each risk is mapped to a separately testable milestone in [PHASES.md](../roadmap/PHASES.md).

## Review against five criteria

1. **Correctness:** No promise of distinct task learning, self-improving policies, infinite intelligence or universal proofs. Proposed APIs clearly labeled and traced to existing modules.
2. **Readability:** One [documentation index](../INDEX.md), one integrated spec, separate detailed runtime / protocol / research ownership docs, and a pure [domain glossary](../../CONTEXT.md).
3. **Architecture:** One owner for each promotion/admission authority; no premature microservices, cloud deployment or extra gene.
4. **Security:** Generator/verifier boundary explicit. No future arbitrary code execution without an OS sandbox. SHA-256 logs not presented as signatures.
5. **Performance:** Full admission and replay costs included in proposed fair comparisons. No performance or scientific superiority claims invented.

## Decisions intentionally deferred

- Which durable store wins: stdlib SQLite vs a correctly transactional single-writer journal, decided from P1 crash tests.
- Whether cvc5/SMT integration adds enough value beyond finite-domain checking to justify a dependency.
- Whether an abstraction learner needs e-graphs; first compare simple AST-level macro extraction against baseline.
- Whether driver policy needs NumPy; start with simple transparent deterministic policies.
- Whether a new CIN-IR domain is needed for useful specialization; start with existing integer semantics.

## Exit review

For this phase, the deliverable is **integrated and internally navigable documentation**, not an implemented v0.4 engine. Run tests and link checks after edits, inspect ZIP structure, and report findings honestly. Proceed with P1 only as a future implementation task after review of design and evidence.
