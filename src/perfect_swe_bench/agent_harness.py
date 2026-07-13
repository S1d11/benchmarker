from __future__ import annotations
import shutil
import subprocess
from abc import ABC, abstractmethod
from pathlib import Path
from .models import Patch, TaskSpec
from .sandbox import Sandbox


class Agent(ABC):
    @abstractmethod
    def run(self, task: TaskSpec, workspace: Path, output_dir: Path):
        """Run the agent in the workspace and write patch files to output_dir."""


class FileAgent(Agent):
    """Agent for testing: copies a fixed patch directory to output_dir."""

    def __init__(self, patch_dir: Path):
        self.patch_dir = patch_dir

    def run(self, task: TaskSpec, workspace: Path, output_dir: Path):
        if output_dir.exists():
            shutil.rmtree(output_dir)
        shutil.copytree(self.patch_dir, output_dir)


class LocalCommandAgent(Agent):
    """Agent that runs a shell command in the workspace."""

    def __init__(self, command: str):
        self.command = command

    def run(self, task: TaskSpec, workspace: Path, output_dir: Path):
        env = {
            'PSB_TASK_DESCRIPTION': task.description,
            'PSB_OUTPUT_DIR': str(output_dir),
            'PSB_WORKSPACE': str(workspace),
        }
        subprocess.run(
            self.command,
            cwd=workspace,
            shell=True,
            env={**dict(subprocess.os.environ), **env},
            check=True,
        )


class AgentHarness:
    def __init__(self, task: TaskSpec, agent: Agent):
        self.task = task
        self.agent = agent

    def run(self) -> Patch:
        # Prepare a workspace without the hidden verifier.
        sandbox = Sandbox.prepare(self.task, stage_verifier=False)
        output_dir = sandbox.root / 'output'
        output_dir.mkdir(parents=True, exist_ok=True)
        try:
            self.agent.run(self.task, sandbox.repo_path, output_dir)
            if not any(output_dir.iterdir()):
                raise RuntimeError('Agent produced no output files')
            return Patch.from_dir(output_dir)
        finally:
            sandbox.cleanup()
