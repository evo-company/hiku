import asyncio

import pytest

from hiku.executors.queue import Queue, Workflow
from hiku.executors.asyncio import AsyncIOExecutor


def func():
    pass


def func2():
    return []


def gen():
    yield


def gen2():
    yield from gen()


async def coroutine():
    return 'smiting'


@pytest.mark.asyncio
async def test_awaitable_check(event_loop):
    executor = AsyncIOExecutor(event_loop)

    with pytest.raises(TypeError) as func_err:
        executor.submit(func)
    func_err.match('returned non-awaitable object')

    with pytest.raises(TypeError) as func2_err:
        executor.submit(func2)
    func2_err.match('returned non-awaitable object')

    with pytest.raises(TypeError) as gen_err:
        executor.submit(gen)
    gen_err.match('returned non-awaitable object')

    with pytest.raises(TypeError) as gen2_err:
        executor.submit(gen2)
    gen2_err.match('returned non-awaitable object')

    assert (await executor.submit(coroutine)) == 'smiting'


@pytest.mark.asyncio
async def test_cancellation(event_loop):
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
            raise AssertionError('impossible')

    executor = AsyncIOExecutor(event_loop)

    queue = Queue(executor)
    queue.submit(queue.fork(None), proc)

    task = event_loop.create_task(executor.process(queue, TestWorkflow()))
    await asyncio.wait([task], timeout=0.01)
    assert not task.done()
    task.cancel()
    await asyncio.wait([task], timeout=0.001)
    assert task.done()
    assert task.cancelled() is True
    assert result == [1, 2]
