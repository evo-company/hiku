from abc import abstractmethod
from typing import List

from hiku.graph import Graph
from hiku.query import Node, QueryVisitor


class QueryValidator(QueryVisitor):
    @abstractmethod
    def validate(self, query: Node, graph: Graph) -> List[str]:
        """Returns list of errors"""
        ...
