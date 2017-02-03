from ..types import SequenceMeta, OptionalMeta
from ..query import Field, Link, merge
from ..graph import Node as GraphNode, Link as GraphLink, Field as GraphField
from ..graph import Many, Maybe


def _set_fields(pb_obj, result, node):
    for f in node.fields:
        setattr(pb_obj, f.name, result[f.name])


def _populate_node(pb_node, graph, graph_node, result, query_node):
    for f in query_node.fields:
        if isinstance(f, Field):
            setattr(pb_node, f.name, result[f.name])
        elif isinstance(f, Link):
            _transform_link(getattr(pb_node, f.name), graph,
                            graph_node.fields_map[f.name], result[f.name], f)
        else:
            raise TypeError(type(f))


def _transform_link(pb_obj, graph, graph_obj, result, query_obj):
    # complex field type
    if isinstance(graph_obj, GraphField):
        type_ = graph_obj.type
        if isinstance(type_, SequenceMeta):
            for item in result:
                pb_item = pb_obj.add()
                _set_fields(pb_item, item, query_obj.node)
        elif isinstance(type_, OptionalMeta) and result is None:
            pass
        else:
            _set_fields(pb_obj, result, query_obj.node)

    # regular link to node
    elif isinstance(graph_obj, GraphLink):
        graph_node = graph.nodes_map[graph_obj.node]
        if graph_obj.type_enum is Many:
            for v in result:
                pb_item = pb_obj.add()
                _populate_node(pb_item, graph, graph_node, v, query_obj.node)
        elif graph_obj.type_enum is Maybe and result is None:
            pass
        else:
            _populate_node(pb_obj, graph, graph_node, result, query_obj.node)

    # node in root node
    else:
        assert isinstance(graph_obj, GraphNode)
        _populate_node(pb_obj, graph, graph_obj, result, query_obj.node)


def populate(pb_root, graph, result, query):
    _populate_node(pb_root, graph, graph.root, result, merge([query]))
