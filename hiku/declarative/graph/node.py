"""Node concept and some code from strawberry :D"""

import typing
import inspect
import dataclasses

import hiku.graph

from collections.abc import Sequence


if typing.TYPE_CHECKING:
    from .field import Fieldgen


_T = typing.TypeVar("_T")
_TContext = typing.TypeVar("_TContext", bound=dict)


class Node(typing.Generic[_T]):
    name: str
    fields: list
    description: str | None = None
    directives: list | None = None

    def accept(self, visitor: typing.Any) -> typing.Any:
        return visitor.visit_node_decl(self)


class NodeProto(typing.Protocol[_T, _TContext]):
    field: "typing.ClassVar[Fieldgen[_T, _TContext]]"  # type: ignore


_TNode = typing.TypeVar("_TNode", bound=NodeProto)


@typing.dataclass_transform(kw_only_default=True)
def node(
    cls: type[_TNode] | None = None,
    *,
    name: str | None = None,
    description: str | None = None,
    directives: Sequence[object] = (),
) -> type[_TNode]:
    def wrap(cls: type[_TNode]) -> type[_TNode]:
        if not inspect.isclass(cls):
            raise TypeError(f"{cls} is not a class")

        wrapped = _wrap_dataclass(cls)
        return _process_type(
            wrapped,
            name=name,
            is_input=is_input,
            is_interface=is_interface,
            description=description,
            directives=directives,
            extend=extend,
        )

    if cls is None:
        return wrap

    return wrap(cls)


def _wrap_dataclass(cls: type) -> type:
    _check_field_annotations(cls)

    dclass = dataclasses.dataclass(kw_only=True)(cls)

    return dclass


def _check_field_annotations(cls):
    cls_annotations = cls.__dict__.get("__annotations__", {})
    cls.__annotations__ = cls_annotations

    for field_name, field_ in cls.__dict__.items():
        if not isinstance(field_, (StrawberryField, dataclasses.Field)):
            # Not a dataclasses.Field, nor a StrawberryField. Ignore
            continue

        # If the field is a StrawberryField we need to do a bit of extra work
        # to make sure dataclasses.dataclass is ready for it
        if isinstance(field_, StrawberryField):

            # Make sure the cls has an annotation
            if field_name not in cls_annotations:
                # If the field uses the default resolver, the field _must_ be
                # annotated
                if not field_.base_resolver:
                    raise MissingFieldAnnotationError(field_name)

                # The resolver _must_ have a return type annotation
                # TODO: Maybe check this immediately when adding resolver to
                #       field
                if field_.base_resolver.type_annotation is None:
                    raise MissingReturnAnnotationError(field_name)

                cls_annotations[
                    field_name
                ] = field_.base_resolver.type_annotation

            # TODO: Make sure the cls annotation agrees with the field's type
            # >>> if cls_annotations[field_name] != field.base_resolver.type:
            # >>>     # TODO: Proper error
            # >>>    raise Exception

        # If somehow a non-StrawberryField field is added to the cls without annotations
        # it raises an exception. This would occur if someone manually uses
        # dataclasses.field
        if field_name not in cls_annotations:
            # Field object exists but did not get an annotation
            raise MissingFieldAnnotationError(field_name)


def _process_type(
    cls,
    *,
    name: str | None = None,
    description: str | None = None,
    directives: Sequence | None = (),
    extend: bool = False,
):
    name = name or to_camel_case(cls.__name__)
    fields = _get_fields(cls)

    cls.__node__ = hiku.graph.Node(
        name=name,
        fields=fields,
        description=description,
        directives=directives,
    )

    return cls
