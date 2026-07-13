from __future__ import annotations
import ast
from typing import Iterable
from .models import MutationResult, Patch, TaskSpec
from .verifier import Verifier


OP_ALTERNATIVES = {
    ast.Add: [ast.Sub, ast.Mult, ast.Div],
    ast.Sub: [ast.Add, ast.Mult, ast.Div],
    ast.Mult: [ast.Add, ast.Sub, ast.Div],
    ast.Div: [ast.Add, ast.Sub, ast.Mult],
    ast.Eq: [ast.NotEq, ast.Lt, ast.Gt],
    ast.NotEq: [ast.Eq, ast.Lt, ast.Gt],
    ast.Lt: [ast.Gt, ast.Eq, ast.NotEq],
    ast.Gt: [ast.Lt, ast.Eq, ast.NotEq],
    ast.LtE: [ast.GtE, ast.Eq, ast.NotEq],
    ast.GtE: [ast.LtE, ast.Eq, ast.NotEq],
    ast.In: [ast.NotIn],
    ast.NotIn: [ast.In],
}


class MutationTester:
    def __init__(self, task: TaskSpec):
        self.task = task
        self.verifier = Verifier(task)

    def load_reference_patch(self) -> Patch:
        if not self.task.reference_patch_path:
            raise ValueError('reference_patch_path not set')
        return Patch.from_dir(self.task.reference_patch_path)

    def validate(self, patch: Patch | None = None) -> MutationResult:
        patch = patch or self.load_reference_patch()
        target = self.task.mutation_target
        if not target:
            raise ValueError('mutation_target not set')
        if target not in patch.files:
            raise ValueError(f'mutation target {target} not in reference patch')

        source = patch.files[target]
        tree = ast.parse(source)
        mutants = list(self._generate_mutants(tree, source))

        killed = 0
        survivors = []
        for name, mutant_source in mutants:
            mutant_files = {**patch.files, target: mutant_source}
            mutant_patch = patch.model_copy(update={'files': mutant_files})
            result = self.verifier.verify(mutant_patch)
            if result.passed:
                survivors.append(name)
            else:
                killed += 1

        total = len(mutants)
        return MutationResult(
            total=total,
            killed=killed,
            survived=len(survivors),
            score=killed / total if total else 1.0,
            survivors=survivors,
        )

    def _generate_mutants(self, tree: ast.AST, source: str) -> Iterable[tuple[str, str]]:
        for node in list(ast.walk(tree)):
            if isinstance(node, ast.BinOp) and type(node.op) in OP_ALTERNATIVES:
                original_op = node.op
                for op_type in OP_ALTERNATIVES[type(original_op)]:
                    node.op = op_type()
                    yield f'binop_{op_type.__name__}_{getattr(node, "lineno", 0)}', ast.unparse(tree)
                    node.op = original_op

            elif isinstance(node, ast.Compare) and node.ops and type(node.ops[0]) in OP_ALTERNATIVES:
                original_op = node.ops[0]
                for op_type in OP_ALTERNATIVES[type(original_op)]:
                    node.ops[0] = op_type()
                    yield f'compare_{op_type.__name__}_{getattr(node, "lineno", 0)}', ast.unparse(tree)
                    node.ops[0] = original_op

            elif isinstance(node, ast.If) and not isinstance(node.test, ast.Constant):
                original_test = node.test
                for value in (True, False):
                    node.test = ast.Constant(value=value)
                    yield f'if_{value}_{getattr(node, "lineno", 0)}', ast.unparse(tree)
                    node.test = original_test
