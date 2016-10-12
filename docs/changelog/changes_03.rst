Changes in 0.3
==============

Backward-incompatible changes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- :py:class:`hiku.result.Result` is not a subclass of ``defaultdict``
  anymore, it even not implements fully ``Mapping`` interface, only
  ``__getitem__`` is implemented
