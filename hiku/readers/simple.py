from ..edn import loads, Dict, List, Keyword
from ..query import Edge, Link, Field
from ..compat import text_type


def _extract(values):
    for value in values:
        if isinstance(value, Keyword):
            yield Field(text_type(value))
        elif isinstance(value, Dict):
            for key, val in value.items():
                yield Link(text_type(key), transform(val))
        else:
            raise ValueError('Invalid edge member: {!r}'.format(value))


def transform(value):
    if isinstance(value, List):
        return Edge(list(_extract(value)))
    else:
        raise ValueError('Edge should be defined as vector, '
                         '{!r} provided instead'.format(value))


def read(src):
    edn_ast = loads(src)
    return transform(edn_ast)
