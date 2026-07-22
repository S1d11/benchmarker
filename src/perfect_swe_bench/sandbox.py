from __future__ import annotations
import shutil
import tempfile
from pathlib import Path
from .models import Patch, TaskSpec


class Sandbox:
    def __init__(self, root: Path, repo_path: Path):
        self.root = root
        self.repo_path = repo_path

    @classmethod
    def prepare(
        cls,
        task: TaskSpec,
        patch: Patch | None = None,
        stage_verifier: bool = True,
    ) -> 'Sandbox':
        root = Path(tempfile.mkdtemp(prefix='psb_'))
        repo_path = root / 'repo'
        shutil.copytree(task.repository_path, repo_path)
        sandbox = cls(root, repo_path)
        if patch:
            sandbox.apply_patch(patch)
        if stage_verifier:
            sandbox._stage_verifier(task)
        return sandbox

    def apply_patch(self, patch: Patch):
        for rel_path, content in patch.files.items():
            target = self.repo_path / rel_path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding='utf-8')

    def _stage_verifier(self, task: TaskSpec):
        dest = self.repo_path / 'verifier'
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(task.verifier_path, dest)

    def snapshot(self, patch_root: Path):
        """Copy current repo state into patch_root as a patch."""
        for file in self.repo_path.rglob('*'):
            if file.is_file():
                rel = file.relative_to(self.repo_path).as_posix()
                # Skip verifier and tests? The caller decides.
                dest = patch_root / rel
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(file, dest)

    def run(self, command: list[str] | str, cwd: Path | None = None, shell: bool = False):
        import subprocess
        cwd = cwd or self.repo_path
        return subprocess.run(command, cwd=cwd, capture_output=True, text=True, shell=shell)

    def cleanup(self):
        shutil.rmtree(self.root, ignore_errors=True)
