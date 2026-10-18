# Contributing to Code in Nothing

Thank you for your interest in contributing to **Code in Nothing (CIN-Lab)**.

CIN-Lab is a **model-free research prototype** exploring bounded evolutionary program synthesis with formal finite-domain verification. To preserve the scientific rigor and reproducibility of the project, all contributions must respect the foundational architectural boundaries.

---

## Architectural Boundaries

Before proposing changes, please review [`AGENTS.md`](AGENTS.md), [`CONTEXT.md`](CONTEXT.md), and [`docs/INDEX.md`](docs/INDEX.md).

1. **Preserve the Five-Gene Seed**: The genome schema enforces exactly five genes (`base`, `heritable_program`, `exploration_policy`, `world_mutation`, `stop_station`). Do not add a sixth gene or modify the seed YAML fixtures without a formal specification update.
2. **Model-Free Invariant**: No LLMs, prompt completions, external neural APIs, or task-solution prompts may be introduced into candidate synthesis or evaluation.
3. **Restricted IR Execution**: `cin/ir.py` is the single source of truth for program execution. Generated programs are interpreted data structures, never executed as arbitrary Python code via `eval()` or `exec()`.
4. **Verifier Separation**: `cin/worlds.py` owns formal finite-domain verification and verifier-private witness discovery. Organisms and search policies must never receive the discovered witness.
5. **No Weakening of Asserts**: Never weaken test assertions or modify reference fixtures to make tests pass. Protocol changes require focused negative test cases.

---

## Development Setup

Requirements: Python 3.11+.

### Using `uv` (Recommended)

```bash
# Clone the repository
git clone https://github.com/imMamdouhaboammar/code-in-nothing.git
cd code-in-nothing

# Run test suite
uv run pytest -q

# Run package contract validator
uv run python -m cin validate
```

### Using standard `pip` and virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'

pytest -q
python -m cin validate
```

---

## Validation & Quality Gates

Every pull request must pass the full verification matrix:

1. **Unit and Integration Tests**:
   ```bash
   python -m pytest -q
   ```
2. **Contract and Schema Validation**:
   ```bash
   python -m cin validate
   ```
3. **End-to-End Experiment Verification**:
   ```bash
   # Choose an unused output directory; the CLI refuses to overwrite existing directories
   python -m cin demo --seed 0 --max-evals 250 --output runs/pr-verify
   ```
4. **Linting and Formatting**:
   ```bash
   uv run ruff check .
   uv run ruff format --check .
   ```

---

## Submitting Pull Requests

1. Create a feature branch from `main`:
   ```bash
   git checkout -b feat/your-feature-name
   ```
2. Commit changes using [Conventional Commits](https://www.conventionalcommits.org/):
   - `feat:` for new capabilities
   - `fix:` for bug fixes
   - `test:` for test additions or fixtures
   - `docs:` for documentation updates
   - `refactor:` for internal restructuring without behavior changes
3. Ensure all tests and validation checks pass.
4. Open a pull request against `main`. Fill in the PR template with clear verification evidence.
