from __future__ import annotations
import time
from pydantic import BaseModel
from .grader import Grader
from .models import GradeResult, Patch, TaskSpec


class ScoreCard(BaseModel):
    task_id: str
    model_id: str
    attempts: int
    pass_rate: float
    avg_score: float
    avg_duration: float
    grade: GradeResult | None = None


class Scorer:
    def __init__(self, task: TaskSpec, attempts: int = 1):
        self.task = task
        self.attempts = attempts
        self.grader = Grader(task)

    def score(self, patch: Patch, model_id: str = 'model') -> ScoreCard:
        grades: list[GradeResult] = []
        total_duration = 0.0

        for _ in range(self.attempts):
            start = time.perf_counter()
            grade = self.grader.grade(patch)
            total_duration += time.perf_counter() - start
            grades.append(grade)

        passes = sum(1 for g in grades if g.passed)
        return ScoreCard(
            task_id=self.task.id,
            model_id=model_id,
            attempts=self.attempts,
            pass_rate=passes / self.attempts,
            avg_score=sum(g.score for g in grades) / self.attempts,
            avg_duration=total_duration / self.attempts,
            grade=grades[0],
        )
