"""Run a dependency graph of async tasks independently for each input file.

Tasks with no dependency relationship can run at the same time. Each input
file gets its own ``FileState`` and task outputs, so concurrent files do not
share mutable workflow data.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Awaitable, Callable, Iterable


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    SKIPPED = "skipped"


TaskFunction = Callable[["TaskContext"], Awaitable[Any]]


@dataclass(frozen=True)
class TaskSpec:
    name: str
    run: TaskFunction
    depends_on: tuple[str, ...] = ()


@dataclass
class FileState:
    """Mutable state and outputs belonging to one input file."""

    path: Path
    data: dict[str, Any] = field(default_factory=dict)
    outputs: dict[str, Any] = field(default_factory=dict)
    statuses: dict[str, TaskStatus] = field(default_factory=dict)
    errors: dict[str, BaseException] = field(default_factory=dict)

    @property
    def succeeded(self) -> bool:
        return all(
            status in (TaskStatus.SUCCEEDED, TaskStatus.SKIPPED)
            for status in self.statuses.values()
        ) and not self.errors


@dataclass(frozen=True)
class TaskContext:
    """The per-file context passed to a task function."""

    file: FileState
    task_name: str

    @property
    def path(self) -> Path:
        return self.file.path

    @property
    def data(self) -> dict[str, Any]:
        return self.file.data

    @property
    def outputs(self) -> dict[str, Any]:
        return self.file.outputs


@dataclass
class WorkflowResult:
    files: list[FileState]

    @property
    def succeeded(self) -> bool:
        return all(file.succeeded for file in self.files)


class Workflow:
    """Execute a DAG of async tasks for every input file.

    ``max_concurrency`` limits the total number of task functions running
    across all files. A task that fails is recorded; its dependents are marked
    skipped, while unrelated tasks and files continue to run.
    """

    def __init__(self, tasks: Iterable[TaskSpec], *, max_concurrency: int = 8):
        if max_concurrency < 1:
            raise ValueError("max_concurrency must be at least 1")

        task_list = list(tasks)
        self.tasks = {task.name: task for task in task_list}
        if len(self.tasks) != len(task_list):
            raise ValueError("task names must be unique")
        if not self.tasks:
            raise ValueError("a workflow needs at least one task")
        self.max_concurrency = max_concurrency
        self._validate_graph()

    def _validate_graph(self) -> None:
        for task in self.tasks.values():
            missing = set(task.depends_on) - self.tasks.keys()
            if missing:
                raise ValueError(
                    f"task {task.name!r} depends on unknown task(s): "
                    f"{', '.join(sorted(missing))}"
                )
            if task.name in task.depends_on:
                raise ValueError(f"task {task.name!r} cannot depend on itself")

        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(name: str) -> None:
            if name in visiting:
                raise ValueError("task dependencies contain a cycle")
            if name in visited:
                return
            visiting.add(name)
            for dependency in self.tasks[name].depends_on:
                visit(dependency)
            visiting.remove(name)
            visited.add(name)

        for name in self.tasks:
            visit(name)

    async def run(self, files: Iterable[str | Path]) -> WorkflowResult:
        """Run this workflow for each path and return its per-file state."""

        semaphore = asyncio.Semaphore(self.max_concurrency)
        states = [
            FileState(
                path=Path(path),
                statuses={name: TaskStatus.PENDING for name in self.tasks},
            )
            for path in files
        ]

        async def run_file(state: FileState) -> None:
            executions: dict[str, asyncio.Task[TaskStatus]] = {}

            async def execute(name: str) -> TaskStatus:
                spec = self.tasks[name]
                dependency_statuses = await asyncio.gather(
                    *(executions[dependency] for dependency in spec.depends_on)
                )
                if any(status != TaskStatus.SUCCEEDED for status in dependency_statuses):
                    state.statuses[name] = TaskStatus.SKIPPED
                    return TaskStatus.SKIPPED

                try:
                    async with semaphore:
                        state.statuses[name] = TaskStatus.RUNNING
                        output = await spec.run(TaskContext(state, name))
                    state.outputs[name] = output
                    state.statuses[name] = TaskStatus.SUCCEEDED
                    return TaskStatus.SUCCEEDED
                except asyncio.CancelledError:
                    raise
                except Exception as error:
                    state.errors[name] = error
                    state.statuses[name] = TaskStatus.FAILED
                    return TaskStatus.FAILED

            # Create all tasks up front. Each task awaits its dependencies,
            # which lets independent branches start without a central queue.
            for name in self.tasks:
                executions[name] = asyncio.create_task(execute(name), name=f"{state.path}:{name}")
            await asyncio.gather(*executions.values())

        await asyncio.gather(*(run_file(state) for state in states))
        return WorkflowResult(states)
