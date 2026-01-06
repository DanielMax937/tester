from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from . import __version__
from . import observe as observe_mod
from . import plan as plan_mod
from . import container as container_mod
from . import runner as runner_mod


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Autonomous SDET (Software Development Engineer in Test) agent CLI")
    parser.add_argument("command", nargs="?", default="run", help="Command to execute (run)")
    parser.add_argument("--base", dest="base", default="main", help="Base branch for git diff (default: main)")
    parser.add_argument("--dry-run", dest="dry_run", action="store_true", help="Plan only; do not build or run Docker/tests")
    parser.add_argument("--version", action="store_true", help="Show version and exit")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.version:
        print(f"Autonomous SDET agent version {__version__}")
        return 0

    command = args.command

    if command not in {"run", "plan", "observe"}:
        parser.print_help()
        return 0

    repo_root = Path.cwd()

    # Observe
    observation = observe_mod.observe_repository(repo_root, base_branch=args.base)

    if command == "observe":
        print(f"Observed app_type={observation.app_type!r}, entry_point={observation.entry_point!r}")
        return 0

    # Plan
    container_plan, test_plan = plan_mod.create_plans(observation, repo_root=repo_root)

    if command == "plan" or args.dry_run:
        print("Autonomous SDET planning complete.")
        print(f"  Base image: {container_plan.base_image}")
        print(f"  CMD: {container_plan.cmd}")
        print(f"  Test kind: {test_plan.kind}")
        print(f"  Flows: {[flow.description for flow in test_plan.flows]}")
        return 0

    # Act + Reflect
    agent_dir = repo_root / ".agent"
    dockerfile_path = container_mod.ensure_dockerfile(repo_root, agent_dir, container_plan)

    report_path = runner_mod.run_e2e(repo_root, agent_dir, observation, container_plan, test_plan)

    rel_report = report_path.relative_to(repo_root)
    print(f"Autonomous SDET run complete. Report written to {rel_report}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
