Changes in 0.3
==============

0.3.4
~~~~~

- Added Protocol Buffers support

0.3.3
~~~~~

- Added Python 3.6 support

0.3.2
~~~~~

- Fixed bug with result denormalization for links with Optional types

0.3.1
~~~~~

- Added basic GraphQL support

0.3.0
~~~~~

- Project structure refactoring

Backward-incompatible changes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- :py:class:`hiku.result.Result` is not a subclass of ``defaultdict``
  anymore, it even not implements fully ``Mapping`` interface, only
  ``__getitem__`` is implemented

- Moved :py:mod:`hiku.expr` to the :py:mod:`hiku.expr.core`
- Moved :py:mod:`hiku.checker` to the :py:mod:`hiku.expr.checker`
- Moved :py:mod:`hiku.compiler` to the :py:mod:`hiku.expr.compiler`
- Moved :py:mod:`hiku.nodes` to the :py:mod:`hiku.expr.nodes`
- Moved :py:mod:`hiku.refs` to the :py:mod:`hiku.expr.refs`

- Renamed :py:class:`hiku.graph.AbstractEdge` into :py:class:`hiku.graph.AbstractNode`
- Renamed :py:class:`hiku.graph.Edge` into :py:class:`hiku.graph.Node`
- Renamed :py:class:`hiku.query.Edge` into :py:class:`hiku.query.Node`
