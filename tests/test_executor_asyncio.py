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
