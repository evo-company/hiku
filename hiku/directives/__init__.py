from typing import (
    Optional,
    Union,
    TYPE_CHECKING,
    Any,
)

if TYPE_CHECKING:
    from hiku.graph import Field, Link


class DirectiveBase:
    pass


class Deprecated(DirectiveBase):
    """
    https://spec.graphql.org/June2018/#sec--deprecated
    """
    def __init__(self, reason: Optional[str] = None):
        self.reason = reason

    def accept(self, visitor: Any) -> Any:
        return visitor.visit_deprecated_directive(self)


def get_deprecated(field: Union['Field', 'Link']) -> Optional[Deprecated]:
    """Get deprecated directive"""
    return next(
        (d for d in field.directives if isinstance(d, Deprecated)),
        None
    )
