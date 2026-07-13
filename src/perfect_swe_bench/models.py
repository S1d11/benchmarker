from __future__ import annotations
from pathlib import Path
from typing import Optional
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


class TaskSpec(BaseModel):
    id: str
    name: str
    description: str
    repository_path: Path
    verifier_path: Path
    public_tests_path: Optional[Path] = None
    reference_patch_path: Optional[Path] = None
    mutation_target: Optional[str] = None
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
        return cls(**data)


class VerificationResult(BaseModel):
    passed: bool
    exit_code: int
    stdout: str
    stderr: str
    tests_passed: int = 0
    tests_failed: int = 0
    mutation_score: Optional[float] = None


class MutationResult(BaseModel):
    total: int
    killed: int
    survived: int
    score: float
    survivors: list[str]
