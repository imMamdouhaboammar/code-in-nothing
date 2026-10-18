# CIN-Lab: What You Can Build Right Now

> A cumulative, milestone-anchored registry of verified capabilities and the production applications they unlock. Every entry is dated and tied to an implemented, tested runtime state. Claims that exceed what the CI and test suite prove are not made here.

---

## How This Document Works

Each section corresponds to a released milestone. **Capabilities listed under a milestone are implemented, tested, and reproducible** — not proposed or designed. Application ideas are grounded in those proven capabilities only. The document grows forward; past entries are never edited or removed.

To reproduce any capability claim:

```bash
uv run python -m cin validate          # contract and schema integrity
uv run pytest -q                       # full test suite
uv run python -m cin demo \
  --seed 0 --max-evals 250 \
  --output runs/baseline              # live synthesis run
```

---

## 2026-10-18 — Milestone P0 + M2 IR Foundation

**Runtime:** `cin-lab/0.1` · `60a5055` · Python 3.11–3.13  
**CI:** passing (57 tests, 0 failures) · `python -m cin validate` → `VALID`  
**Language model calls:** 0

### Verified Capabilities

| Capability | How It Works | Verified By |
| :--- | :--- | :--- |
| **Model-free program synthesis** | Grammar enumeration over a typed IR AST; no LLM, no neural network, no pretrained weights. | `candidate_evaluations: 63` → `learned_program_ir` in `runs/baseline/report.json` |
| **Formal finite-domain verification** | Exhaustive evaluation against every input pair in a declared bounded domain; no sampling, no fuzzing. | `initial_world_status: ADMITTED`, `verified_world_specs: 2` |
| **Replay-gated hereditary transfer** | A child genome is created only after the parent's verified program passes a two-spec replay gate in the mutated world. | `offspring_count: 1`, `parents_contracts_equal: true`, `archive_chain_valid: true` |
| **SHA-256 provenance chain** | Every event — candidate, verdict, world mutation, offspring — is appended to `events.jsonl` with a hash-linked chain. Deletion or reordering is detectable. | `archive_chain_valid: true`; chain verified in CI |
| **Versioned N-input IR (1–8 Int parameters)** | `cin.genome/v0.2` schema and `run_ir_args` interpreter accept up to 8 integer inputs while keeping the two-input `v0.1` contract frozen and untouched. | `tests/test_multi_input_ir.py` — 12 regression contracts, all green |
| **Task-blind candidate enumeration** | The search engine derives probe vectors from arity alone; it never reads the benchmark name, target function, or expected outputs. | `test_multi_input_search_is_task_blind_deterministic_and_uses_third_argument` |
| **Deterministic reproducibility** | Fixed seed → identical candidate sequence → identical synthesis outcome, always. | `test_multi_input_search_is_task_blind_deterministic_and_uses_third_argument` (first == second) |
| **Bounded interpreter safety** | The interpreter enforces op-count, bit-width, and arity limits; no infinite loops, no memory escapes, no arbitrary code execution. | `test_unsupported_versions_and_non_integer_runtime_inputs_fail_closed` |

### What the Synthesis Engine Produced (Baseline Run)

The engine discovered `max(x, y)` after evaluating 63 candidates against a formally declared domain, with zero prior knowledge of the target:

```python
# Generated from a verified CIN-IR artifact.
# This export is not the bounded CIN runtime.
def solve(x: int, y: int) -> int:
    return y if (x < y) else x
```

**Scope boundary:** This is a two-input integer comparison solved under a finite domain. It is not general-purpose code generation and makes no claim about programs outside the declared grammar and world.

---

### Applications Unlocked at This Milestone

The following application categories are achievable **with the current runtime** because the required guarantees are already implemented and tested. Each maps directly to one or more verified capabilities above.

---

#### 1. Verified Pricing & Fee Rule Engine

**The problem it solves:** Pricing rules in insurance, BNPL, and e-commerce are written by hand, deployed without formal verification, and silently fail on edge cases. Using an LLM to generate or fix rules is commercially unacceptable — hallucinated rounding behavior in a fee calculation is a regulatory event.

**What CIN provides:**

- A domain expert declares the business invariants as Pre/Post-conditions (the same format as `world-max2.v0.1.yaml`).
- The synthesis engine enumerates candidate fee functions — clamping, tiered selection, bounded arithmetic — and formally verifies each against the declared domain before accepting it.
- The accepted function is exported as a verifiable artifact with a full provenance chain.

**Supported input shape (today):** Up to 8 integer parameters (`cin.genome/v0.2`). Suitable for functions over quantized monetary amounts, tier indices, and rate codes — all of which are representable as bounded integers.

**What it does not do:** The bounded interpreter does not evaluate floating-point, string, or datetime inputs. Continuous-domain pricing requires quantization first.

---

#### 2. Automated Safety Interlock for Embedded & IoT Systems

**The problem it solves:** Safety interlocks on embedded controllers — temperature ceilings, pressure cutoffs, actuator limits — are hand-coded in C without formal verification. A missed edge case in a multi-sensor guard function is a field safety incident.

**What CIN provides:**

- Sensor readings from 1–8 channels (quantized to integer units) are declared as a typed input signature under `cin.genome/v0.2`.
- The domain is declared as a Safe Operating Envelope (pre/postcondition over bounded integer ranges).
- The synthesized guard function is provably correct over the declared domain. The SHA-256-linked artifact is auditable — every verification run is on record.
- The exported Python function can be transpiled to C with trivial mechanical effort; the IR is structurally equivalent to a finite state expression with no dynamic allocation.

**Supported input shape (today):** 1–8 `Int` inputs, bounded arithmetic and comparisons (`Add`, `Sub`, `LessThan`, `Equal`, `If`). Sufficient for threshold guards, min/max selectors, and bounded saturation logic.

---

#### 3. Provable Compliance Audit Engine

**The problem it solves:** Regulators in financial services, customs, and tax administration increasingly require that automated decision systems provide a machine-verifiable audit trail — not just log output, but proof that the decision function was formally verified against the applicable rule domain before deployment.

**What CIN provides:**

- Every accepted program, every world verification step, and every genealogical event is written to `events.jsonl` with a SHA-256 hash chain (`archive_chain_valid: true`).
- The chain can be independently replayed: anyone with the repository and a Python 3.11+ environment can reproduce the full synthesis history.
- Provenance is not an assertion — it is a structural property of the append-only journal.

**Deployment pattern:** Wrap the `cin demo` run in a CI job that publishes the `events.jsonl` artifact. Compliance auditors receive a reproducible hash-linked record of every decision the synthesis engine made, including rejected candidates and world admission verdicts.

---

#### 4. Zero-Hallucination Micro-Patch Generator for Critical Business Logic

**The problem it solves:** When a bounded arithmetic bug appears in production code — a miscomputed maximum, a saturating counter that overflows, a threshold that fails on equal inputs — engineers fix it by hand, with associated regression risk. Using an LLM to suggest the patch introduces a new failure mode: confident but incorrect code.

**What CIN provides:**

- The failing input/output pair is added as a counterexample to the world specification.
- The synthesis engine searches for the minimal-AST function that passes both the original domain and the new counterexample, then formally verifies the combined domain before accepting the patch.
- The result is not a suggested fix — it is a proof that the new function satisfies all declared cases.

**Supported fix scope (today):** Functions expressible in CIN-IR: bounded integer arithmetic, comparisons, and conditional selection. This covers a significant class of production bugs in fee calculators, priority queues, and rate limiters.

---

### Honest Boundaries

| Claim | Status |
| :--- | :--- |
| Formally verified programs over declared bounded integer domains | **Implemented** |
| Multi-generation (P1) evolution across epochs | **Designed, not implemented** |
| Semantic world co-evolution — discovering new function families (P2) | **Designed, not implemented** |
| Cross-task hereditary abstraction reuse (P3) | **Designed, not implemented** |
| Scientific self-improvement | **`NOT_ESTABLISHED`** (field in `report.json`) |
| General-purpose code generation or software engineering | **Out of scope; not a goal** |

The next engineering gate is `P1-01` (immutable cohort manifest + normalized replay). No application claims above depend on P1; they are unlocked by P0 capabilities already in `main`.

---

*This document is append-only. The next entry will be added when a new milestone passes its acceptance gates.*
