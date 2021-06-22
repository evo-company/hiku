from collections import namedtuple


def _namedtuple(typename, field_names):
    """Fixes hashing for different tuples with same content
    """
    base = namedtuple(typename, field_names)

    def __hash__(self):
        return hash((self.__class__, super(base, self).__hash__()))

    return type(typename, (base,), {
        '__slots__': (),
        '__hash__': __hash__,
    })


SCALAR = _namedtuple('SCALAR', 'name')
OBJECT = _namedtuple('OBJECT', 'name')
DIRECTIVE = _namedtuple('DIRECTIVE', 'name')
INPUT_OBJECT = _namedtuple('INPUT_OBJECT', 'name')
LIST = _namedtuple('LIST', 'of_type')
NON_NULL = _namedtuple('NON_NULL', 'of_type')

FieldIdent = _namedtuple('FieldIdent', 'node, name')
FieldArgIdent = _namedtuple('FieldArgIdent', 'node, field, name')
InputObjectFieldIdent = _namedtuple('InputObjectFieldIdent', 'name, key')
DirectiveArgIdent = _namedtuple('DirectiveArgIdent', 'name')
