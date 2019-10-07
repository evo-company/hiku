from ..edn import Keyword, Dict, Tuple, List, Set
from ..query import QueryVisitor


def _encode(value):
    if value is None:
        return value
    elif isinstance(value, (str, bool, int, float)):
        return value
    elif isinstance(value, list):
        return List(_encode(val) for val in value)
    elif isinstance(value, dict):
        return Dict((Keyword(key), _encode(val)) for key, val in value.items())
    elif isinstance(value, (set, frozenset)):
        return Set(_encode(val) for val in value)
    else:
        raise TypeError('Unsupported type: {!r}'.format(value))


class Exporter(QueryVisitor):

    def visit_field(self, obj):
        f = Keyword(obj.name)
        if obj.options is not None:
            f = Tuple([f, _encode(obj.options)])
        return f

    def visit_link(self, obj):
        lnk = Keyword(obj.name)
        if obj.options is not None:
            lnk = Tuple([lnk, _encode(obj.options)])
        return Dict([(lnk, self.visit(obj.node))])

    def visit_node(self, obj):
        return List(self.visit(f) for f in obj.fields)


def export(query):
    return Exporter().visit(query)
