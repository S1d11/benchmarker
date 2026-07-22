# Perfect SWE Bench

A verifier-centric, contamination-resistant coding benchmark for evaluating software engineering agents.

Core principles:

- Tasks are scratch-written and not derived from public PRs or commits.
- Correctness is decided by hidden behavioral tests and property tests, not by diff matching.
- Verifiers are validated with mutation testing before any task is used.
- Public and hidden tests are strictly separated.
- Model and agent tracks are separated.
- Grading uses an extensible rubric with blocker and non-blocker criteria, inspired by FrontierCode.

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
  - `models.py` — task, patch, rubric, and result schemas
  - `sandbox.py` — isolated repo preparation and patch application
  - `verifier.py` — hidden/property test execution
  - `grader.py` — rubric-based grading (classical, reverse-classical, command, scope, prompt, adaptive)
  - `mutation.py` — verifier validation via mutation testing
  - `scoring.py` — pass rate, weighted score, and scorecards
  - `runner.py` — CLI entry point
- `tasks/<task>/` — task definitions
  - `repo/` — starting repository snapshot
  - `verifier/` — hidden test suite and property tests
  - `patches/` — reference and example patches

### Rubric grading

Each task may define a `rubric` in `task.yaml`. A rubric is a list of criteria with `type`, `blocker`, `weight`, and `config`.

Supported criterion types:

| Type | Purpose |
|------|---------|
| `classical` | Inject hidden verifier tests and run pytest over the patched repo. |
| `reverse_classical` | Run agent-submitted tests on the base (buggy) commit; they must fail to be meaningful. |
| `command` | Run a shell command (e.g., `python -m compileall .`) and require exit code 0. |
| `scope` | Enforce changed files, diff size, and test-file boundaries. |
| `prompt` | LLM diff review (placeholder; requires an API key to enable). |
| `adaptive` | Adaptive test alignment (placeholder). |

Blockers must all pass for a submission to be considered "passing." The final score is a weighted aggregate of all criteria; if any blocker fails, the score is zero.

Example `task.yaml` rubric:

```yaml
rubric:
  - name: behavioral_correctness
    type: classical
    blocker: true
    weight: 3.0
    config:
      paths: [tests, verifier]
  - name: reverse_classical_tests
    type: reverse_classical
    blocker: true
    weight: 2.0
    config:
      min_new_tests: 1
  - name: scope
    type: scope
    blocker: true
    weight: 1.0
    config:
      allowed: [calculator.py, tests/*]
      denied: [verifier/*]
      max_changed_files: 2
      max_added_lines: 50
      max_removed_lines: 20
      max_total_lines: 70
  - name: compile_check
    type: command
    blocker: true
    weight: 1.0
    config:
      command: [python, -m, compileall, .]
  - name: code_quality
    type: prompt
    blocker: false
    weight: 0.0
    config:
      enabled: false
```

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

## FrontierCode-inspired additions

- **Mergeability rubric**: tasks are graded on multiple axes (correctness, test quality, scope, mechanical cleanliness, code quality) rather than a single pass/fail bit.
- **Reverse-classical tests**: agent-written tests are run on the buggy base commit to ensure they actually detect the bug.
- **Scope enforcement**: automated checks on allowed/denied files, changed-file count, and diff-size limits.
- **Command checks**: build, lint, and style commands can be run as blocker or non-blocker criteria.
- **Weighted score and pass rate**: score is a weighted aggregate of rubric items; blockers gate the final score.
- **Network policy field**: tasks declare an offline/restricted network policy for fair-internet-use tracking (enforcement is environment-specific).

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
