import logging
import typing as t

from flask import Flask, request, jsonify

from hiku.directives import Deprecated, SchemaDirective
from hiku.federation.v2.directive import (
    Inaccessible, InterfaceObject, Key,
    External,
    Override, Provides, Requires, Shareable, Tag,
)
from hiku.federation.v2.endpoint import FederatedGraphQLEndpoint
from hiku.federation.v2.engine import Engine
from hiku.graph import (
    Nothing, Root,
    Field,
    Option,
    Node,
    Link,
    Graph,
)
from hiku.readers.graphql import setup_query_cache
from hiku.types import (
    Float, Integer,
    Record, TypeRef,
    String,
    Optional,
    Sequence,
)
from hiku.executors.sync import SyncExecutor
from hiku.utils import listify

log = logging.getLogger(__name__)


def get_by_id(id_, collection):
    for item in collection:
        if item['id'] == id_:
            return item


def direct_link_id(opts):
    return opts['id']


def direct_link(ids):
    return ids


class Dimension(t.NamedTuple):
    size: str
    weight: int
    unit: str


class Study(t.NamedTuple):
    case_number: str
    description: str


class Research(t.NamedTuple):
    study: Study
    outcome: t.Optional[str]


dimension = {
    "size": "small",
    "weight": 1,
    "unit": "kg",
}

user = {
    "email": "support@apollographql.com",
    "name": "Jane Smith",
    "total_products_created": 1337,
    "years_of_employment": 10,
}


deprecated_product = {
    "sku": "apollo-federation-v1",
    "package": "@apollo/federation-v1",
    "reason": "Migrate to Federation V2",
    "created_by": user["email"],
}

products_research = [
    {
        "study": {
            "case_number": "1234",
            "description": "Federation Study",
        },
        "outcome": None,
    },
    {
        "study": {
            "case_number": "1235",
            "description": "Studio Study",
        },
        "outcome": None,
    },
]


products = [
    {
        "id": "apollo-federation",
        "sku": "federation",
        "package": "@apollo/federation",
        "variation": {"id": "OSS"},
        "dimensions": dimension,
        "research": [products_research[0]],
        "created_by": user["email"],
        "notes": None,
    },
    {
        "id": "apollo-studio",
        "sku": "studio",
        "package": "",
        "variation": {"id": "platform"},
        "dimensions": dimension,
        "research": [products_research[1]],
        "created_by": user["email"],
        "notes": None,
    },
]


@listify
def product_fields_resolver(fields: t.List[Field], ids: t.List[str]):
    def get_field(field: Field, product: dict):
        if field.name == "id":
            return product['id']
        elif field.name == "sku":
            return product['sku']
        elif field.name == "package":
            return product['package']
        elif field.name == "notes":
            return product['notes']
        elif field.name == "variation":
            return product['variation']
        elif field.name == "_createdBy":
            return product['created_by']
        else:
            raise ValueError(f"Unknown field {field.name}")

    for product_id in ids:
        data = get_by_id(product_id, products)
        yield [get_field(field, data) for field in fields]


@listify
def link_product_dimensions(ids: t.List[str]) -> t.Iterable[Dimension]:
    for product_id in ids:
        data = get_by_id(product_id, products)
        yield Dimension(
            data['dimensions']['size'],
            data['dimensions']['weight'],
            data['dimensions']['unit'],
        )


@listify
def product_dimension_fields_resolver(fields: t.List[Field], dimensions: t.List[Dimension]):
    def get_field(field: Field, dim: Dimension):
        if field.name == "size":
            return dim.size
        elif field.name == "weight":
            return dim.weight
        elif field.name == "unit":
            return dim.unit

        else:
            raise ValueError(f"Unknown field {field.name}")

    for item in dimensions:
        yield [get_field(field, item) for field in fields]


@listify
def link_product_research(ids: t.List[str]):
    @listify
    def gen_researches(researches: t.List[dict]) -> t.Iterable[Research]:
        for res in researches:
            yield Research(
                Study(
                    res['study']['case_number'],
                    res['study']['description'],
                ),
                res['outcome'],
            )

    for product_id in ids:
        data = get_by_id(product_id, products)
        yield from gen_researches(data['research'])


@listify
def product_research_fields_resolver(fields: t.List[Field], researches: t.List[Research]):
    def get_field(field: Field, r: Research):
        if field.name == "study":
            return r.study
        elif field.name == "outcome":
            return r.outcome
        else:
            raise ValueError(f"Unknown field {field.name}")

    for item in researches:
        yield [get_field(field, item) for field in fields]


@listify
def user_fields_resolver(fields: t.List[Field], emails: t.List[str]):
    def get_field(field: Field, u: dict):
        if field.name == "email":
            return u['email']
        elif field.name == "name":
            return u['name']
        elif field.name == "totalProductsCreated":
            return u['total_products_created']
        elif field.name == "yearsOfEmployment":
            return u['years_of_employment']
        elif field.name == "averageProductsCreatedPerYear":
            raise ValueError("averageProductsCreatedPerYear is not implemented")
        else:
            raise ValueError(f"Unknown field {field.name}")

    for _ in emails:
        yield [get_field(field, user) for field in fields]


@listify
def deprecated_product_fields_resolver(fields: t.List[Field], ids):
    def get_field(field: Field):
        raise ValueError(f"Unknown field {field.name}")

    for _ in ids:
        yield [get_field(field) for field in fields]


def link_deprecated_product():
    return Nothing


class Custom(SchemaDirective):
    # TODO: implement __directive_name__, because we can not make visitor pattern for every custom directive
    ...


QUERY_GRAPH = Graph([
    Node('Product', [
        # TODO: ID type is not supported yet
        # TODO: custom types are not supported yet
        Field('id', String, product_fields_resolver),
        Field('sku', Optional[String], product_fields_resolver),
        Field('package', Optional[String], product_fields_resolver),
        Field('notes', Optional[String], product_fields_resolver, directives=[Tag("internal")]),
        Field('variation', Optional[TypeRef['ProductVariation']], product_fields_resolver),
        Field('_createdBy', Optional[String], product_fields_resolver),
        Link('dimensions', Optional[TypeRef['ProductDimension']], link_product_dimensions, requires='id'),
        Link('createdBy', Optional[TypeRef['User']], direct_link, requires='_createdBy', directives=[Provides("totalProductsCreated")]),
        Link('research', Sequence[TypeRef['ProductResearch']], link_product_research, requires='id'),
    ], directives=[Custom(), Key('id'), Key("sku package"), Key("sku variation { id }")]),
    # Node('ProductVariation', [
    #     Field('id', Integer, ids_resolver),
    # ]),
    Node('ProductDimension', [
        Field('size', Optional[String], product_dimension_fields_resolver),
        Field('weight', Optional[Float], product_dimension_fields_resolver),
        # TODO: what means Inaccessible directive?
        Field('unit', Optional[String], product_dimension_fields_resolver, directives=[Inaccessible()]),
    ], directives=[Shareable()]),
    Node('ProductResearch', [
        Field('study', TypeRef['CaseStudy'], product_research_fields_resolver),
        Field('outcome', Optional[String], product_research_fields_resolver),
    ], directives=[Key('study { caseNumber }')]),
    # Node('CaseStudy', [
    #     Field('caseNumber', String, ids_resolver),
    #     Field('description', Optional[String], ids_resolver),
    # ]),
    Node('User', [
        Field('averageProductsCreatedPerYear', Optional[Integer], user_fields_resolver, directives=[Requires("totalProductsCreated yearsOfEmployment")]),
        # TODO: email: must be ID!
        Field('email', String, user_fields_resolver, directives=[External()]),
        # TODO: implement Override directive, because user subgraph marked this field as non-sharable
        Field('name', Optional[String], user_fields_resolver, directives=[Override("users")]),
        Field('totalProductsCreated', Optional[Integer], user_fields_resolver, directives=[External()]),
        # TODO: implement External directive, because user subgraph marked this field as non-sharable
        Field('yearsOfEmployment', Integer, user_fields_resolver, directives=[External()]),
    ], directives=[Key('email')]),
    Node('DeprecatedProduct', [
        Field('sku', String, deprecated_product_fields_resolver),
        Field('package', String, deprecated_product_fields_resolver),
        Field('reason', String, deprecated_product_fields_resolver),
        Link('createdBy', TypeRef['User'], direct_link, requires=None),
    ], directives=[Key('sku package')]),
    # TODO: seems like this type must be Interface and not object !
    Node('Inventory', [
        Field('id', String, lambda _, __: []),
        Link('deprecatedProducts', Sequence[TypeRef['DeprecatedProduct']], direct_link, requires='id'),
    ], directives=[InterfaceObject(), Key('id')]),
    Root([
        Link(
            'product',
            Optional[TypeRef['Product']],
            direct_link_id,
            requires=None,
            options=[
                Option('id', Integer)
            ],
        ),
        Link(
            'deprecatedProduct',
            Optional[TypeRef['DeprecatedProduct']],
            link_deprecated_product,
            requires=None,
            options=[
                Option('sku', String),
                Option('package', String),
            ],
            directives=[Deprecated("Use product query instead")]
        )
    ]),
], data_types={
    'ProductVariation': Record[{
        'id': Integer
    }],
    'CaseStudy': Record[{
        'caseNumber': String,
        'description': Optional[String],
    }],
})


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


def main():
    logging.basicConfig(level=logging.DEBUG)
    setup_query_cache(size=128)
    app.run(host='0.0.0.0', port=5000, debug=True)


if __name__ == '__main__':
    main()
