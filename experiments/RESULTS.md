# CIN-Lab v0.1: pilot run results

Verified commands run from the extracted source tree:

```bash
python -m cin validate
python -m cin demo --seed 0 --max-evals 250 --output experiments/sample-full
python -m cin demo --seed 0 --max-evals 250 --no-world-evolution --output experiments/sample-frozen-world
pytest -q
```

| Metric | Full pilot | Frozen-world control |
|---|---:|---:|
| Accepted source-world task | Yes | Yes |
| Proposals until accepted MAX2 program | 85 | 85 |
| Verified task behavior | 1 | 1 |
| Distinct admitted world specifications solved | 2 | 1 |
| World mutation admitted | Yes | No |
| Children inheriting verified source program | 1 | 0 |
| One-shot sealed transfer assessment | Not run | Not run |
| Operational maturity evaluation | Not run | Not run |

The full pilot discovers `return (y if x < y else x)` from a typed grammar. The second admitted world expands the finite input domain while preserving the same MAX2 objective, so this is **not evidence of new functional task learning**. The control result has no offspring because the prototype requires checks against two distinct world specifications before inheritance. These two configurations alone cannot establish scientific efficacy of co-evolution.
