from typing import Any, Callable, Optional, Union

from hiku.scalar import ScalarMeta
from hiku.types import GenericMeta, OptionalMeta, SequenceMeta


def serialize(
    type_: Optional[Union[GenericMeta, ScalarMeta]],
    value: Any,
    callback: Callable[[Any], Any],
) -> Any:
    """Serializes value recursively.
    Handles Optional and Sequence types.
    """
    if type_ is None:
        return value

    if isinstance(type_, SequenceMeta):
        return [serialize(type_.__item_type__, v, callback) for v in value]
    elif isinstance(type_, OptionalMeta):
        if value is None:
            return None

        return serialize(type_.__type__, value, callback)

    return callback(value)
