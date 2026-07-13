from __future__ import annotations
import time
from pydantic import BaseModel
from .models import Patch, TaskSpec
from .verifier import Verifier


class ScoreCard(BaseModel):
    task_id: str
    model_id: str
    attempts: int
    passes: int
    pass_rate: float
    avg_tests_passed: float
    avg_tests_failed: float
    avg_duration: float
    mutation_score: float | None = None


class Scorer:
    def __init__(self, task: TaskSpec, attempts: int = 1):
        self.task = task
        self.attempts = attempts
        self.verifier = Verifier(task)

    def score(self, patch: Patch, model_id: str = 'model') -> ScoreCard:
        passes = 0
        total_passed = 0
        total_failed = 0
        total_duration = 0.0

        for _ in range(self.attempts):
            start = time.perf_counter()
            result = self.verifier.verify(patch)
            total_duration += time.perf_counter() - start
            if result.passed:
                passes += 1
            total_passed += result.tests_passed
            total_failed += result.tests_failed

        return ScoreCard(
            task_id=self.task.id,
            model_id=model_id,
            attempts=self.attempts,
            passes=passes,
            pass_rate=passes / self.attempts,
            avg_tests_passed=total_passed / self.attempts,
            avg_tests_failed=total_failed / self.attempts,
            avg_duration=total_duration / self.attempts,
            mutation_score=result.mutation_score,
        )
