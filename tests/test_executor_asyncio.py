import asyncio
import inspect
from unittest.mock import Mock

import pytest

from hiku.executors.asyncio import AsyncIOExecutor
from hiku.executors.queue import Queue, Workflow


def func():
    pass


def func2():
    return []


def gen():
    yield


def gen2():
    yield from gen()


async def coroutine():
    return "smiting"


@pytest.mark.asyncio
async def test_awaitable_check__async_only():
    executor = AsyncIOExecutor(deny_sync=True)

    with pytest.raises(TypeError) as func_err:
        executor.submit(func)
    func_err.match("returned non-awaitable object")

    with pytest.raises(TypeError) as func2_err:
        executor.submit(func2)
    func2_err.match("returned non-awaitable object")

    with pytest.raises(TypeError) as gen_err:
        executor.submit(gen)
    gen_err.match("returned non-awaitable object")

    with pytest.raises(TypeError) as gen2_err:
        executor.submit(gen2)
    gen2_err.match("returned non-awaitable object")

    assert (await executor.submit(coroutine)) == "smiting"


@pytest.mark.asyncio
async def test_awaitable_check__sync_async():
    executor = AsyncIOExecutor()

    assert await executor.submit(func) is None
    assert await executor.submit(func2) == []
    assert await executor.submit(gen)
    assert await executor.submit(gen2)
    assert (await executor.submit(coroutine)) == "smiting"


@pytest.mark.asyncio
async def test_awaitable_check__sync_called_once():
    executor = AsyncIOExecutor()
    func_mock = Mock(side_effect=func)
    assert await executor.submit(func_mock) is None
    func_mock.assert_called_once()


@pytest.mark.asyncio
async def test_cancellation():
    loop = asyncio.get_running_loop()
    result = []

    async def proc():
        result.append(1)
        try:
            while True:
                await asyncio.sleep(1)
        finally:
            result.append(2)

    class TestWorkflow(Workflow):
        def result(self):
            raise AssertionError("impossible")

    executor = AsyncIOExecutor()

    queue = Queue(executor)
    queue.submit(queue.fork(None), proc)

    task = loop.create_task(executor.process(queue, TestWorkflow()))
    await asyncio.wait([task], timeout=0.01)
    assert not task.done()
    task.cancel()
    await asyncio.wait([task], timeout=0.01)
    assert task.done()
    assert task.cancelled() is True
    assert result == [1, 2]


@pytest.mark.asyncio
async def test_failed_task_cancels_pending_tasks():
    result = []

    async def failing():
        raise TimeoutError("connect timeout")

    async def proc():
        result.append(1)
        try:
            await asyncio.sleep(1)
        finally:
            result.append(2)

    class TestWorkflow(Workflow):
        def result(self):
            raise AssertionError("impossible")

    executor = AsyncIOExecutor()

    queue = Queue(executor)
    task_set = queue.fork(None)
    queue.submit(task_set, proc)
    failing_fut = queue.submit(task_set, failing)
    queue.add_callback(failing_fut, failing_fut.result)

    with pytest.raises(TimeoutError, match="connect timeout"):
        await executor.process(queue, TestWorkflow())

    assert result == [1, 2]
    assert all(task.done() for task in queue.__futures__)


@pytest.mark.asyncio
async def test_failed_resolver_leaves_no_pending_tasks():
    from hiku.graph import Field, Graph, Root
    from hiku.schema import Schema
    from hiku.types import String

    async def failing(fields):
        raise TimeoutError("connect timeout")

    async def slow(fields):
        await asyncio.sleep(1)
        return ["slow"]

    graph = Graph(
        [Root([Field("failing", String, failing), Field("slow", String, slow)])]
    )
    schema = Schema(AsyncIOExecutor(), graph)

    with pytest.raises(TimeoutError, match="connect timeout"):
        await schema.execute("{ failing slow }")

    current = asyncio.current_task()
    assert [t for t in asyncio.all_tasks() if t is not current] == []
