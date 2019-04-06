import pytest

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
