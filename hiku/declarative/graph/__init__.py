'''General api structure reiterated'''


import typing
from .resolver import resolver
from .dataloader import Dataloader
from .option import options, opt
from .field import Fieldgen
from .node import node


class ProductDB(Dataloader[int]):
    id: int = Field(product_query)
    name: str = Field(product_query)
    status: int = Field(product_query)

    variation_base_id: int | None = Field(product_auery)

    variation: 'ProductDB' | None = Link(
        maybe_direct_link,
        requires=lambda: ProductDB.variation_base_id
    )


@resolver(preload=ProductDB.load(ProductDB.name), listify=True)
def product_name_for_catalog(product: ProductDB, ctx: dict, opts) -> str:
    return get_product_name(product.name)


@options
class ProductCanonicalUrlOptions:
    prices_param: str | None = opt(default=None)


@resolver(
    preload=ProductDB.load(
        ProductDB.id,
        ProductDB.name,
        ProductDB.variation.load(
            ProductDB.id
            ProductDB.name
        )
    ),
    listify=True,
)
def get_product_canonical_url(
    product: ProductDB,
    ctx: dict,
    opts: ProductCanonicalUrlOptions,
) -> str:
    ...


@resolver(preload=ProductDB.load(...))
def link_promo_label_banner(
    products: list[ProductDB],
    ctx: dict,
) -> list[Banner]:
    advantages = [get_promo_advantages(p) for p in products]

    return get_banners(advantages)


@node
class Banner:
    field: typing.ClassVar[Fieldgen['Banner', dict]] = Fieldgen()

    id: int
    image_id: int
    image_url: str = field(get_image_url, options=...)
    text: str


@node
class ProductNode:
    field: typing.ClassVar[Fieldgen[int, dict]] = Fieldgen()

    id: int = field(preload=ProductDB.id.load())
    name: str = field(preload=ProductDB.name.load())
    status: int = field(preload=ProductDB.status.load())
    name_for_catalog: str = field(product_name_for_catalog)
    urlForCanonical: str | None = field(
        get_product_canonical_url,
        options=ProductCanonicalUrlOptions,
    )
    promo_label_banner: 'Banner | None' = field(link_promo_label_banner)
