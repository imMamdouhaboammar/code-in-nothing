# CIN-Lab Prototype Implementation Plan

> **For agentic workers:** Use the host's available task-by-task implementation workflow. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Run a deterministic, model-free vertical slice from Seed Genome to typed mutations, independently checked functional growth, world admission, offspring lineage, and archived termination.

**Architecture:** Python package with immutable typed expression trees, total bounded interpreter, JSON-Schema-validated genome/world descriptors, bounded-domain exhaustive verifier, and deterministic evolutionary runner. A formal-world DSL is data only; an independent enumerator discovers potential world witnesses and never passes them to the organism. Evidence is append-only JSONL, with hashed artifacts and explicit experimental limitations.

**Tech Stack:** Python 3.11+, PyYAML, jsonschema, pytest; stdlib hashlib, json, itertools, dataclasses, argparse. No models, solvers, network or arbitrary generated-code execution.

## Global Constraints

Exactly the five approved genes; no sixth gene; maturity/stop contracts immutable during life; candidate execution restricted to typed CIN-IR; independent verification and strict per-organism budget; UNKNOWN never counts as success; code lineage tied to content hashes. Bounded exhaustive checking is a domain-relative guarantee, not universal proof for unbounded integers. No hidden benchmark results in growth feedback. The v0.3 long-horizon scientific metrics are not claimed for this pilot.

---

### Task 1: Validated genome, typed IR and evaluator

**Files:** `cin/contracts.py`, `cin/ir.py`, `tests/test_contracts.py`, `tests/test_ir.py`

**Interfaces:** `load_genome(path) -> Genome`; `load_world(path) -> World`; `check_tree(expr, genome) -> str`; `run_ir(expr,x,y,limits) -> int`; `canonical_hash(value) -> str`.

- [ ] **Step 1: Add focused failing tests:** six gene rejected; incorrect types/unknown op rejected; x/y outputs deterministic; If non-selected branch lazy; depth/size/op/bit limits enforced.
- [ ] **Step 2: Verify relevant failure:** `pytest -q tests/test_contracts.py tests/test_ir.py` fails on missing modules.
- [ ] **Step 3: Implement:** exact schema validation, semantic budget/weight checks, frozen genome read, typed safe interpreter with no Python `eval`/`exec`.
- [ ] **Step 4: Verify focused pass:** same command passes.
- [ ] **Step 5: Integration check:** contract and IR tests pass together.
- [ ] **Step 6: Commit:** Not performed; this is a new downloadable prototype with no user-authorized repository remote.

### Task 2: World admission and constrained search

**Files:** `cin/worlds.py`, `cin/search.py`, `tests/test_worlds.py`, `tests/test_search.py`

**Interfaces:** `admit_world(world, witness_engine, governor) -> WorldCertificate`; `verify_program(expr,world,governor) -> Verdict`; `enumerate_candidates(seed, task, rng) -> Iterator[Proposal]`.

- [ ] **Step 1:** Tests for MAX2 admission on full finite domain; contradictory tasks rejected or UNKNOWN; incomplete domain fails; invalid preconditions rejected; bounded search emits typed new trees without reading the private witness.
- [ ] **Step 2:** `pytest -q tests/test_worlds.py tests/test_search.py` fails due to absent imports.
- [ ] **Step 3:** Implement safe closed formula language, exhaustive domain truth checks, verifier-private bounded witness discovery, deterministic task-directed structural candidate generation; cap domain and search.
- [ ] **Step 4:** Focused tests pass.
- [ ] **Step 5:** Test task validity with exported sample world.
- [ ] **Step 6:** No commit (new local artifact only).

### Task 3: Acceptance, offspring, lifecycle and evidence

**Files:** `cin/evolution.py`, `cin/archive.py`, `tests/test_evolution.py`

**Interfaces:** `Experiment(...).run() -> Report`; `spawn_verified(parent,artifact,...) -> Organism`; `Archive.append(kind,payload) -> hash`.

- [ ] **Step 1:** Tests that no failure promotes; prior skills cannot regress; child has exactly five frozen genes and inherits verified artifact with lineage; hitting budget stops and repeated archive is idempotent; world mutation has fresh admission verdict; replays match with fixed seed.
- [ ] **Step 2:** `pytest -q tests/test_evolution.py` fails on missing exports.
- [ ] **Step 3:** Implement monotonic capability map and content-addressed accepted solutions, offspring from approved replayed capability, deterministic terminal stop, JSONL event records, domain mutation and read-only verifier.
- [ ] **Step 4:** Focused tests pass.
- [ ] **Step 5:** End-to-end experiment run twice under fixed RNG and compare content hashes of normalized scientific outcomes.
- [ ] **Step 6:** No commit (new local artifact only).

### Task 4: Command-line demonstration and research report

**Files:** `cin/__main__.py`, `README.md`, `tests/test_cli.py`, `experiments/example_run.json`

**Interfaces:** `python -m cin validate`; `python -m cin demo --seed 7 --output PATH`.

- [ ] **Step 1:** Tests that validate exits nonzero for bad genome, demo records real accepted capability/lineage/world evidence when found, fixed-seed outcomes stable.
- [ ] **Step 2:** `pytest -q tests/test_cli.py` fails while CLI absent.
- [ ] **Step 3:** Implement reproducible CLI, output folder with JSON report and event log; honest missing scientific claims and documented limits.
- [ ] **Step 4:** Focused tests pass.
- [ ] **Step 5:** `pytest -q` and CLI smoke run; inspect actual report before claiming results.
- [ ] **Step 6:** No commit (new local artifact only).

## Decisions and explicitly deferred work

- No GitHub repository or remote was provided, so do not push or create commits.
- Verification of worlds/candidates is exhaustive over declared finite input domains, not SMT proofs over all mathematical integers.
- Organism-generated IR is data only. The Python host is trusted and not isolated from malicious changes to the host itself; stronger OS sandboxing is required for arbitrary code support.
- The sealed transfer evaluation and maturity certification are reserved for separate research runs with a precommitted holdout; the demo must report them as not evaluated, not passed.
- v0.1 can demonstrate reproduction after a verified hereditary skill and world domain evolution, but driver meta-mutation, full two-task heritability proofs, composition learning, and 5-seed statistical ablations are deferred rather than simulated.
