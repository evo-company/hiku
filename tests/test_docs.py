from hiku.compat import PY3

if PY3:
    from docs.guide.database import test_character_to_actors  # noqa
    from docs.guide.database import test_actor_to_character  # noqa
    from docs.guide.subgraph import test_low_level  # noqa
    from docs.guide.subgraph import test_high_level  # noqa
