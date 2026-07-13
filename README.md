# Perfect SWE Bench

A verifier-centric, contamination-resistant coding benchmark for evaluating software engineering agents.

Core principles:

- Tasks are scratch-written and not derived from public PRs or commits.
- Correctness is decided by hidden behavioral tests and property tests, not by diff matching.
- Verifiers are validated with mutation testing before any task is used.
- Public and hidden tests are strictly separated.
- Model and agent tracks are separated.

## Quick start

Install the package:

```powershell
pip install -e .
```

Validate the verifier for a task (runs mutation testing against the reference patch):

```powershell
perfect-swe-bench validate --task tasks\calculator_bug\task.yaml
```

Run a model patch against the task:

```powershell
perfect-swe-bench run --task tasks\calculator_bug\task.yaml --patch tasks\calculator_bug\patches\correct
```

## Architecture

- `src/perfect_swe_bench/` — benchmark harness
  - `models.py` — task, patch, and result schemas
  - `sandbox.py` — isolated repo preparation and patch application
  - `verifier.py` — hidden/property test execution
  - `mutation.py` — verifier validation via mutation testing
  - `scoring.py` — pass/fail, reliability, and scorecards
  - `runner.py` — CLI entry point
- `tasks/<task>/` — task definitions
  - `repo/` — starting repository snapshot
  - `verifier/` — hidden test suite and property tests
  - `patches/` — reference and example patches

### Verifier test files

Files placed in `tasks/<task>/verifier/` are copied into the scoring sandbox but are not present in the `repo/` snapshot the agent sees during its work. Files must be named `test_*.py` or `*_test.py` so `pytest` collects them. Property tests using `hypothesis` should also follow this naming convention.

## Verification results

Correct patch:

```powershell
perfect-swe-bench run --task tasks\calculator_bug\task.yaml --patch tasks\calculator_bug\patches\correct --attempts 3
```

Broken patch:

```powershell
perfect-swe-bench run --task tasks\calculator_bug\task.yaml --patch tasks\calculator_bug\patches\broken
```

## Next steps

To scale this into a real benchmark:

1. Add more tasks in `tasks/`, each authored from scratch with a reference patch, hidden tests, and property/metamorphic tests.
2. Require `mutation_score == 1.0` (or a very high threshold) before a task is admitted.
3. Separate the agent harness from the scorer so the agent workspace never contains hidden tests.
4. Add regression and integration tests for each task.
5. Add per-task build checks, lint, and static analysis.
6. Implement a private, rotating leaderboard dataset and a public dev split.
7. Add model and agent tracks with a fixed harness and an open harness.
8. Add cost, latency, token, and step tracking.
9. Add human-review sampling and false-pass auditing.
10. Add bootstrap confidence intervals and per-category reporting.
