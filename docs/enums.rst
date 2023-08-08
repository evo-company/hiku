Enums
=====

.. _enums-doc:

Enums are a special types that can be used to define a set of possible values for a field.

In graphql you can use enum type like this:

.. code-block::

    enum Status {
        ACTIVE
        DELETED
    }

    type Usr {
        id: ID!
        status: Status!
    }

    type Query {
        user: User!
    }


Enum from string
----------------

The simplest way to create enum in `hiku` from a list of strings:

.. code-block:: python

    from hiku.enum import Enum

    Enum('Status', ['ACTIVE', 'DELETED'])

Enum from python Enum
---------------------

You can also create enum from builtin python ``Enum`` type:

.. code-block:: python

    from enum import Enum as PyEnum
    from hiku.enum import Enum

    class Status(PyEnum):
        ACTIVE = 'active'
        DELETED = 'deleted'

    Enum.from_builtin(Status)

In this example:

- ``EnumFromBuiltin`` will use ``Enum.__name__`` as a enum name.
- ``EnumFromBuiltin`` will use ``Enum.__members__`` to get a list of possible values.
- ``EnumFromBuiltin`` will use ``member.name`` to get a value name:

So this python enum:

.. code-block:: python

    class Status(PyEnum):
        ACTIVE = 1
        DELETED = 2

is equivalent to this enum in graphql:

.. code-block:: python

    enum Status { ACTIVE, DELETED }

If you want to specify different name you can pass ``name`` argument to ``Enum.from_builtin`` method:

.. code-block:: python

    Enum.from_builtin(Status, name='User_Status')

.. note::

    If you use builtin python ``Enum``, then you MUST return enum value from the resolver function, otherwise ``hiku`` will raise an error.

    .. code-block:: python

        def user_fields_resolver(fields, ids):
            def get_field(field, user):
                if field.name == 'id':
                    return user.id
                elif field.name == 'status':
                    return Status(user.status)

            return [[get_field(field, users[id]) for field in fields] for id in ids]

Lets look at the full example on how to use enum type in `hiku`:

.. code-block:: python

    from hiku.graph import Field, Graph, Link, Node, Root
    from hiku.enum import Enum
    from hiku.types import ID, TypeRef, Optional, EnumRef

    users = {
        1: {'id': "1", 'status': 'ACTIVE'},
    }

    def user_fields_resolver(fields, ids):
        def get_field(field, user):
            if field.name == 'id':
                return user['id']
            elif field.name == 'status':
                return user['status']

        return [[get_field(field, users[id]) for field in fields] for id in ids]

    def get_user(opts):
        return 1

    enums = [
        Enum('Status', ['ACTIVE', 'DELETED'])
    ]

    GRAPH = Graph([
        Node('User', [
            Field('id', ID, user_fields_resolver),
            Field('status', EnumRef['Status'], user_fields_resolver),
        ]),
        Root([
            Link('user', TypeRef['User'], get_user, requires=None),
        ]),
    ], enums=enums)

Lets decode the example above:

- ``Enum`` type is defined with a name and a list of possible values.
- ``User.status`` field has type ``EnumRef['Status']`` which is a reference to the ``Status`` enum type.
- ``status`` field returns ``user.status`` which is plain string.

If we run this query:

.. code-block:: python

    query {
        user {
            id
            status
        }
    }

We will get the following result:

.. code-block::

    {
        'id': "1",
        'status': 'ACTIVE',
    }


Custom Enum type
----------------

You can also create custom enum type by subclassing ``hiku.enum.BaseEnum`` class:

.. code-block:: python

    from hiku.enum import BaseEnum

    class IntToStrEnum(BaseEnum):
        _MAPPING = {1: 'one', 2: 'two', 3: 'three'}
        _INVERTED_MAPPING = {v: k for k, v in _MAPPING.items()}

        def __init__(self, name: str, values: list[int], description: str = None):
            super().__init__(name, [_MAPPING[v] for v in values], description)

        def parse(self, value: str) -> int:
            return self._INVERTED_MAPPING[value]

        def serialize(self, value: int) -> str:
            return self._MAPPING[value]

Enum serialization
------------------

- ``Enum`` values are serialized into strings. If value is not in the list of possible values, then ``hiku`` will raise an error.
- ``EnumFromBuiltin`` values which are instances of ``Enum`` class are serialized into strings by calling **.name** on enum value. If value is not an instance of ``Enum`` class, then ``hiku`` will raise an error.

You can also define custom serialization for your enum type by subclassing ``hiku.enum.BaseEnum`` class.

Enum parsing
------------

- ``Enum`` parses values into strings. If value is not in the list of possible values, then ``hiku`` will raise an error.
- ``EnumFromBuiltin`` parses values into enum values by calling **Enum(value)**. If value is not in the list of possible values, then ``hiku`` will raise an error.

You can also define custom parsing for your enum type by subclassing ``hiku.enum.BaseEnum`` class.

Enum as an input argument
-------------------------

You can use enum as an field input argument:

.. code-block:: python

    import enum
    from hiku.enum import Enum
    from hiku.graph import Node, Root, Field, Link, Graph, Option
    from hiku.types import ID, TypeRef, Optional, EnumRef

    users = [
        {'id': "1", 'status': Status.ACTIVE},
        {'id': "2", 'status': Status.DELETED},
    ]

    def link_users(opts):
        ids = []
        for user in users:
            # here opts['status'] will be an instance of Status enum
            if user['status'] == opts['status']:
                ids.append(user.id)

       return ids


    class Status(enum.Enum):
        ACTIVE = 'active'
        DELETED = 'deleted'

    GRAPH = Graph([
        Node('User', [
            Field('id', ID, user_fields_resolver),
            Field('status', EnumRef['Status'], user_fields_resolver),
        ]),
        Root([
            Link(
                'users',
                Sequence[TypeRef['User']],
                link_users,
                requires=None,
                options=[
                    Option('status', EnumRef['Status'], default=Status.ACTIVE),
                ]
           ),
        ]),
    ], enums=[Enum.from_builtin(Status)])


Now you can use enum as a field argument:

.. code-block::

    query {
        users(status: DELETED) {
            id
            status
        }
    }

The result will be:

.. code-block::

    [{
        "id": "2",
        "status": "DELETED",
    }]
