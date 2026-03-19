from hiku.engine import _is_hashable


hashable_objects = [
    1,
    "string",
    (1, 2, 3),
    None,
    True,
    frozenset([1, 2]),
    3.14,
    (1, "a", None, (2, 3)),
]

unhashable_objects = [
    [1, 2, 3],
    {"a": 1},
    {1, 2, 3},
    [1, [2, 3]],
]


def test_is_hashable_hashable(benchmark):
    benchmark.pedantic(
        lambda: [_is_hashable(obj) for obj in hashable_objects],
        iterations=10,
        rounds=1000,
    )


def test_is_hashable_unhashable(benchmark):
    benchmark.pedantic(
        lambda: [_is_hashable(obj) for obj in unhashable_objects],
        iterations=10,
        rounds=1000,
    )


def test_is_hashable_mixed_list(benchmark):
    mixed = hashable_objects + unhashable_objects

    benchmark.pedantic(
        lambda: all(map(_is_hashable, mixed)),
        iterations=10,
        rounds=1000,
    )
