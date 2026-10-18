# CIN mathematical evolution benchmark contract v0.5

**Status:** Pre-registration *template*, not a frozen or executed benchmark. **Canonical spec:** [mathematical evolution v0.5](../specs/2026-10-18-cin-mathematical-evolution-v0.5.md).

## Task registry and formal semantics

Each task must have a mathematical specification independent of any candidate program. Expected sample input-output values are smoke tests only; they are not exhaustive proof. Do not make all inputs or solution code available to the organism.

| ID | Function/signature | Unique specification and edge cases | Version gate |
| --- | --- | --- | --- |
| CIN-MATH-01 | `min2(x:Int,y:Int)->Int` | `r<=x ∧ r<=y ∧ (r=x ∨ r=y)`; ties and signs | existing binary IR |
| CIN-MATH-02 | `absdiff(x:Int,y:Int)->Int` | `(x>=y ∧ r=x-y) ∨ (x<y ∧ r=y-x)`; ± symmetry, zeros | deeper conditional typed search |
| CIN-MATH-03 | `median3(x:Int,y:Int,z:Int)->Int` | `r` is middle element of the sorted multiset `[x,y,z]`, including repeated values | 3-argument signature |
| CIN-MATH-04 | `clamp(x:Int,lo:Int,hi:Int)->Int` | precondition `lo<=hi`; `r=lo` if below; `r=hi` if above; else `r=x` | 3-argument signature |
| CIN-MATH-05 | `three_zone(x:Int,y:Int)->Int` | piecewise: if `x<0`, `r=x+y`; else if `x<=y`, `r=x-y`; else `r=y-x`; boundary-tested | nested conditionals |
| CIN-MATH-06 | `gcd(a:Int,b:Int)->Int` | `r=gcd(abs(a),abs(b))`, nonnegative, `gcd(0,0)=0`, divisor/greatestness | versioned modulo and bounded iteration |
| CIN-MATH-07 | `egcd(a:Int,b:Int)->(Int,Int,Int)` | `(g,s,t)` with `s*a+t*b=g=gcd(a,b)`; deterministic tie choice not needed if multiple valid triples | typed outputs + loop invariant |

### Complexity and eligibility controls

- The benchmark registry maps each task to a permitted **public** grammar version and fixed seed/generation budget; do not add operators that directly implement the target relation (`Gcd`, `Median`, `Clamp` as a primitive).
- Distinct functions are grouped by **mathematical relation**, not by world ID or numeric range. Negative values, tie cases, zeros, guards and overflow/bitwidth policy are part of the contract.
- New generated formal worlds may vary parameters of *public relation templates* but can't mutate the sealed holdout.
- On **finite domains**, exact proof scope includes a published list/definition of input bounds, precondition satisfiability, integer bitwidth and permitted output range or equivalent proof-backed uniqueness.
- `UNKNOWN`, resource exceeded, verifier exceptions and inadmissible relation must remain separate from `FAIL` and `PASS`.

## Research arms and shared costs

| Arm | Organism changes | World changes | Inheritance | Search policy |
| --- | --- | --- | --- | --- |
| R0 | typed random candidate sampling | fixed | no | random |
| R1 | cost-fair typed enumeration | fixed | no | fixed |
| R2 | typed CEGIS search | fixed | no | fixed |
| R3 | CEGIS with macros | fixed | yes | fixed |
| R4 | CEGIS with macros | semantically evolving | yes | fixed |
| R5 | CEGIS with macros | semantically evolving | yes | birth-gated adapted |

**Fairness:** Freeze all arms' grammar, training/holdout split, proof semantics, compute cap, solver version and hardware class within a study. Account for world-admission cost, rejected worlds, macro mining, training verification, solver time and run retries. R5 is an ablation arm only after prior phases exist. Reject post-hoc changes to tasks, random seeds or outcome definitions.

## Pre-registration manifest schema (design, not shipping API)

```yaml
study_id: cin-math-study-v1
status: proposed
cohort_source_ref: "git-commit-sha-at-freeze"
protocol_version: cin.research.math/v1
ir_version: cin.ir/v0.2
world_version: cin.world/v0.2
proof_semantics_version: "versioned-semantic-hash"
seeds: [0, 1, 2, 3, 4] # engineering pilot only; not statistical-power claim
arms: [R0, R1, R2, R3, R4, R5]
primary: "distinct_hidden_tasks_solved_per_total_verified_compute"
secondary: ["compute_to_first_pass", "cross_task_macro_reuse", "invalid_world_rate"]
sealed_holdout_manifest_sha256: "to-be-pinned-at-study-freeze"
compute_budget_policy: "identical per arm; exact metering contract must be finalized"
```

The fields above are **design placeholders**, not valid run artifacts; no comparative study is authorized until the manifest contains real pinned hashes, budgets and frozen task instances. Keep pilot studies distinct from confirmatory studies.

## Minimal engineering demonstrations (not scientific evidence)

- `min2` should solve finite signed values with ties and not alias `max2`.
- `absdiff` should solve negative and swapped inputs; naive `x-y` fails negative results.
- `median3` should handle all six permutations and duplicates; program must actually take three arguments.
- `clamp` should reject malformed `lo>hi` world inputs or mark them excluded by a declared precondition, never return an unverified result.
- `three_zone` should exercise all branches and branch boundaries.
- `gcd` must handle (0,0), zero with nonzero, negatives and co-primes; no `Gcd` helper; interpreter step budgets enforced.
- `egcd` must check Bézout coefficients and gcd normalization; do not pass based on a single arbitrary reference coefficient pair.

## Leakage tests

1. Inject an `oracle_code` field into a world proposal and verify rejection.
2. Attempt to pull witness/source/counterexample records from the sealed verifier context and verify read rejection.
3. Swap an artifact/program hash after approval and verify inheritance rejection.
4. Call `UNKNOWN` a pass and verify admission/maturity rejection.
5. Disable the macro library and compare full discovery cost on identical frozen task sets.
6. Present MAX2 with a wider `x,y` range as a new family and verify it remains one semantic task.
7. Trigger precondition-true/no-result constraint or multiple valid results and verify world admission rejects/returns explicit relational policy.

## Result protocol

Release a manifest, raw evidence references, code and domain/grammar hashes, holdout protocol digest, budget table and complete failures. Report medians/distributions by independent cohort, with uncertainty intervals when appropriately powered. Distinguish `FINITE_EXHAUSTIVE` from any universal statement. Never publish fake improvement percentages or unsupported complexity claims.
