import abc
from typing import (
    Any,
    Dict,
    List,
)


class BaseCache(abc.ABC):
    @abc.abstractmethod
    def get_many(self, keys: List[str]) -> Dict[str, Any]:
        """Result must contain only keys which were cached"""
        raise NotImplementedError()

    @abc.abstractmethod
    def set_many(self, items: Dict[str, Any], ttl: int) -> None:
        raise NotImplementedError()
