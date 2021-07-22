from typing import Optional

from hiku.graph import Field


class DirectiveBase:
    pass


class Deprecated(DirectiveBase):
    """
    https://spec.graphql.org/June2018/#sec--deprecated
    """
    def __init__(self, reason: Optional[str] = None):
        self.reason = reason

    def accept(self, visitor):
        return visitor.visit_deprecated_directive(self)


def get_deprecated(field: Field) -> Optional[Deprecated]:
    """Get deprecated directive"""
    return next(
        (d for d in field.directives if isinstance(d, Deprecated)),
        None
    )
