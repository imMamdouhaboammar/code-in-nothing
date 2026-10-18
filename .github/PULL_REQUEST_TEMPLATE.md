## Description

<!-- Provide a clear description of changes, rationale, and context. -->

## Boundary & Architectural Checklist

- [ ] Preserves the five-gene genome constraint (no 6th gene added).
- [ ] Strictly model-free (no LLMs, prompt completion APIs, or pretrained generative models).
- [ ] Pure AST interpretation (no arbitrary `eval()`, `exec()`, or runtime I/O in `cin.ir`).
- [ ] Verifier isolation maintained (witness discovered by `cin.worlds` is never passed to search/organism).
- [ ] No weakened assertions or modified reference fixtures.

## Verification Evidence

- [ ] `python -m pytest -q` passes (attach output or note test count).
- [ ] `python -m cin validate` passes against schemas and genomes.
- [ ] `python -m cin demo --seed 0 --max-evals 250 --output runs/<unique-path>` completes cleanly.
- [ ] `ruff check .` and `ruff format --check .` pass without errors.
