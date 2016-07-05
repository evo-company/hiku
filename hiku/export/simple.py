from ..edn import Keyword, Dict, Tuple, List


class Exporter(object):

    def visit(self, obj):
        return obj.accept(self)

    def visit_field(self, obj):
        f = Keyword(obj.name)
        if obj.options:
            f = Tuple([f, Dict((Keyword(k), v)
                               for k, v in obj.options.items())])
        return f

    def visit_link(self, obj):
        l = Keyword(obj.name)
        if obj.options:
            l = Tuple([l, Dict((Keyword(k), v)
                               for k, v in obj.options.items())])
        return Dict([(l, self.visit(obj.edge))])

    def visit_edge(self, obj):
        return List(self.visit(f) for f in obj.fields.values())


def export(query):
    return Exporter().visit(query)
