from __future__ import annotations
import difflib
import fnmatch
import os
import subprocess
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any
from .models import Criterion, CriterionResult, GradeResult, Patch, TaskSpec
from .sandbox import Sandbox


class CriterionRunner(ABC):
    @abstractmethod
    def run(self, criterion: Criterion, task: TaskSpec, patch: Patch) -> CriterionResult:
        pass


class ClassicalRunner(CriterionRunner):
    """Inject hidden verifier tests and run pytest over the patched repository."""

    def run(self, criterion: Criterion, task: TaskSpec, patch: Patch) -> CriterionResult:
        sandbox = Sandbox.prepare(task, patch)
        try:
            paths = criterion.config.get('paths', ['tests', 'verifier'])
            cmd = ['python', '-m', 'pytest', '-q'] + paths
            proc = sandbox.run(cmd)
            passed = proc.returncode == 0
            stdout = proc.stdout
            stderr = proc.stderr
        except Exception as exc:
            return self._result(criterion, False, error=str(exc))
        finally:
            sandbox.cleanup()
        return self._result(
            criterion,
            passed,
            stdout=stdout,
            stderr=stderr,
            exit_code=proc.returncode,
        )

    def _result(
        self,
        criterion: Criterion,
        passed: bool,
        stdout: str = '',
        stderr: str = '',
        exit_code: int | None = None,
        error: str | None = None,
    ) -> CriterionResult:
        return CriterionResult(
            name=criterion.name,
            type=criterion.type,
            passed=passed,
            blocker=criterion.blocker,
            weight=criterion.weight,
            score=1.0 if passed else 0.0,
            stdout=stdout,
            stderr=stderr,
            exit_code=exit_code,
            error=error,
        )


class ReverseClassicalRunner(CriterionRunner):
    """Run agent-submitted tests on the base (buggy) commit. They must fail."""

    def run(self, criterion: Criterion, task: TaskSpec, patch: Patch) -> CriterionResult:
        new_tests = self._new_test_files(patch, task)
        min_new_tests = criterion.config.get('min_new_tests', 1)
        if len(new_tests) < min_new_tests:
            return self._result(
                criterion,
                False,
                error=f'expected at least {min_new_tests} new test file(s), found {len(new_tests)}',
            )

        sandbox = Sandbox.prepare(task, patch=None, stage_verifier=False)
        try:
            for rel, content in new_tests:
                target = sandbox.repo_path / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(content, encoding='utf-8')
            cmd = ['python', '-m', 'pytest', '-q'] + [rel for rel, _ in new_tests]
            proc = sandbox.run(cmd)
            passed = proc.returncode != 0
            stdout = proc.stdout
            stderr = proc.stderr
        except Exception as exc:
            return self._result(criterion, False, error=str(exc))
        finally:
            sandbox.cleanup()
        return self._result(
            criterion,
            passed,
            stdout=stdout,
            stderr=stderr,
            exit_code=proc.returncode,
        )

    def _new_test_files(self, patch: Patch, task: TaskSpec) -> list[tuple[str, str]]:
        result = []
        for rel, content in patch.files.items():
            if not rel.startswith('tests/'):
                continue
            original_path = task.repository_path / rel
            if original_path.exists():
                original = original_path.read_text(encoding='utf-8')
                if original == content:
                    continue
            result.append((rel, content))
        return result

    def _result(
        self,
        criterion: Criterion,
        passed: bool,
        stdout: str = '',
        stderr: str = '',
        exit_code: int | None = None,
        error: str | None = None,
    ) -> CriterionResult:
        return CriterionResult(
            name=criterion.name,
            type=criterion.type,
            passed=passed,
            blocker=criterion.blocker,
            weight=criterion.weight,
            score=1.0 if passed else 0.0,
            stdout=stdout,
            stderr=stderr,
            exit_code=exit_code,
            error=error,
        )


class CommandRunner(CriterionRunner):
    """Run a shell command and pass if it exits 0."""

    def run(self, criterion: Criterion, task: TaskSpec, patch: Patch) -> CriterionResult:
        sandbox = Sandbox.prepare(task, patch)
        try:
            cmd = criterion.config['command']
            shell = criterion.config.get('shell', False)
            proc = sandbox.run(cmd, shell=shell)
            passed = proc.returncode == 0
            stdout = proc.stdout
            stderr = proc.stderr
        except KeyError as exc:
            return self._result(criterion, False, error=f'missing command: {exc}')
        except Exception as exc:
            return self._result(criterion, False, error=str(exc))
        finally:
            sandbox.cleanup()
        return self._result(
            criterion,
            passed,
            stdout=stdout,
            stderr=stderr,
            exit_code=proc.returncode,
        )

    def _result(
        self,
        criterion: Criterion,
        passed: bool,
        stdout: str = '',
        stderr: str = '',
        exit_code: int | None = None,
        error: str | None = None,
    ) -> CriterionResult:
        return CriterionResult(
            name=criterion.name,
            type=criterion.type,
            passed=passed,
            blocker=criterion.blocker,
            weight=criterion.weight,
            score=1.0 if passed else 0.0,
            stdout=stdout,
            stderr=stderr,
            exit_code=exit_code,
            error=error,
        )


class ScopeRunner(CriterionRunner):
    """Check patch boundaries, diff size, and semantic locality of changes."""

    def run(self, criterion: Criterion, task: TaskSpec, patch: Patch) -> CriterionResult:
        try:
            stats = self._compute_diff_stats(task, patch)
            errors = self._check_constraints(criterion, stats)
            passed = not errors
            stdout = '\n'.join(errors) if errors else 'scope checks passed'
            stderr = repr(stats)
        except Exception as exc:
            return self._result(criterion, False, error=str(exc))
        return self._result(criterion, passed, stdout=stdout, stderr=stderr)

    def _compute_diff_stats(self, task: TaskSpec, patch: Patch) -> dict[str, Any]:
        added = 0
        removed = 0
        changed_files = []
        new_tests = 0

        original_files = {
            p.relative_to(task.repository_path).as_posix()
            for p in task.repository_path.rglob('*')
            if p.is_file()
        }

        for rel in sorted(patch.files.keys()):
            original = ''
            modified = patch.files[rel]
            original_path = task.repository_path / rel
            if original_path.exists():
                original = original_path.read_text(encoding='utf-8')

            if original == modified:
                continue

            changed_files.append(rel)
            if rel.startswith('tests/'):
                new_tests += 1

            original_lines = original.splitlines()
            modified_lines = modified.splitlines()
            diff = list(
                difflib.unified_diff(
                    original_lines,
                    modified_lines,
                    fromfile=f'a/{rel}',
                    tofile=f'b/{rel}',
                    lineterm='',
                )
            )
            for line in diff:
                if line.startswith('+') and not line.startswith('+++'):
                    added += 1
                elif line.startswith('-') and not line.startswith('---'):
                    removed += 1

        return {
            'changed_files': changed_files,
            'changed_files_count': len(changed_files),
            'added': added,
            'removed': removed,
            'net': added - removed,
            'total': added + removed,
            'new_tests': new_tests,
        }

    def _check_constraints(self, criterion: Criterion, stats: dict[str, Any]) -> list[str]:
        errors = []
        cfg = criterion.config
        allowed = cfg.get('allowed', [])
        denied = cfg.get('denied', [])

        for rel in stats['changed_files']:
            if denied and any(fnmatch.fnmatch(rel, p) for p in denied):
                errors.append(f'{rel} matches denied pattern')
            if allowed and not any(fnmatch.fnmatch(rel, p) for p in allowed):
                errors.append(f'{rel} not in allowed files')

        limits = {
            'max_changed_files': 'changed_files_count',
            'max_added_lines': 'added',
            'max_removed_lines': 'removed',
            'max_net_lines': 'net',
            'max_total_lines': 'total',
            'min_new_tests': 'new_tests',
        }
        for key, stat_key in limits.items():
            if key in cfg:
                limit = cfg[key]
                value = stats[stat_key]
                if key == 'min_new_tests':
                    if value < limit:
                        errors.append(f'new tests {value} < {limit}')
                else:
                    if value > limit:
                        errors.append(f'{stat_key} {value} > {limit}')

        return errors

    def _result(
        self,
        criterion: Criterion,
        passed: bool,
        stdout: str = '',
        stderr: str = '',
        exit_code: int | None = None,
        error: str | None = None,
    ) -> CriterionResult:
        return CriterionResult(
            name=criterion.name,
            type=criterion.type,
            passed=passed,
            blocker=criterion.blocker,
            weight=criterion.weight,
            score=1.0 if passed else 0.0,
            stdout=stdout,
            stderr=stderr,
            exit_code=exit_code,
            error=error,
        )


class PromptRunner(CriterionRunner):
    """LLM-based code quality review (placeholder; requires API key to enable)."""

    def run(self, criterion: Criterion, task: TaskSpec, patch: Patch) -> CriterionResult:
        if not criterion.config.get('enabled', False):
            return CriterionResult(
                name=criterion.name,
                type=criterion.type,
                passed=True,
                blocker=criterion.blocker,
                weight=criterion.weight,
                score=1.0,
                stdout='LLM review disabled',
            )
        api_key = criterion.config.get('api_key') or os.environ.get('OPENAI_API_KEY')
        if not api_key:
            return CriterionResult(
                name=criterion.name,
                type=criterion.type,
                passed=False,
                blocker=criterion.blocker,
                weight=criterion.weight,
                score=0.0,
                error='No LLM API key configured for prompt review',
            )
        return CriterionResult(
            name=criterion.name,
            type=criterion.type,
            passed=True,
            blocker=criterion.blocker,
            weight=criterion.weight,
            score=1.0,
            stdout='LLM review not yet implemented; scored as passing',
        )


class AdaptiveRunner(CriterionRunner):
    """Adaptive classical grading: LLM aligns reference tests to the submission."""

    def run(self, criterion: Criterion, task: TaskSpec, patch: Patch) -> CriterionResult:
        return CriterionResult(
            name=criterion.name,
            type=criterion.type,
            passed=True,
            blocker=criterion.blocker,
            weight=0.0,
            score=1.0,
            stdout='Adaptive grading not yet implemented; skipped',
        )


class Grader:
    _runners: dict[str, type[CriterionRunner]] = {
        'classical': ClassicalRunner,
        'reverse_classical': ReverseClassicalRunner,
        'command': CommandRunner,
        'scope': ScopeRunner,
        'prompt': PromptRunner,
        'adaptive': AdaptiveRunner,
    }

    def __init__(self, task: TaskSpec):
        self.task = task

    def grade(self, patch: Patch) -> GradeResult:
        rubric = self.task.rubric or self._default_rubric()
        criteria: list[CriterionResult] = []
        any_blocker_failed = False
        total_weight = 0.0
        raw_score = 0.0

        for criterion in rubric:
            runner_cls = self._runners.get(criterion.type)
            if runner_cls is None:
                result = CriterionResult(
                    name=criterion.name,
                    type=criterion.type,
                    passed=False,
                    blocker=criterion.blocker,
                    weight=criterion.weight,
                    score=0.0,
                    error=f'unknown criterion type: {criterion.type}',
                )
            else:
                result = runner_cls().run(criterion, self.task, patch)
            criteria.append(result)
            total_weight += criterion.weight
            if result.passed:
                raw_score += criterion.weight
            if criterion.blocker and not result.passed:
                any_blocker_failed = True

        if any_blocker_failed:
            score = 0.0
        else:
            score = raw_score / total_weight if total_weight else 1.0

        return GradeResult(
            passed=not any_blocker_failed,
            score=score,
            total_weight=total_weight,
            raw_score=raw_score,
            criteria=criteria,
        )

    def _default_rubric(self) -> list[Criterion]:
        return [
            Criterion(name='classical', type='classical', blocker=True, weight=1.0),
        ]
