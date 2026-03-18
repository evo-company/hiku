Caching
=======

.. _caching-doc:

Caching is experimental feature.

For now only non-root link will be cached.

How it works
~~~~~~~~~~~~

By specifying ``@cached`` directive on query node we can instruct backend to
cache node result.

Rules:

- ``@cached`` directive can be specified only on non-root query node

- cached key will be generated from:

    - node arguments
    - node fields and all child nodes and its fields and so on
    - node fields arguments
    - value from `requires`

- we store to cache all fields from node + all fields of all child nodes and so on.

Consider this graph:

.. code-block:: python

    Graph([
        Node('Product', [
            Field('id'),
            Field('name'),
            Field('company_id'),
            Link('company', TypeRef['Company'], requires='company_id'),
        ]),
        Node('Company', [
            Field('id'),
            Field('name', options=[Option('capitalize', Optional[Boolean], default=False)]),
        ]),
        Root([
            Link('product', TypeRef['Product'])
        ])
    ])


So in next 3 queries `company` node will be cached separately:

.. code-block::  graphql

    query {
        product(id: 1) {
            name
            company @cached(ttl: 10) {
                id
            }
        }
    }

``company`` here has ``name`` field, which is the difference between this query and
previous one.

.. code-block:: graphql

    query {
        product(id: 1) {
            name
            company @cached(ttl: 10) {
                id
                name
            }
        }
    }

``company`` here has ``name`` field but with argument, which is the difference between this query and
previous one.


.. code-block:: graphql

    query {
        product(id: 1) {
            name
            company @cached(ttl: 10) {
                id
                name(capitalize: true)
            }
        }
    }

How data stored in cache
~~~~~~~~~~~~~~~~~~~~~~~~

Although it is an implementation detail and cache layout may change in the future
it is worth to know how data is stored in cache.

Data is stored in cache as a part of index.

When we fetching data from cache, we basically restoring parts of index from cache.

For example, if we have this query:

.. code-block:: graphql

    query {
        products {
            name
            company @cached(ttl: 10) {
                id
            }
        }
    }

The cached data will look like this:

.. code-block:: python

    {
        'Product': {
            'company': Reference('Company', 1)
        },
        'Company': {
            1: {'id': 1}
        }
    }

As we can see we cache ``company`` with id 1 and make reference to it from ``Product``.
Note that we are not specifying particular product id and that means that any product that has
``company_id == 1`` will reuse company from cache.

Note also that link to same node but with different name is considered as as a different cache object.
Lets take ``Product`` node from a previous example and add another link to company.

.. code-block:: python

    Node('Product', [
        Field('id'),
        Field('name'),
        Field('company_id'),
        Link('company', TypeRef['Company'], requires='company_id'),
        Link('companyX', TypeRef['Company'], requires='company_id'),
    ])

Even though both links are pointing to the same node and if query selection set is the same, they will be cached separately.

Effective caching
~~~~~~~~~~~~~~~~~

For caching to be the most effective we need to make sure that we are caching
data that will be reused and will eliminate unnecessary queries to database.

By design hiku stores data in index by key from ``requires``.

For example, if we have this graph:

.. code-block:: python

    product_sg = SubGraph(low_level, 'Product')
    company_sg = SubGraph(low_level, 'Company')

    def direct_link(ids):
        return ids

    Node('Company', [
        Field('id', company_sg),
        Field('name', company_sg),
    ]),
    Node('Product', [
        Field('id', product_sg),
        Field('company_id', product_sg),
        Link('company', TypeRef['Company'], direct_link, requires='company_id'),
    ])

In this example graph, ``direct_link`` will return ids and then we fetch data from database by this ids.

The index will look like this:

.. code-block:: python

    {
        'Company': {
            1: {'id': 1, 'name': 'apple'}
        }
    }


where 1 is a value from link resolver ``direct_link``.

In this case cache will be the most efficient, because we will store fetched data by primitive id and next time
we will skip data fetching by this id.

But lets consider another case, when link resolver returns not primitive value, but a list of objects:


.. code-block:: python

    product_sg = SubGraph(low_level, 'Product')

    def map_company_fields(fields, companies):
        def get_field(f, company):
            if f.name == 'id':
                return company.id
            elif f.name == 'name':
                return company.name

            raise ValueError(f'Unknown field {f.name}')

        return [
            [get_field(f, company) for f in fields]
            for company in companies
        ]

    def expensive_link(ids):
        return db.query(Company).filter(Company.id.in_(ids)).all()

    Node('Company', [
        Field('id', map_company_fields),
        Field('name', map_company_fields),
    ]),
    Node('Product', [
        Field('id', product_sg),
        Field('company_id', product_sg),
        Link('company', TypeRef['Company'], expensive_link, requires='company_id'),
    ])


The main difference here is that we are fetching data from database inside link resolver ``expensive_link`` and instead of returning
primitive ids we are returning list of objects. Lets see how index will look like:


.. code-block:: python

    {
        'Company': {
            Company(1, 'apple'): {'id': 1, 'name': 'apple'}
        }
    }


Here we have two problems:

1. In this case index will be much bigger, because we are storing whole objects in index, and this will lead to data duplication.
2. We are storing data by object itself, not by id. In this case cache will be much less efficient.
   Yes, we will be able to cache and reuse data, but we will sill be fetching data from database in link resolver which will make cache useless.


How to enable cache on backend
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Implement ``BaseCache`` abstract class.

Lets implement InMemoryCache for example:

.. code-block:: python

    from hiku.cache import BaseCache

    class InMemoryCache(BaseCache):
        def __init__(self) -> None:
            self._store = {}

        def get_many(self, keys):
            result = {}
            for key in keys:
                if key in self._store:
                    result[key] = self._store[key]
            return result

        def set_many(self, items, ttl):
            self._store.update(items)

Note that cache ``get_many`` must return only keys that are found in cache.

2. Pass ``cache`` argument to ``Engine`` constructor.

.. code-block:: python

    from hiku.cache import CacheSettings
    from hiku.engine import Engine

    cache = InMemoryCache()
    engine = Engine(ThreadsExecutor(thread_pool), CacheSettings(cache))


``CacheSettings`` has ``cache_key`` optional argument. It is a function that
takes ``Context`` and ``Hasher`` (`hashlib.sha1` instance) and can be used to add additional data to cache key.

.. code-block:: python

    def cache_key(context, hasher):
        return hasher.update(context['locale'])

    engine = Engine(ThreadsExecutor(thread_pool), CacheSettings(cache, cache_key))


How to specify cache on client
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use `@cached` directive on any non root node.

.. code-block:: graphql

    query Products {
      products {
        id
        name
        company @cached(ttl: 60) {
          id
          name
        }
      }
    }

Here we are caching company node for 60 seconds.
