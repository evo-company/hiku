from abc import abstractmethod

from hiku.graph import Graph
from hiku.query import Node, QueryVisitor


class QueryValidator(QueryVisitor):
    @abstractmethod
    def validate(self, query: Node, graph: Graph) -> list[str]:
        """Returns list of errors"""
        ...
