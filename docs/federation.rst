Federation
==========

What is Federation
------------------

Apollo Federation is a set of open-source tools that allow you to compose multiple GraphQL services into a single data graph.

It is a method of splitting a large GraphQL schema into smaller, more manageable schemas that can be composed together to form a single data graph.

Hiku includes integrated support for both Federation v1 and v2, enabling you to expose your Hiku graph as a federated subgraph.

Although Hiku offers support for Apollo Federation v1, it is not recommended for use due to its deprecation in favor of v2.

For more details about Apollo Federation v2, please refer to `Apollo GraphQL Federation v2 Docs <https://www.apollographql.com/docs/federation/federation-2/new-in-federation-2/>`_.

The specification for subgraphs can be found here: `Apollo GraphQL Subgraph Spec <https://www.apollographql.com/docs/federation/subgraph-spec/>`_.

How it Works in General
-----------------------

In a federated architecture, there are two main components: the router and the subgraphs. The router is tasked with composing the subgraphs into a supergraph schema. It routes requests to the appropriate subgraph and combines the results from these subgraphs into a unified response.

Hiku is utilized to implement a subgraph.

There are two primary methods to compose a supergraph:

* Through managed federation in Apollo Studio, which is done automatically.
* Locally, using the Rover CLI, which is a manual process.

For more detailed information, please refer to the `Apollo GraphQL Federation Setup Guide <https://www.apollographql.com/docs/federation/quickstart/setup>`_.

Guide to Setup Federation Subgraph
----------------------------------

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

Now let's implement the Order service using Hiku:

.. code-block:: python

    from flask import Flask, request, jsonify
    from hiku.graph import Graph, Root, Field, Link, Node, Option
    from hiku.types import ID, Integer, TypeRef, String, Optional, Sequence
    from hiku.executors.sync import SyncExecutor
    from hiku.federation.directives import Key
    from hiku.federation.endpoint import FederatedGraphQLEndpoint
    from hiku.federation.engine import Engine

    QUERY_GRAPH = Graph([
        Node('Order', [
            Field('id', ID, order_fields_resolver]),
            Field('status', Integer, order_fields_resolver]),
            Field('cartId', Integer, order_fields_resolver]),
        ], directives=[Key('id'), Key('cartId')]),
        Root([
            Link(
                'order',
                Optional[TypeRef['Order']],
                direct_link_by_id,
                requires=None,
                options=[
                    Option('id', Integer)
                ],
            ),
        ]),
    ])

    app = Flask(__name__)

    graphql_endpoint = FederatedGraphQLEndpoint(
        Engine(SyncExecutor()),
        QUERY_GRAPH,
    )

    @app.route('/graphql', methods={'POST'})
    def handle_graphql():
        data = request.get_json()
        result = graphql_endpoint.dispatch(data)
        resp = jsonify(result)
        return resp

    if __name__ == '__main__':
        app.run(host='0.0.0.0', port=4001)

Note that by default, v2 of Federation is used. To enable v1, you need to pass `federation_version=1` to the `Engine` constructor.

We define the `Order` type with the `@key` directive. This directive specifies the primary key of the type. So in our case, `id` is the primary key of the `Order` type. The router now knows to fetch an order it needs to provide the `id` field value. It will then join different parts of data from different subgraphs into one type using the Key. A type can have many `Key` directives, and we define `cartId` as another key. This will allow us to join `Order` and `ShoppingCart` types together.

Next, let's implement the ShoppingCart service using Hiku:

.. code-block:: python

    from flask import Flask, request, jsonify
    from hiku.graph import Graph, Root, Field, Link, Node, Option
    from hiku.types import ID, Integer, TypeRef, String, Optional, Sequence
    from hiku.executors.sync import SyncExecutor
    from hiku.federation.directives import Key
    from hiku.federation.endpoint import FederatedGraphQLEndpoint
    from hiku.federation.engine import Engine

    QUERY_GRAPH = Graph([
        Node('ShoppingCart', [
            Field('id', ID, cart_fields_resolver]),
            Link('items', Sequence[TypeRef['ShoppingCartItem']], link_cart_items, requires='id'),
        ]),
        Node('ShoppingCartItem', [
            Field('id', ID, cart_item_fields_resolver]),
            Field('productName', String, cart_item_fields_resolver]),
            Field('price', Integer, cart_item_fields_resolver]),
            Field('quantity', Integer, cart_item_fields_resolver]),
        ]),
        Node('Order', [
            Field('cartId', ID, order_fields_resolver]),
            Link('cart', TypeRef['ShoppingCart'], link_order_to_cart, requires='cartId'),
        ], directives=[Key('cartId')]),
        Root([
            Link(
                'cart',
                Optional[TypeRef['ShoppingCart']],
                direct_link_by_id,
                requires=None,
                options=[
                    Option('id', Integer)
                ],
            ),
        ]),
    ])

    app = Flask(__name__)

    graphql_endpoint = FederatedGraphQLEndpoint(
        Engine(SyncExecutor()),
        QUERY_GRAPH,
    )

    @app.route('/graphql', methods={'POST'})
    def handle_graphql():
        data = request.get_json()
        result = graphql_endpoint.dispatch(data)
        resp = jsonify(result)
        return resp

    if __name__ == '__main__':
        app.run(host='0.0.0.0', port=4002)


In the ShoppingCart service, we define the `ShoppingCart` and `ShoppingCartItem` types. But also, we define a stub `Order` type. This is needed because we want to extend the `Order` type with a `cart` field. In the `Order` type, we specify `cartId` as a key. This will allow us to join `Order` and `ShoppingCart` types together.

Now we need to compose subgraph schemas into a supergraph schema and run an instance of the router.

Start the `Order` service on port 4001 and the `ShoppingCart` service on port 4002.

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