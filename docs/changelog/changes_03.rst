Changes in 0.3
==============

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
