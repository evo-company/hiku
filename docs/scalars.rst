Scalars
=====

.. _scalars-doc:

Scalar are a types that used to represent leaves of a graph.

Hiku has a few built-in scalars according to the GraphQL specification:

- ``ID`` - a string that represents unique identifier.
- ``Int`` - a signed 32‐bit integer.
- ``Float`` - a signed double-precision floating-point value.
- ``String`` - a UTF‐8 character sequence.
- ``Boolean`` - a boolean value: ``true`` or ``false``.
- ``Any`` - any value.

Although these scalar types is sufficient to represent the majority of data types returned from graph,
it is sometimes necessary to define custom scalar types.

``Hiku`` has a few additional custom scalars:

- ``Date`` - a date value in ISO 8601 format.
- ``DateTime`` - a date and time value in ISO 8601 format.
- ``UUID`` - a UUID value.

.. note::

    Hiku built-in custom scalars are not enabled by default.
    You need to enable them explicitly, by adding each scalar that you need
    to the ``scalars`` argument of the ``Graph`` constructor.

Custom scalars
--------------

If builtin scalars do not cover your specific needs, you can define custom scalar type like this:

.. code-block:: python

    from datetime import datetime

    from hiku.graph import Field, Graph, Link, Node, Root
    from hiku.scalar import Scalar
    from hiku.types import ID, TypeRef, Optional

    users = {
        1: {'id': "1", 'dateCreated': datetime(2023, 6, 15, 12, 30, 59, 0)},
    }

    class YMDDate(Scalar):
        """Format datetime info %Y-%m-%d"""
        @classmethod
        def parse(cls, value):
            return datetime.strptime(value, '%Y-%m-%d').date()

        @classmethod
        def serialize(cls, value):
            return value.strftime('%Y-%m-%d')

    def user_fields_resolver(fields, ids):
        def get_field(field, user):
            if field.name == 'id':
                return user['id']
            elif field.name == 'dateCreated':
                return user['dateCreated']

        return [[get_field(field, users[id]) for field in fields] for id in ids]

    def get_user(opts):
        return 1

    scalars = [YMDDate]

    GRAPH = Graph([
        Node('User', [
            Field('id', ID, user_fields_resolver),
            Field('dateCreated', YMDDate, user_fields_resolver),
        ]),
        Root([
            Link('user', TypeRef['User'], get_user, requires=None),
        ]),
    ], scalars=scalars)

Lets look at the example above:

- ``YMDDate`` type is subclassing ``Scalar` and implements ``parse`` and ``serialize`` methods.
- ``User.dateCreated`` field has type ``YMDDate`` which is a custom scalar.
- ``dateCreated`` field returns ``user.dateCreated`` which is a ``datetime`` instance.
- ``YMDDate.parse`` method will be called to parse ``datetime`` instance into ``%Y-%m-%`` formated string.

Now lets look at the query:

.. code-block:: python

    query {
        user {
            id
            dateCreated
        }
    }

The result will be:

.. code-block::

    {
        'id': "1",
        'dateCreated': '2023-06-15',
    }


.. note::

    By default scalar name will be the name of a class.

    If you want to specify a custom name for scalar or add description,
    you can use ``@scalar()`` decorator:

    .. code-block:: python

        @scalar('YearMonthDayDate', 'Format datetime info %Y-%m-%d')
        class YMDDate(Scalar):
            ...