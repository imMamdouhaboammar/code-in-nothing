# M1 tier-1 mathematical synthesis — development evidence

**Date:** 2026-10-18  
**Branch:** `feat/m1-compositional-math-search`  
**Review:** [PR #1](https://github.com/imMamdouhaboammar/code-in-nothing/pull/1)  
**Protocol:** `cin.m1/development-pilot` (not a preregistered comparison study).

## Reproduction

From a repository checkout with `pip install -e '.[dev]'`:

```bash
python -m cin validate
python -m pytest -q
python experiments/run_m1.py
python -m ruff check .
python -m ruff format --check .
```

CI runs the experiment on Ubuntu/Python 3.12, and full tests plus legacy
MAX2 demonstrations on Python 3.11–3.13 across Ubuntu and macOS.
Recorded CI: [GitHub Actions run 39118757098](https://github.com/imMamdouhaboammar/code-in-nothing/actions/runs/39118757098).

## Observed results

Values below are the **CI-produced results** of the current repository
experiment (not handwritten target programs or earlier local prototypes).

| Formal world | Proposals seen | Shape attempts | Observational prunes | Budget | Verified points | Screen calls | Screen IR ops | Formal calls | Formal IR ops | CPU (s) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `min2` | 59 | 832 | 722 | 250 | 81 | 66 | 280 | 1 | 405 | 0.009 |
| `absdiff` | 22,698 | 229,135 | 197,970 | 30,000 | 81 | 24,547 | 199,347 | 1 | 567 | 1.724 |

**Verdict:** `PASS / FINITE_EXHAUSTIVE` for each stated domain
`x,y ∈ [-4,4]` (81 ordered pairs). The independently verified hashes
are `3cff4c3c2e1fff526b1e48f4f051dac3477dd6122852d7990cffe42719fdbc9f`
and `834179df86cc9393eb20ed862d2fa8ea1844e60d73bc4ba18ecfb5901c1d55eb`
respectively. Neither result is a universal proof over unbounded integers.

The experiment's six fixed public screening inputs are used only by the
development harness. They are **not** passed into `candidate_stream`.
Only surviving programs enter complete formal verification. The 22,698
candidate count includes screening failures and is **not** the number of
full exhaustive-verifier calls.

**Current accounting omissions:** generated fingerprint tuple operations and
world-admission witness search have no separate operation ledger (admission
was **not run** in this experiment). Internal shape attempts and observational
prunes are now explicitly counted. Training screen and complete final
verification operations are separately reported. CPU seconds are
hardware-specific and include Python-level generation costs.

## Regression evidence

At CI run 39118757098, the 6 test-matrix jobs and the Ruff lint/format job
completed successfully; the previously implemented MAX2 demo, frozen-world
control, and no-inheritance control remain part of each matrix job.
CodeQL runs independently. This proves compatibility with these checks,
not absence of all bugs or performance regressions.

## Scientific interpretation and next review gates

`min2` and `absdiff` are distinct specified functions. Their success
demonstrates newly expressible compositional arithmetic, **not** verified
offspring learning, cross-task transfer, evolutionary policy adaptation,
GCD synthesis, or general intelligence.

The existing organism lifecycle has a 2,000-candidate limit in the frozen
`stop_station` gene. The 30,000-proposal `absdiff` result comes from an
independent research harness; it is not claimed as within one organism's
current lifetime.

Before any efficiency claim: extend internal work accounting to measured fingerprint
construction, and execute\nequal-budget typed-random, prior shallow grammar, CEGIS and hereditary
comparisons, include world admission and witness costs, freeze task splits,
and preserve failed/UNKNOWN runs. Next separately reviewable engineering
gate M2 adds versioned 3-input IR/world signatures for `median3` and
`clamp`; co-evolution, transfer, SMT, GCD and extended GCD must follow
their existing independent gates in [MATH-PHASES](../roadmap/MATH-PHASES.md).

See the [architecture decision](../adr/0005-cost-layered-observational-search.md)
and [v0.5 specification](../specs/2026-10-18-cin-mathematical-evolution-v0.5.md).
