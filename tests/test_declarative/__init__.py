'''Exploring all kinds of stuff'''

# def get_proper_name_from_obj(obj):
#     return get_proper_name(obj.name)


# def get_url_for_catalog_from_obj(obj):
#     return get_url_for_catalog(obj.id, obj.name, obj.company_id, obj.company_name)


# def get_companies(objs: list) -> list:
#     companies_map = await get_companies([obj.id for obj in objs])

#     return [
#         ProductCompanyCtx(
#             id=obj.id,
#             name=obj.name,
#             company_id=companies_map[obj.id].id,
#             company_name=companies_map[obj.id].name,
#         ) for obj in objs
#     ]


# def get_products_data(objs):
#     return fetch_data_for_objs(objs)

# @hiku.preprocess(ProductDB.load(ProductDB))
# @hiku.postprocess(fetch_banners)
# def get_promo_advantages(product_data):
#     if not flag:
#         return None
#     if not_avail_for_delivery(product_data):
#         return None
#     ...
#     return [EnumValue1, EnumValue2, EnumValue3]


# def fetch_banners(banners_labels):
#     uniq_labels = set(chain.from_iterable(banner_lists))
#     banners = fetch_banners(unique_labels)
#     label_to_banner = {banner.label: banner for banner in banners}
#     return [[label_to_banner.get(label) for label in labels] for labels in banners_labels]

from typing import Any, TypeVar
import functools
from collections.abc import Callable, Hashable

from hiku.engine import Context

from hiku.graph import Field as GraphField, Node as GraphNode, Option
from hiku.directives import DirectiveBase

Options = dict

TKey = TypeVar('TKey', bound=Hashable)

TIn = TypeVar('TIn')
TOut = TypeVar('TOut')


def foreach(
    func: Callable[[TIn, Context, Options], TOut],
) -> Callable[[list[TIn], Context, Options], list[TOut]]:

    @functools.wraps(func)
    def resolver(data: list[TIn], ctx: Context, opts: Options) -> list[TOut]:
        return [func(i, ctx, opts) for i in data]

    return resolver


def identity(objs: list[TKey], ctx: Context, opts: Options) -> list[TKey]:
    return objs


class hiku:
    deprecated: DirectiveBase

    class resolver:
        def __init__(
            self,
            preload: Callable[[list[TKey], Context], list[TRes]] | None = None,
            
        )

    @staticmethod
    def node(*args, **kwargs) -> Any:
        ...

    @staticmethod
    def field(*args, **kwargs) -> Any:
        ...

    @staticmethod
    def require(*args, **kwargs) -> Any:
        ...

    @staticmethod
    def opt(*args, **kwargs) -> Any:
        ...

    @staticmethod
    def dataloader(*args, **kwargs) -> Any:
        ...

    @staticmethod
    def loadfield(*args, **kwargs) -> Any:
        ...

    @staticmethod
    def link(*args, **kwargs) -> Any:
        ...


@hiku.dataloader(int)
class CompanyDB:
    id: int = hiku.loadfield(company_query)
    name: str = hiku.loadfield(company_query)


@hiku.dataloader(int)
class ProductDB:
    id: int = hiku.loadfield(product_query)
    name: str = hiku.loadfield(product_query)
    company_id: int = hiku.loadfield(product_query)

    company: Annotated['CompanyDB', '.company'] = hiku.link(
        link_company,
        requires=['company_id'],
    )


def get_url_for_catalog(
    productdb: ProductDB,
    ctx: Context,
    opts: Options,
) -> str:
    companydb = productdb.company
    return f'{productdb.id} {productdb.name} {companydb.id} {companydb.name}'


async def fetch_some_companies(
    c_ids: list[int],
    id: int,
    name: str,
) -> list[list[int]]:
    ...


async def get_some_companies(
    products: list[ProductDB],
    ctx: Context,
    opts: Options,
) -> list[list[int]]:
    company_ids = [p.company_id for p in products]
    return await fetch_some_companies(company_ids, opts['id'], opts['name'])


@hiku.node(int)
class Company:
    id: int = hiku.field(resolve=identity)


@hiku.node(int)
class Product:
    id: int = hiku.field(preload=ProductDB.load(ProductDB.id))
    name: str = hiku.field(preload=ProductDB.load(ProductDB.name))
    url_for_catalog: str = hiku.field(
        resolve=foreach(get_url_for_catalog),
        preload=ProductDB.load(
            ProductDB.id,
            ProductDB.name,
            ProductDB.company.id,
            ProductDB.company.name,
        )
    )
    company_id: int = hiku.field(preload=ProductDB.load(ProductDB.company_id))
    company: Company = hiku.field(
        resolve=identity,
        preload=hiku.require(lambda: (Product.company_id,)),
    )
    some_companies: list[Company] = hiku.field(
        resolve=get_some_companies,
        preload=ProductDB.load(
            ProductDB.id,
            ProductDB.company_id,
        ),
        options=[
            hiku.opt('id', int),
            hiku.opt('name', str)
        ],
        directives=[hiku.deprecated],
    )


# def mapper(fields, objs):

#     companies_map = await get_companies([obj.id for obj in objs])

#     def get_field(obj, field):
#         company = companies_map[obj.id]
#         if field.name == 'id':
#             return obj.id
#         if field.name == 'name':
#             return get_proper_name(obj.name)
#         if field.name == 'urlForCatalog':
#             return get_url_for_catalog(obj.id, obj.name, company.id, company.name)
#         if field.name == 'companyId':
#             return company.id
#         return None

#     return [
#         [get_field(obj, field) for field in fields]
#         for obj in objs
#     ]



# class ProductDB:

#     def resolve(cls, *args: *TArgs):

#         def wrapper(func: Callable[[*TArgs, Opts, Ctx], T])


#         return wrapper

# @ProductDB.resolve(
#     ProductDB.id,
#     ProductDB.name,
#     ProductDB._translation_modified_data,
#     ProductDB.company.delivery_regions,
#     ProductDB.company.address.region_id,
#     ProductDB.variation.id,
#     ProductDB.variation.name,
#     ProductDB.variation._translation_modified_data,
# )
# def product_name_for_catalog(id, name, opts, ctx):
#     return x

# class Product:
#     id: int = field(preprocess=product_sg(ProductDB.id))
#     name: str = field(ProductDB.name)
#     nameForCatalog: str = field(product_sg.c(product_name_for_catalog))
#     urlForCanonical: str | None = get_product_canonical_url(
#         ProductDB.id,
#         ProductDB.name,
#         ProductDB._translation_modified_data,
#         ProductDB.company.delivery_regions,
#         ProductDB.company.address.region_id,
#         ProductDB.variation.id,
#         ProductDB.variation.name,
#         ProductDB.variation._translation_modified_data,
#     )
#     promo_label_banner: list[Banner] = field(
#         preload=product_sg.load(
#             ProductDB.id,
#             ProductDB.name,
#             ProductDB...,
#         ),
#         resolve=get_banners,
#     )


# def field(
#     pre: Callable[[list[TKey], Ctx, Opts], TPre],
#     resolve: TResolver[TPreOut, TPostIn],
#     post: Callable[[list[TRes], Ctx, Opts], TKeyRes]
# ):
#     resolve_full = 


# def field(
#     pre: None = None,
#     resolve: Callable[[TKey, Ctx, Opts], TKeyRes],
#     post: None = None,
# )


# def field(
#     resolve: Callable[[TKey, Ctx, Opts], TRes],
#     post: Callable[[list[TRes], Ctx, Opts], TKeyRes],
#     pre: None = None,
# )

# def field(
#     pre: Callable[[list[TKey], Ctx, Opts], TPre],
#     resolve: Callable[[TPre, Ctx, Opts], TKeyRes],
#     post: None = None,
# )


# def resolver(resolve):
#     def wrapper(objs, ctx, opts):
#         return 


# def get_field(field, obj, ctx, opts):
#     return field.resolve(obj, ctx, opts)


# lambda: True


# def mapper(ctx, objs, fields):
#     res = [[] for _ in range(objs)]

#     preprocs =  {pre for field in fields if (pre := field.pre)}
#     obj_by_preproc = {pre: pre(objs, ctx) for pre in preprocs}

#     field_results = []
#     for field in fields:
#         objs = obj_by_preproc.get(field.pre, objs)

#         field_res = [
#             field.resolve(obj, ctx, *field.opts)
#             for obj in objs
#         ]
#         field_results = field.post(field_res, ctx) if field.post else field_res
#         for i, res in enumerate(field_results):
#             res[i].append(res)

#     return res


# class FullResolver:
#     pass_context = True

#     def __call__(self, ctx, objs, fields):
#         res = [[] for _ in range(objs)]

#         preprocs =  {pre for field in fields if (pre := field.pre)}
#         obj_by_preproc = {pre: pre(objs, ctx) for pre in preprocs}

#         field_results = []
#         for field in fields:
#             objs = obj_by_preproc.get(field.pre, objs)

#             field_res = [
#                 field.resolve(obj, ctx, *field.opts)
#                 for obj in objs
#             ]
#             field_results = field.post(field_res, ctx) if field.post else field_res
#             for i, res in enumerate(field_results):
#                 res[i].append(res)

#         return res
from types import UnionType
import dataclasses
import functools
from collections.abc import Callable, Sequence, Hashable
from typing import TypeVar, Generic, NewType, TypeAlias, Any

from hiku.engine import Context

from hiku.graph import Field as GraphField, Node as GraphNode, Option, Directive


Options = dict


ID = NewType(str)
CustomScalar = NewType(object)

TScalars = int | float | str | bool | ID | CustomScalar
TObjects: TypeAlias = 'Node | Callable[[], Node]'
TList = list[TScalars]
TNullable = None
TInterfaces: TypeAlias = 'Interface | Callable[[], Interface]'
TUnions = UnionType | Callable[[], UnionType]

FieldTypes = TScalars | TObjects | TList | TNullable | TInterfaces | TUnions


TKey = TypeVar('TKey', bound=Hashable)
TField = TypeVar('TField', bound=FieldTypes)
TNode = TypeVar('TNode', bound='GraphNode')

TIn = TypeVar('TIn')
TOut = TypeVar('TOut')

TPreloaded = TypeVar('TPreloaded')
TPostIn = TypeVar('TPostIn')


class QField:
    ...


class Interface:
    ...


type_map = {}


def process_type(type_: type):
    ...


def default_resolver(objs, fields):
    return [
        [getattr(obj, f.name) for f in fields]
        for obj in objs
    ]


def to_camel_case(name):
    return name


def node(key_type: type, obj, name, description, directives):
    obj = dataclasses.dataclass(obj)

    fields = []
    for field in obj.__fields__:
        if isinstance(field, Field):
            fields.append(
                GraphField(
                    field.name,
                    process_type(field.type),
                    field.resolver,
                    options=field.options,
                    description=field.description,
                    directives=field.directives,
                )
            )
        else:
            default = getattr(obj, field.name, dataclasses.MISSING)
            if default is not dataclasses.MISSING:

                def func(objs, fields):
                    return [[default] * len(fields)] * len(objs)

                resolver = func
            else:
                resolver = default_resolver
            fields.append(
                GraphField(
                    to_camel_case(field.name),
                    process_type(field.type),
                    resolver,
                )
            )

    return GraphNode(
        name or obj.__name__,
        fields,
        description=description,
        directives=directives,
    )


@dataclasses.dataclass
class Field(Generic[TKey, TField, TPreloaded, TPostIn]):
    name: str
    type: TField
    options: list[Option] | None
    description: str | None
    directives: list[Directive] | None
    preload: Callable[[list[TKey]], list[TPreloaded]]
    resolver: Callable[[list[TPreloaded]], list[TField]]


def field(
    name: str | None = None,
    full_resolve: Callable[[Context, list[TKey], list[QField]], list[list]] | None = None,
    options: list[Option] | None = None,
    directives: list[Directive] | None = None,
    description: str | None = None,
    pre=None, post=None, resolve=None,
) -> Any:
    return Field(...)


class SubgraphLoader(Generic[TKey, TRes]):

    def __init__(self, subgraph):
        self._subgraph = subgraph

    @classmethod
    def load(cls, *fields) -> Callable[[list[TKey], Context], list[Self]]:
        cls._loader.add_many(fields)
        return cls._loader
