from typing import Any

from hiku.directives import DirectiveBase


class Key(DirectiveBase):
    """
    https://www.apollographql.com/docs/federation/federation-spec/#key
    """

    def __init__(self, fields: str) -> None:
        self.fields = fields

    def accept(self, visitor: Any) -> Any:
        return visitor.visit_key_directive(self)


class Provides(DirectiveBase):
    """
    https://www.apollographql.com/docs/federation/federation-spec/#provides
    """

    def __init__(self, fields: str) -> None:
        self.fields = fields

    def accept(self, visitor: Any) -> Any:
        return visitor.visit_provides_directive(self)


class Requires(DirectiveBase):
    """
    https://www.apollographql.com/docs/federation/federation-spec/#requires
    """

    def __init__(self, fields: str) -> None:
        self.fields = fields

    def accept(self, visitor: Any) -> Any:
        return visitor.visit_requires_directive(self)


class External(DirectiveBase):
    """
    https://www.apollographql.com/docs/federation/federation-spec/#external
    """

    def accept(self, visitor: Any) -> Any:
        return visitor.visit_external_directive(self)


class Extends(DirectiveBase):
    """
    Apollo Federation supports using an @extends directive in place of extend
    type to annotate type references
    https://www.apollographql.com/docs/federation/federation-spec/
    """

    def accept(self, visitor: Any) -> Any:
        return visitor.visit_extends_directive(self)
