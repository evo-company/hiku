__all__ = ["GraphQLError"]


class GraphQLError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message
