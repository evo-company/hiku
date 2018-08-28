Changes in 0.5
==============

Unreleased
~~~~~~~~~~

  - Added Python 3.7 compatibility
  - Added ``Any`` type support for GraphQL introspection, this type also will
    be used for fields, which are incompatible with GraphQL's type system
  - Added ability to specify GraphQL operation name if client submits several
    operations in one document
  - Added ability to specify data types

Backward-incompatible changes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

  - Removed ability to define Node in Root node in favor of complex types and
    data types
