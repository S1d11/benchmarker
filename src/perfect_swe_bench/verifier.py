from __future__ import annotations
import re
from .models import Patch, TaskSpec, VerificationResult
from .sandbox import Sandbox


class Verifier:
    def __init__(self, task: TaskSpec):
        self.task = task

    def verify(self, patch: Patch) -> VerificationResult:
        sandbox = Sandbox.prepare(self.task, patch)
        try:
            cmd = ['python', '-m', 'pytest', '-q']
            if (sandbox.repo_path / 'tests').is_dir():
                cmd.append('tests')
            cmd.append('verifier')
            proc = sandbox.run(cmd)
            passed, failed = self._parse_summary(proc.stdout + proc.stderr)
            result = VerificationResult(
                passed=proc.returncode == 0,
                exit_code=proc.returncode,
                stdout=proc.stdout,
                stderr=proc.stderr,
                tests_passed=passed,
                tests_failed=failed,
            )
        finally:
            sandbox.cleanup()
        return result

    def _parse_summary(self, output: str) -> tuple[int, int]:
        passed = 0
        failed = 0
        for line in reversed(output.splitlines()):
            line = line.strip()
            if 'passed' in line or 'failed' in line:
                match_passed = re.search(r'(\d+)\s+passed', line)
                if match_passed:
                    passed = int(match_passed.group(1))
                match_failed = re.search(r'(\d+)\s+failed', line)
                if match_failed:
                    failed = int(match_failed.group(1))
                break
        return passed, failed
