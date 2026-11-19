"""Example: process files through parallel branches and join at ``report``."""

import asyncio

from async_workflow import TaskContext, TaskSpec, Workflow


async def read_metadata(ctx: TaskContext) -> dict[str, str]:
    await asyncio.sleep(0.1)  # stand in for asynchronous I/O
    metadata = {"name": ctx.path.name, "extension": ctx.path.suffix}
    ctx.data["metadata"] = metadata
    return metadata


async def count_characters(ctx: TaskContext) -> int:
    await asyncio.sleep(0.2)  # stand in for an async file read
    count = len(ctx.path.name)
    ctx.data["character_count"] = count
    return count


async def make_report(ctx: TaskContext) -> dict[str, object]:
    # This task waits for both branches above. Their results are stored under
    # their task names and their shared per-file data is available as well.
    return {
        "metadata": ctx.outputs["metadata"],
        "character_count": ctx.outputs["character_count"],
    }


async def main() -> None:
    workflow = Workflow(
        [
            TaskSpec("metadata", read_metadata),
            TaskSpec("count", count_characters),
            TaskSpec("report", make_report, depends_on=("metadata", "count")),
        ],
        max_concurrency=4,
    )

    result = await workflow.run(["alpha.txt", "beta.csv", "gamma.json"])
    for file_state in result.files:
        print(file_state.path, file_state.statuses, file_state.outputs["report"])


if __name__ == "__main__":
    asyncio.run(main())
