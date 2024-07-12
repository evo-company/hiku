import logging
import sys
import typing as t
from pathlib import Path

from flask import Flask, request, jsonify

from hiku.directives import Deprecated, Location
from hiku.federation.directive import (
    Extends,
    FederationSchemaDirective,
    Inaccessible,
    InterfaceObject,
    Key,
    External,
    Override,
    Provides,
    Requires,
    Shareable,
    Tag,
    schema_directive,
)
from hiku.federation.graph import Graph, FederatedNode
from hiku.engine import Engine
from hiku.graph import (
    Nothing,
    Root,
    Field,
    Option,
    Node,
    Link,
)
from hiku.schema import Schema
from hiku.types import (
    Float,
    ID,
    Integer,
    Record,
    TypeRef,
    String,
    Optional,
    Sequence,
)
from hiku.executors.sync import SyncExecutor
from hiku.utils import ImmutableDict, listify, to_immutable_dict

log = logging.getLogger(__name__)


def get_by_id(id_, collection):
    for item in collection:
        if item["id"] == id_:
            return item


def direct_link_id(opts):
    return opts["id"]


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

inventory = {"id": "apollo-oss", "deprecatedProducts": [deprecated_product]}


@listify
def product_fields_resolver(fields: t.List[Field], ids: t.List[str]):
    def get_field(field: Field, product: dict):
        if field.name == "id":
            return product["id"]
        elif field.name == "sku":
            return product["sku"]
        elif field.name == "package":
            return product["package"]
        elif field.name == "notes":
            return product["notes"]
        elif field.name == "variation":
            return product["variation"]
        elif field.name == "_createdBy":
            return product["created_by"]
        else:
            raise ValueError(f"Unknown field {field.name}")

    for product_id in ids:
        if isinstance(product_id, ImmutableDict):
            for product in products:
                if product_id.get("id") == product["id"]:
                    data = product
                    break
                if product_id.get("sku") == product["sku"]:
                    if "package" in product_id:
                        if product["package"] == product_id["package"]:
                            data = product
                            break
                    elif "variation" in product_id:
                        if (
                            product["variation"]["id"]
                            == product_id["variation"]["id"]
                        ):
                            data = product
                            break
            if not product:
                raise ValueError(f"Unknown product {product_id}")
        else:
            data = get_by_id(product_id, products)
        yield [get_field(field, data) for field in fields]


@listify
def link_product_dimensions(ids: t.List[str]) -> t.Iterable[Dimension]:
    for product_id in ids:
        data = get_by_id(product_id, products)
        yield Dimension(
            data["dimensions"]["size"],
            data["dimensions"]["weight"],
            data["dimensions"]["unit"],
        )


@listify
def product_dimension_fields_resolver(
    fields: t.List[Field], dimensions: t.List[Dimension]
):
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
def gen_researches(researches: t.List[dict]) -> t.Iterable[Research]:
    for res in researches:
        yield Research(
            Study(
                res["study"]["case_number"],
                res["study"]["description"],
            ),
            res["outcome"],
        )


@listify
def link_product_research(ids: t.List[str]):
    for product_id in ids:
        data = get_by_id(product_id, products)
        yield from gen_researches(data["research"])


@listify
def product_research_fields_resolver(
    fields: t.List[Field], researches: t.List[t.Union[Research, ImmutableDict]]
):
    def get_field(field: Field, r: Research):
        if field.name == "study":
            return {
                "caseNumber": r.study.case_number,
                "description": r.study.description,
            }
        elif field.name == "outcome":
            return r.outcome
        else:
            raise ValueError(f"Unknown field {field.name}")

    for item in researches:
        # if we are here this is federated query
        if isinstance(item, ImmutableDict):
            case_number = item["study"]["caseNumber"]
            res = next(
                (
                    product_research
                    for product_research in products_research
                    if product_research["study"]["case_number"] == case_number
                ),
                None,
            )
            research = Research(
                Study(
                    res["study"]["case_number"],
                    res["study"]["description"],
                ),
                res["outcome"],
            )
        else:
            research = item
        yield [get_field(field, research) for field in fields]


@listify
def user_fields_resolver(fields: t.List[Field], emails: t.List[str]):
    def get_field(field: Field, u: dict):
        if field.name == "email":
            return u["email"]
        elif field.name == "name":
            return u["name"]
        elif field.name == "totalProductsCreated":
            return u["total_products_created"]
        elif field.name == "yearsOfEmployment":
            return u["years_of_employment"]
        elif field.name == "averageProductsCreatedPerYear":
            if u["total_products_created"] is not None:
                return round(
                    u["total_products_created"] / u["years_of_employment"]
                )

            return None
        else:
            raise ValueError(f"Unknown field {field.name}")

    for _ in emails:
        yield [get_field(field, user) for field in fields]


@listify
def deprecated_product_fields_resolver(
    fields: t.List[Field], ids: t.List[ImmutableDict]
):
    def get_field(field: Field, p: dict):
        if field.name == "sku":
            return p["sku"]
        elif field.name == "package":
            return p["package"]
        elif field.name == "reason":
            return p["reason"]
        elif field.name == "_createdBy":
            return p["created_by"]

        raise ValueError(f"Unknown field {field.name}")

    for id_ in ids:
        if (
            deprecated_product["sku"] == id_["sku"]
            and deprecated_product["package"] == id_["package"]
        ):
            p = deprecated_product
            yield [get_field(field, p) for field in fields]
        else:
            raise ValueError(f"Unknown id {id_}")


@listify
def inventory_fields_resolver(fields: t.List[Field], ids: t.List[str]):
    def get_field(field: Field, id_):
        if field.name == "id":
            if inventory["id"] == id_:
                return inventory["id"]

        raise ValueError(f"Unknown field {field.name}")

    for id_ in ids:
        yield [get_field(field, id_) for field in fields]


def link_deprecated_product():
    return Nothing


@listify
def link_inventory_products(ids):
    for id_ in ids:
        if id_ == inventory["id"]:
            yield [
                ImmutableDict({"sku": p["sku"], "package": p["package"]})
                for p in inventory["deprecatedProducts"]
            ]


def resolve_reference_by(key):
    def resolver(representations):
        return [r[key] for r in representations]

    return resolver


def resolve_reference_direct(representations):
    return [to_immutable_dict(r) for r in representations]


@schema_directive(
    name="custom",
    locations=[Location.OBJECT],
    compose=True,
    import_url="https://myspecs.dev/myCustomDirective/v1.0",
)
class Custom(FederationSchemaDirective):
    ...


QUERY_GRAPH = Graph(
    [
        FederatedNode(
            "User",
            [
                Field(
                    "averageProductsCreatedPerYear",
                    Optional[Integer],
                    user_fields_resolver,
                    directives=[
                        Requires("totalProductsCreated yearsOfEmployment")
                    ],
                ),
                Field(
                    "email", ID, user_fields_resolver, directives=[External()]
                ),
                Field(
                    "name",
                    Optional[String],
                    user_fields_resolver,
                    directives=[Override("users")],
                ),
                Field(
                    "totalProductsCreated",
                    Optional[Integer],
                    user_fields_resolver,
                    directives=[External()],
                ),
                Field(
                    "yearsOfEmployment",
                    Integer,
                    user_fields_resolver,
                    directives=[External()],
                ),
            ],
            directives=[Key("email"), Extends()],
            resolve_reference=resolve_reference_by('email')
        ),
        FederatedNode(
            "Product",
            [
                Field("id", ID, product_fields_resolver),
                Field("sku", Optional[String], product_fields_resolver),
                Field("package", Optional[String], product_fields_resolver),
                Field(
                    "notes",
                    Optional[String],
                    product_fields_resolver,
                    directives=[Tag("internal")],
                ),
                Field(
                    "variation",
                    Optional[TypeRef["ProductVariation"]],
                    product_fields_resolver,
                ),
                Field("_createdBy", Optional[String], product_fields_resolver),
                Link(
                    "dimensions",
                    Optional[TypeRef["ProductDimension"]],
                    link_product_dimensions,
                    requires="id",
                ),
                Link(
                    "createdBy",
                    Optional[TypeRef["User"]],
                    direct_link,
                    requires="_createdBy",
                    directives=[Provides("totalProductsCreated")],
                ),
                Link(
                    "research",
                    Sequence[TypeRef["ProductResearch"]],
                    link_product_research,
                    requires="id",
                ),
            ],
            directives=[
                Custom(),
                Key("id"),
                Key("sku package"),
                Key("sku variation { id }"),
            ],
            resolve_reference=resolve_reference_direct
        ),
        Node(
            "ProductDimension",
            [
                Field(
                    "size", Optional[String], product_dimension_fields_resolver
                ),
                Field(
                    "weight", Optional[Float], product_dimension_fields_resolver
                ),
                Field(
                    "unit",
                    Optional[String],
                    product_dimension_fields_resolver,
                    directives=[Inaccessible()],
                ),
            ],
            directives=[Shareable()],
        ),
        FederatedNode(
            "ProductResearch",
            [
                Field(
                    "study",
                    TypeRef["CaseStudy"],
                    product_research_fields_resolver,
                ),
                Field(
                    "outcome",
                    Optional[String],
                    product_research_fields_resolver,
                ),
            ],
            directives=[Key("study { caseNumber }")],
            resolve_reference=resolve_reference_direct
        ),
        FederatedNode(
            "DeprecatedProduct",
            [
                Field("sku", String, deprecated_product_fields_resolver),
                Field("package", String, deprecated_product_fields_resolver),
                Field(
                    "reason",
                    Optional[String],
                    deprecated_product_fields_resolver,
                ),
                Field(
                    "_createdBy",
                    Optional[String],
                    deprecated_product_fields_resolver,
                ),
                Link(
                    "createdBy",
                    Optional[TypeRef["User"]],
                    direct_link,
                    requires="_createdBy",
                ),
            ],
            directives=[Key("sku package")],
            resolve_reference=resolve_reference_direct,
        ),
        FederatedNode(
            "Inventory",
            [
                Field("id", ID, inventory_fields_resolver),
                Link(
                    "deprecatedProducts",
                    Sequence[TypeRef["DeprecatedProduct"]],
                    link_inventory_products,
                    requires="id",
                ),
            ],
            directives=[InterfaceObject(), Key("id")],
            resolve_reference=resolve_reference_by("id"),
        ),
        Root(
            [
                Link(
                    "product",
                    Optional[TypeRef["Product"]],
                    direct_link_id,
                    requires=None,
                    options=[Option("id", ID)],
                ),
                Link(
                    "deprecatedProduct",
                    Optional[TypeRef["DeprecatedProduct"]],
                    link_deprecated_product,
                    requires=None,
                    options=[
                        Option("sku", String),
                        Option("package", String),
                    ],
                    directives=[Deprecated("Use product query instead")],
                ),
            ]
        ),
    ],
    data_types={
        "ProductVariation": Record[{"id": ID}],
        "CaseStudy": Record[
            {
                "caseNumber": ID,
                "description": Optional[String],
            }
        ],
    },
    directives=[Custom],
)


app = Flask(__name__)

schema = Schema(
    Engine(SyncExecutor()),
    QUERY_GRAPH,
)


@app.route("/graphql", methods={"POST"})
def handle_graphql():
    data = request.get_json()
    result = schema.execute_sync(data)
    resp = jsonify(result)
    return resp


@app.route('/', methods={'GET'})
def graphiql():
    path = Path(__file__).parent.parent / 'graphiql.html'
    with open(path) as f:
        page = f.read()
        page = page.replace("localhost:5000", "localhost:4001")
        return page.encode('utf-8')


def main():
    logging.basicConfig(level=logging.DEBUG)

    app.run(host="0.0.0.0", port=4001, debug=True)


def dump():
    from hiku.federation.sdl import print_sdl

    out_file = Path(__file__).resolve().parent / 'products.graphql'
    print(f"Dumping schema to {out_file}")
    sdl = print_sdl(QUERY_GRAPH)
    with open(out_file, "w") as f:
        f.write(sdl)


if __name__ == "__main__":
    """
    Run server: python3 ./examples/federation-compatibility/server.py
    Dump schema: python3 ./examples/federation-compatibility/ dump
    Federation Compatibility test: ./examples/federation-compatibility/run_compatibility_test.sh  # noqa
    """
    if len(sys.argv) > 1 and sys.argv[1] == "dump":
        dump()
        sys.exit(0)

    main()
