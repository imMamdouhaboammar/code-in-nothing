# Security, evaluation integrity, and operations

**Scope:** Offline, trusted-host research pilot. This is not a security certification and does not assert sandbox isolation beyond data-only CIN-IR.

## 1. Trust model

- **Trusted:** project owner, runtime source/dependencies, evaluator implementation, formal-schema registry, experiment controller, governor and private holdout storage.
- **Untrusted:** organism-generated IR, future learned drivers, world-generated specifications, importable third-party task corpora, human-readable metadata, generated source exports and external research text.
- **Sensitive boundaries:** verifier-only witness program, held-out tasks and scores, actor access to host process, resource accounting, accepted artifact promotion, and append-only evidence persistence.

An in-process Python module boundary is **not** a security isolation boundary. Today CIN-IR cannot call imports, network, files or process execution. Future arbitrary-source execution is prohibited until a separate OS-level sandbox is implemented and tested.

## 2. Attack and failure matrix

| Threat / failure | Present protection | Required before scope expands |
| --- | --- | --- |
| Generated code runs host shell or reads secrets | Closed CIN-IR opcode whitelist and `run_ir` | Dedicated sandboxed process, no network, read-only inputs, mount/UID/seccomp or equivalent policy, memory/CPU/pid limits |
| Rewriting evaluator/holdout | No generated IR access to host files | Distinct permission boundary, audit, pinned signed manifests if threat requires |
| Benchmark leakage via world admission | Witness implementation not provided to candidate stream | Strict separate witness store and no shared dynamic tracing/logs visible to generator |
| Grading through test manipulation | Independent fixed world spec checks | Versioned evaluator release, one-shot sealed holdout, no adaptive exposure of final set |
| Search overrun / denial of service | `max_evals`, bounded AST/ops/domain | Total cohort and world witness budgets, external watchdog and allocation limits |
| Forged inheritance record | Program digest and independent replay of required world specs | Transactional certificate schema/version verification; full dependency closure |
| Hash-chain rewriter | JSONL chain detects incidental corruption | External anchoring/signing where insider threat is relevant |
| Data loss on process crash | Current JSONL append per event | Durable transaction/checkpoint/recovery; reconcile report, event and artifact graph |
| Scientific score inflation | Explicit not-evaluated flags and finite-domain wording | Frozen hypotheses, matched budgets, hidden transfer set, audit of every evaluation |
| Malicious or contradictory formal task | Limited DSL, semantic guards, finite admission witness | Deeper constraint validation, equivalence/novelty checks, solver unknown policy |

## 3. Worker boundary for future arbitrary code

No unrestricted generated Python runs in the current host. If future research justifies source execution, design the worker as a disposable process with a read-only immutable input bundle, dedicated temporary directory, zero network access by default, no inherited credentials or host home mounts, a fixed time and RSS/PID/file-size quota, immutable interpreter/kernel identity, and status channel carrying only typed verdicts and bounded stdout/stderr. Terminate on quota violation. Never claim a subprocess alone is an adequate sandbox.

## 4. Evidence and operational runbook

Baseline commands:

```bash
python -m pytest -q
python -m cin validate
python -m cin demo --seed 0 --max-evals 250 --output runs/first
```

The output directory must not exist. Preserve `report.json`, `events.jsonl` and any `generated_program.py` without modifying source evidence. Verify the journal with `Archive.verify_chain(path)`; this is an integrity check, not independent authentication.

**Unexpected validation failure:** Check source YAML/schema mismatch; do not weaken a schema to admit the artifact. **World admission UNKNOWN:** report exhausted witness budget, do not classify the world impossible. **Budget cap:** stop actor, preserve evidence and record what work was charged. **Mismatch on reproducibility:** compare manifest, versions and normalized decisions; CPU timing diagnostics can differ. **Journal corruption:** quarantine run, preserve original bytes, do not continue or silently recreate chain. **Prototype crash:** manual new run in a new directory; resume is not implemented.

## 5. Next-phase acceptance for operations

P1 must prove that power loss or forced crash at event boundaries cannot cause a duplicate accepted birth or skill, that resumed resource budgets cannot reset, and that replay with a fixed pinned manifest regenerates identical semantic decisions. OS isolation should be introduced only when actual research requires unsafe operators, separately from the persistence/scheduler change.
