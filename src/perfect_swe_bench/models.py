from __future__ import annotations
from pathlib import Path
from typing import Any, Optional
from pydantic import BaseModel, Field


class Metadata(BaseModel):
    category: str = 'bug_fix'
    language: str = 'python'
    difficulty: str = 'easy'
    risk: str = 'low'


class Patch(BaseModel):
    files: dict[str, str]

    @classmethod
    def from_dir(cls, path: Path) -> 'Patch':
        files = {}
        for file in path.rglob('*'):
            if file.is_file():
                rel = file.relative_to(path).as_posix()
                files[rel] = file.read_text(encoding='utf-8')
        return cls(files=files)


class Criterion(BaseModel):
    name: str
    type: str  # classical | reverse_classical | command | scope | prompt | adaptive
    blocker: bool = True
    weight: float = 1.0
    config: dict[str, Any] = Field(default_factory=dict)


class TaskSpec(BaseModel):
    id: str
    name: str
    description: str
    repository_path: Path
    verifier_path: Path
    public_tests_path: Optional[Path] = None
    reference_patch_path: Optional[Path] = None
    mutation_target: Optional[str] = None
    rubric: list[Criterion] = Field(default_factory=list)
    network_policy: str = 'offline'
    metadata: Metadata = Field(default_factory=Metadata)

    @classmethod
    def from_yaml(cls, path: Path) -> 'TaskSpec':
        import yaml
        data = yaml.safe_load(path.read_text(encoding='utf-8'))
        base = path.parent
        for key in [
            'repository_path',
            'verifier_path',
            'public_tests_path',
            'reference_patch_path',
        ]:
            if data.get(key):
                data[key] = base / data[key]
        if data.get('rubric'):
            data['rubric'] = [Criterion(**c) for c in data['rubric']]
        return cls(**data)


class VerificationResult(BaseModel):
    passed: bool
    exit_code: int
    stdout: str
    stderr: str
    tests_passed: int = 0
    tests_failed: int = 0
    mutation_score: Optional[float] = None


class CriterionResult(BaseModel):
    name: str
    type: str
    passed: bool
    blocker: bool
    weight: float
    score: float  # 0..1
    exit_code: int | None = None
    stdout: str = ''
    stderr: str = ''
    error: str | None = None


class GradeResult(BaseModel):
    passed: bool
    score: float  # 0..1; 0 if any blocker fails, else weighted average
    total_weight: float
    raw_score: float
    criteria: list[CriterionResult]


class MutationResult(BaseModel):
    total: int
    killed: int
    survived: int
    score: float
    survivors: list[str]
