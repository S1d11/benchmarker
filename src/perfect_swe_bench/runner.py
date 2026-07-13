from __future__ import annotations
import argparse
from pathlib import Path
from .models import Patch, TaskSpec
from .mutation import MutationTester
from .scoring import Scorer


def main():
    parser = argparse.ArgumentParser(description='Perfect SWE Bench harness')
    sub = parser.add_subparsers(dest='command')

    run = sub.add_parser('run')
    run.add_argument('--task', required=True, type=Path)
    run.add_argument('--patch', required=True, type=Path)
    run.add_argument('--model-id', default='model')
    run.add_argument('--attempts', type=int, default=1)

    validate = sub.add_parser('validate')
    validate.add_argument('--task', required=True, type=Path)

    args = parser.parse_args()
    task = TaskSpec.from_yaml(args.task)

    if args.command == 'run':
        patch = Patch.from_dir(args.patch)
        scorer = Scorer(task, attempts=args.attempts)
        card = scorer.score(patch, model_id=args.model_id)
        print(card.model_dump_json(indent=2))
    elif args.command == 'validate':
        tester = MutationTester(task)
        result = tester.validate()
        print(result.model_dump_json(indent=2))
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
