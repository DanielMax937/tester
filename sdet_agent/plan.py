from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

from .observe import Observation


@dataclass
class ContainerPlan:
    base_image: str
    cmd: List[str]
    ports: List[int]


@dataclass
class TestFlow:
    description: str


@dataclass
class TestPlan:
    kind: str
    flows: List[TestFlow]


def create_plans(observation: Observation, repo_root: Path) -> Tuple[ContainerPlan, TestPlan]:  # noqa: ARG001
    """Create container and test plans from an Observation.

    Supports minimal python-cli and python-web scenarios and falls back to
    conservative defaults otherwise.
    """

    # Python CLI application
    if observation.app_type == "python-cli" and observation.entry_point:
        container_plan = ContainerPlan(
            base_image="python:3.11-slim-bookworm",
            cmd=["python", observation.entry_point],
            ports=[],
        )
        test_plan = TestPlan(
            kind="cli",
            flows=[
                TestFlow(
                    description=f"Run {observation.entry_point} and assert success",
                )
            ],
        )
        return container_plan, test_plan

    # Python web application (single-port, simple heuristic)
    if observation.app_type == "python-web" and observation.entry_point:
        # Default to a common development port; this can be refined later or
        # inferred from configuration if available.
        port = 8000
        container_plan = ContainerPlan(
            base_image="python:3.11-slim-bookworm",
            cmd=["python", observation.entry_point],
            ports=[port],
        )
        test_plan = TestPlan(
            kind="web-python",
            flows=[
                TestFlow(
                    description=(
                        f"Start container on port {port} and exercise key "
                        f"HTTP flows via http://localhost:{port}/"
                    ),
                )
            ],
        )
        return container_plan, test_plan

    # Fallback case
    container_plan = ContainerPlan(
        base_image="python:3.11-slim-bookworm",
        cmd=["python", "-m", "sdet_agent"],
        ports=[],
    )
    test_plan = TestPlan(
        kind="unknown",
        flows=[TestFlow(description="No concrete flows inferred")],
    )
    return container_plan, test_plan
