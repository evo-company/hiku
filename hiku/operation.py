import enum

from typing import Optional, TYPE_CHECKING

from graphql.language import ast

if TYPE_CHECKING:
    from hiku.query import Node


class OperationType(enum.Enum):
    """Enumerates GraphQL operation types"""

    #: query operation
    QUERY = ast.OperationType.QUERY
    #: mutation operation
    MUTATION = ast.OperationType.MUTATION
    #: subscription operation
    SUBSCRIPTION = ast.OperationType.SUBSCRIPTION


class Operation:
    """Represents requested GraphQL operation"""

    __slots__ = ("type", "query", "name")

    def __init__(
        self, type_: OperationType, query: "Node", name: Optional[str] = None
    ):
        #: type of the operation
        self.type = type_
        #: operation's query
        self.query = query
        #: optional name of the operation
        self.name = name
