from . import query, graph
from .nodes import NodeVisitor


class Ref(object):

    def __init__(self, backref, to):
        self.backref = backref
        self.to = to


class NamedRef(Ref):

    def __init__(self, backref, name, to):
        super(NamedRef, self).__init__(backref, to)
        self.name = name


def ref_to_req(ref, add_req=None):
    if ref is None:
        assert add_req is not None
        return add_req

    elif isinstance(ref.to, graph.Field):
        assert isinstance(ref, NamedRef), type(ref)
        assert add_req is None, repr(add_req)
        return ref_to_req(ref.backref,
                          query.Edge([query.Field(ref.name)]))

    elif isinstance(ref.to, graph.Edge):
        if isinstance(ref, NamedRef):
            edge = query.Edge([]) if add_req is None else add_req
            return ref_to_req(ref.backref,
                              query.Edge([query.Link(ref.name, edge)]))
        else:
            return ref_to_req(ref.backref, add_req)

    elif isinstance(ref.to, graph.Link):
        assert isinstance(ref, NamedRef), type(ref)
        edge = query.Edge([]) if add_req is None else add_req
        return ref_to_req(ref.backref,
                          query.Edge([query.Link(ref.name, edge)]))

    elif isinstance(ref.to, graph.Option):
        return None

    else:
        raise TypeError(type(ref.to))


class RequirementsExtractor(NodeVisitor):

    def __init__(self, env):
        self.env = env
        self._reqs = []

    @classmethod
    def extract(cls, env, expr):
        extractor = cls(env)
        extractor.visit(expr)
        return query.merge(extractor._reqs)

    def visit(self, node):
        ref = getattr(node, '__ref__', None)
        if ref is not None:
            req = ref_to_req(ref)
            if req is not None:
                self._reqs.append(req)
        super(RequirementsExtractor, self).visit(node)

    def visit_tuple(self, node):
        sym, args = node.values[0], node.values[1:]
        if sym.name in self.env:
            for arg, req in zip(args, self.env[sym.name].__requires__):
                if req is None:
                    continue
                if isinstance(arg.__ref__.to, (graph.Edge, graph.Link)):
                    assert isinstance(req, query.Edge), type(req)
                    self._reqs.append(ref_to_req(arg.__ref__, req))
                else:
                    assert isinstance(arg.__ref__.to, graph.Field), \
                        type(arg.__ref__.to)
                    assert isinstance(req, None), repr(req)
        super(RequirementsExtractor, self).visit_tuple(node)
