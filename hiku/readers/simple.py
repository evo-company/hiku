from ..edn import loads, Dict, List, Keyword, Tuple
from ..query import Edge, Link, Field
from ..compat import text_type


def _iter_options(args):
    i = iter(args)
    while True:
        key = next(i)
        if not isinstance(key, Keyword):
            raise TypeError('Option keyword expected, {} received instead'
                            .format(key))
        try:
            value = next(i)
        except StopIteration:
            raise TypeError('Missing keyword value')
        else:
            yield (text_type(key), value)


def _extract(values):
    for value in values:
        if isinstance(value, Tuple):
            name = text_type(value[0])
            options = dict(_iter_options(value[1:]))
            yield Field(name, options)
        elif isinstance(value, Keyword):
            yield Field(text_type(value))
        elif isinstance(value, Dict):
            for key, val in value.items():
                if isinstance(key, Tuple):
                    name = text_type(key[0])
                    options = dict(_iter_options(key[1:]))
                elif isinstance(key, Keyword):
                    name = text_type(key)
                    options = None
                else:
                    raise TypeError('Link name defined not as keyword, '
                                    'but as {!r}'.format(key))
                yield Link(name, transform(val), options)
        else:
            raise TypeError('Invalid edge member: {!r}'.format(value))


def transform(value):
    if isinstance(value, List):
        return Edge(list(_extract(value)))
    else:
        raise TypeError('Edge should be defined as vector, '
                        '{!r} provided instead'.format(value))


def read(src):
    edn_ast = loads(src)
    return transform(edn_ast)
