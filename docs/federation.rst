Apollo Federation
=================

What is Apollo Federation
-------------------------

Apollo Federation is a technology to implement distributed GraphQL by composing multiple subgraphs into one supergraph.

In the terms of Apollo Federation:

#. A subgraph is a standalone GraphQL server with enabled federation support. Hiku supports Apollo Federation and can be used to implement a subgraph.
#. A supergraph is a composition of multiple subgraphs into a single data graph. To run a supergraph, you need to use special gateway (or sometimes called router) that will route requests to the appropriate subgraph and combine the results into a unified response.

Hiku supports both Federation v1 and v2, but it is recommended to use v2 as v1 is deprecated.

For more details about Apollo Federation v2, please refer to `Apollo GraphQL Federation v2 Docs <https://www.apollographql.com/docs/federation/federation-2/new-in-federation-2/>`_.

The specification for subgraphs can be found here: `Apollo GraphQL Subgraph Spec <https://www.apollographql.com/docs/federation/subgraph-spec/>`_.

How it Works
------------

In a federated architecture, there are two main components: the gateway/router and the subgraphs.

In order to run supergraph you need to compose one.

There are two primary methods to compose a supergraph:

* Using `schema registry` (managed federation in Apollo Studio is one of them), where composition happens automatically when we push new subgraph schema
* Manually, using the Rover CLI, by providing a configuration file with subgraph URLs and routing URLs. The Rover CLI will then fetch remote services and compose schema into a file.

Then you can run gateway/router with the composed schema and router should start routing requests to the appropriate subgraph and combine the results into a unified response.

For more detailed information, please refer to the `Apollo GraphQL Federation Setup Guide <https://www.apollographql.com/docs/federation/quickstart/setup>`_.

Setup Federation Subgraph
-------------------------

.. note:: You can find the source code for this example `on GitHub <https://github.com/evo-company/hiku/blob/master/examples/graphql_federation_v2.py>`_.

Let's start with a simple example of a federated subgraph using the following GraphQL schema:

Order Service

.. code-block:: graphql

   type Order @key(fields: "id") {
       id: ID!
       status: Int!
       cartId: Int!
   }

   type Query {
       order: [Order!]!
   }

Shopping Cart Service

.. code-block:: graphql

   type ShoppingCart @key(fields: "id") {
       id: ID!
       items: [ShoppingCartItem!]!
   }

   type ShoppingCartItem {
       id: ID!
       productName: String!
       price: Int!
       quantity: Int!
   }

   type Query {
       cart(id: ID!): ShoppingCart
   }

Now let's implement the ``Order`` service using Hiku:

.. literalinclude:: federation/order_service.py
    :lines: 1-76

* Using ``hiku.federation.graph.Graph`` instead of ``hiku.graph.Graph``
* Using ``hiku.federation.graph.FederatedNode`` instead of ``hiku.graph.Node``
* Also using ``hiku.federation.schema.Schema`` instead of ``hiku.schema.Schema``
* By default, the federation version is set to 2. To enable v1, you need to pass ``federation_version=1`` to the ``Schema`` constructor.

We define the ``Order`` type with the ``@key`` directive. This directive specifies the primary key of the type.

In our case, ``id`` is the primary key of the ``Order`` type.
``Router`` now knows, that in order for it to fetch an order, it needs to provide the ``id`` field value when requesting ``Order`` service.
``Router`` then joins different parts of data from different subgraphs into one response using the ``Key``.

A type can have many ``Key`` directives. We define ``cartId`` as another key.
This will allow us to join ``Order`` and ``ShoppingCart`` types together.

Also we define ``resolve_reference`` function which in our case is ``resolve_order_reference``.
A ``resolve_reference`` function works very similar to ``Link`` resolver -
it returns a list of values that will be passed to ``Node`` as a root values.

.. note:: Since we want to pass representations as is to ``Node`, we need to convert each representation to ``ImmutableDict`` because ``resolve_reference`` function must return **hashable** values just like ``Link`` resolver.

Then in ``order_fields_resolver`` we fetch orders either by ``id`` or by ``cartId``.

.. note:: In the example above, we fetch orders by one. In real-world applications, you would fetch orders in butches to avoid N+1.

Next, let's implement the ``ShoppingCart`` service using Hiku:

.. literalinclude:: federation/cart_service.py
    :lines: 1-116


In the ``ShoppingCart`` service, we define the ``ShoppingCart`` and ``ShoppingCartItem`` types.
But also, we define a stub ``Order`` type. This is needed because we want to extend the ``Order`` type with a ``cart`` field.
In the ```Order`` type, we specify ``cartId`` as a key. This will allow us to join ``Order`` and ``ShoppingCart`` types together.

Now we need to compose subgraph schemas into a supergraph schema and run an instance of the router.

Start the ``Order`` service on port 4001 and the ``ShoppingCart`` service on port 4002.

Apollo Router
-------------

With our services up and running, we need to configure a gateway to consume our services. Apollo provides a router for this purpose.

Before proceeding, install the Apollo Router by following their `installation guide <https://www.apollographql.com/docs/router/quickstart/>`_. Also, install Apollo's CLI (rover) `here <https://www.apollographql.com/docs/rover/getting-started/>`_ to compose the schema.

Create a file named `supergraph.yaml` with the following contents:

.. code-block:: yaml

    federation_version: 2.3
    subgraphs:
      order:
        routing_url: http://localhost:4001/graphql
        schema:
          subgraph_url: http://localhost:4001/graphql

      shopping_cart:
        routing_url: http://localhost:4002/graphql
        schema:
          subgraph_url: http://localhost:4002/graphql

This file will be used by Rover to compose the schema, which can be done with the following command:

.. code-block:: bash

   rover supergraph compose --config ./supergraph.yaml > supergraph-schema.graphql

With the composed schema, we can now start the router:

.. code-block:: bash

   ./router --supergraph supergraph-schema.graphql

With the router running, visit http://localhost:4000 and try running the following query:

.. code-block:: graphql

    {
        order(id: 1) {
            id
            status
            cart {
                id
                items {
                    id
                    productName
                    price
                }
            }
        }
    }
