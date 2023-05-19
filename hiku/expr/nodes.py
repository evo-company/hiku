import typing as t


VisitorT = t.Union["NodeTransformer", "NodeVisitor"]


class Node:
    def accept(self, visitor: VisitorT) -> t.Any:
        raise NotImplementedError(type(self))


class Symbol(Node):
    def __init__(self, name: str) -> None:
        self.name = name

    def __repr__(self) -> str:
        return self.name

    def accept(self, visitor: VisitorT) -> t.Any:
        return visitor.visit_symbol(self)


class Keyword(Node):
    def __init__(self, name: str) -> None:
        self.name = name

    def __repr__(self) -> str:
        return ":{}".format(self.name)

    def accept(self, visitor: VisitorT) -> t.Any:
        return visitor.visit_keyword(self)


class Tuple(Node):
    def __init__(self, values: t.List[Node]) -> None:
        self.values = tuple(values)

    def __repr__(self) -> str:
        return "({})".format(" ".join(map(repr, self.values)))

    def accept(self, visitor: VisitorT) -> t.Any:
        return visitor.visit_tuple(self)


class List(Node):
    def __init__(self, values: t.List[Node]) -> None:
        self.values = tuple(values)

    def __repr__(self) -> str:
        return "[{}]".format(" ".join(map(repr, self.values)))

    def accept(self, visitor: VisitorT) -> t.Any:
        return visitor.visit_list(self)


class Dict(Node):
    def __init__(self, values: t.List[Node]):
        self.values = tuple(values)

    def __repr__(self) -> str:
        return "{{{}}}".format(" ".join(map(repr, self.values)))

    def accept(self, visitor: VisitorT) -> t.Any:
        return visitor.visit_dict(self)


class NodeVisitor:
    def visit(self, node: Node) -> t.Any:
        if hasattr(node, "accept"):
            node.accept(self)
        else:
            self.generic_visit(node)

    def generic_visit(self, node: Node) -> t.Any:
        pass

    def visit_symbol(self, node: Symbol) -> t.Any:
        pass

    def visit_keyword(self, node: Keyword) -> t.Any:
        pass

    def visit_tuple(self, node: Tuple) -> t.Any:
        for value in node.values:
            self.visit(value)

    def visit_list(self, node: List) -> t.Any:
        for value in node.values:
            self.visit(value)

    def visit_dict(self, node: Dict) -> t.Any:
        for value in node.values:
            self.visit(value)


class NodeTransformer:
    def visit(self, node: Node) -> t.Any:
        if hasattr(node, "accept"):
            return node.accept(self)

        return self.generic_visit(node)

    def generic_visit(self, node: Node) -> Node:
        return node

    def visit_symbol(self, node: Symbol) -> Symbol:
        return Symbol(node.name)

    def visit_keyword(self, node: Keyword) -> Keyword:
        return Keyword(node.name)

    def visit_tuple(self, node: Tuple) -> Tuple:
        return Tuple([self.visit(value) for value in node.values])

    def visit_list(self, node: List) -> List:
        return List([self.visit(value) for value in node.values])

    def visit_dict(self, node: Dict) -> Dict:
        return Dict([self.visit(value) for value in node.values])
