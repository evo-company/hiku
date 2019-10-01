"""
    hiku.readers.simple
    ~~~~~~~~~~~~~~~~~~~

    Support for queries encoded using EDN format

"""
from ..edn import loads, Dict, List, Keyword, Tuple
from ..query import Node, Link, Field, merge


def _get_options(value):
    if len(value) < 2:
        raise TypeError('Missing options argument')
    elif len(value) > 2:
        raise TypeError('More arguments than expected')

    keyword_value, options_value = value
    if not isinstance(keyword_value, Keyword):
        raise TypeError('Names should be specified as keywords, not as {!r}'
                        .format(type(keyword_value)))

    if not isinstance(options_value, Dict):
        raise TypeError('Options should be specified as mapping, not as {!r}'
                        .format(type(options_value)))

    non_keyword = set((k, type(k)) for k in options_value.keys()
                      if not isinstance(k, Keyword))
    if non_keyword:
        keys_repr = ' '.join('{} {!r}'.format(k, t) for k, t in non_keyword)
        raise TypeError('Option names should be specified as keywords: {}'
                        .format(keys_repr))

    name = str(keyword_value)
    options = {str(k): v for k, v in options_value.items()}
    return name, options


def _extract(values):
    for value in values:
        if isinstance(value, Tuple):
            name, options = _get_options(value)
            yield Field(name, options)
        elif isinstance(value, Keyword):
            yield Field(str(value))
        elif isinstance(value, Dict):
            for key, val in value.items():
                if isinstance(key, Tuple):
                    name, options = _get_options(key)
                elif isinstance(key, Keyword):
                    name = str(key)
                    options = None
                else:
                    raise TypeError('Link name defined not as keyword, '
                                    'but as {!r}'.format(key))
                yield Link(name, transform(val), options)
        else:
            raise TypeError('Invalid node member: {!r}'.format(value))


def transform(value):
    if isinstance(value, List):
        return merge([Node(list(_extract(value)))])
    else:
        raise TypeError('Node should be defined as vector, '
                        '{!r} provided instead'.format(value))


def read(src):
    """Reads a query, encoded using EDN format

    Example:

    .. code-block:: python

        query = read('[{(:characters {:limit 100}) [:name]}]')
        result = engine.execute(graph, query)

    :param str src: EDN-encoded data structure
    :return: :py:class:`hiku.query.Node`, ready to execute query object
    """
    edn_ast = loads(src)
    return transform(edn_ast)
