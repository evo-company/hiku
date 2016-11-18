from ..edn import Keyword, Dict, Tuple, List
from ..query import QueryVisitor


class Exporter(QueryVisitor):

    def visit_field(self, obj):
        f = Keyword(obj.name)
        if obj.options is not None:
            f = Tuple([f, Dict((Keyword(k), v)
                               for k, v in obj.options.items())])
        return f

    def visit_link(self, obj):
        l = Keyword(obj.name)
        if obj.options is not None:
            l = Tuple([l, Dict((Keyword(k), v)
                               for k, v in obj.options.items())])
        return Dict([(l, self.visit(obj.node))])

    def visit_node(self, obj):
        return List(self.visit(f) for f in obj.fields)


def export(query):
    return Exporter().visit(query)
