"""
Based on the code from https://github.com/gns24/pydatomic project
"""
from uuid import UUID
from decimal import Decimal
from datetime import datetime
from itertools import chain
from json.encoder import encode_basestring, encode_basestring_ascii


class ImmutableDict(dict):
    _hash = None

    def __hash__(self):
        if self._hash is None:
            self._hash = hash(frozenset(self.items()))
        return self._hash

    def _immutable(self):
        raise TypeError("{} object is immutable"
                        .format(self.__class__.__name__))

    __delitem__ = __setitem__ = _immutable
    clear = pop = popitem = setdefault = update = _immutable


class Symbol(str):

    def __repr__(self):
        return self

    def __eq__(self, other):
        return isinstance(other, type(self)) and \
            super(Symbol, self).__eq__(other)

    def __hash__(self):
        return super(Symbol, self).__hash__()


class Keyword(str):

    def __repr__(self):
        return ':{}'.format(self)

    def __eq__(self, other):
        return isinstance(other, type(self)) and \
            super(Keyword, self).__eq__(other)

    def __hash__(self):
        return super(Keyword, self).__hash__()


class List(tuple):

    def __repr__(self):
        return '[{}]'.format(' '.join(map(repr, self)))


class Tuple(tuple):

    def __repr__(self):
        return '({})'.format(' '.join(map(repr, self)))


class Dict(ImmutableDict):

    def __repr__(self):
        return '{{{}}}'.format(' '.join('{!r} {!r}'.format(*i)
                               for i in self.items()))


class Set(frozenset):

    def __repr__(self):
        return '#{{{}}}'.format(' '.join(map(repr, self)))


class TaggedElement:

    def __init__(self, name, value):
        self.name = name
        self.value = value

    def __repr__(self):
        return '#{} {!r}'.format(self.name, self.value)

    def __eq__(self, other):
        return isinstance(other, type(self)) and \
            self.name == other.name and self.value == other.value


def coroutine(func):
    def start(*args, **kwargs):
        cr = func(*args, **kwargs)
        next(cr)
        return cr
    return start


@coroutine
def appender(l):
    while True:
        l.append((yield))


def inst_handler(time_string):
    return datetime.strptime(time_string, '%Y-%m-%dT%H:%M:%S.%fZ')


TAG_HANDLERS = {'inst': inst_handler, 'uuid': UUID}

STOP_CHARS = " ,\n\r\t"

_CHAR_HANDLERS = {
    'newline': '\n',
    'space': ' ',
    'tab': '\t',
}

_CHAR_MAP = {
    "a": "\a",
    "b": "\b",
    "f": "\f",
    "n": "\n",
    "r": "\r",
    "t": "\t",
    "v": "\v",
}

_END_CHARS = {
    '#': '}',
    '{': '}',
    '[': ']',
    '(': ')',
}

_NIL = object()


@coroutine
def tag_handler(tag_name, tag_handlers):
    while True:
        c = (yield)
        if c in STOP_CHARS + '{"[(\\#':
            break
        tag_name += c
    elements = []
    handler = parser(appender(elements), tag_handlers)
    handler.send(c)
    while not elements:
        handler.send((yield))
    if tag_name in tag_handlers:
        yield tag_handlers[tag_name](elements[0]), True
    else:
        yield TaggedElement(tag_name, elements[0]), True
        yield None, True


@coroutine
def character_handler():
    r = (yield)
    while 1:
        c = (yield)
        if not c.isalpha():
            if len(r) == 1:
                yield r, False
            else:
                yield _CHAR_HANDLERS[r], False
        r += c


def parse_number(s):
    s = s.rstrip('MN').upper()
    if 'E' not in s and '.' not in s:
        return int(s)
    return float(s)


@coroutine
def number_handler(s):
    while 1:
        c = (yield)
        if c in "0123456789+-eEMN.":
            s += c
        else:
            yield parse_number(s), False


@coroutine
def symbol_handler(s):
    while 1:
        c = (yield)
        if c in '}])' + STOP_CHARS:
            if s[0] == ':':
                yield Keyword(s[1:]), False
            elif s == 'true':
                yield True, False
            elif s == 'false':
                yield False, False
            elif s == 'nil':
                yield _NIL, False
            else:
                yield Symbol(s), False
        else:
            s += c


@coroutine
def parser(target, tag_handlers, stop=None):
    handler = None
    while True:
        c = (yield)
        if handler:
            v = handler.send(c)
            if v is None:
                continue
            else:
                handler = None
                v, consumed = v
                if v is not None:
                    if v is _NIL:
                        target.send(None)
                    else:
                        target.send(v)
                if consumed:
                    continue
        if c == stop:
            return
        if c in STOP_CHARS:
            continue
        if c == ';':
            while (yield) != '\n':
                pass
        elif c == '"':
            chars = []
            while 1:
                char = (yield)
                if char == '\\':
                    char = (yield)
                    char2 = _CHAR_MAP.get(char)
                    if char2 is not None:
                        chars.append(char2)
                    else:
                        chars.append(char)
                elif char == '"':
                    target.send(''.join(chars))
                    break
                else:
                    chars.append(char)
        elif c == '\\':
            handler = character_handler()
        elif c in '0123456789':
            handler = number_handler(c)
        elif c in '-.':
            c2 = (yield)
            if c2.isdigit():  # .5 should be an error
                handler = number_handler(c + c2)
            else:
                handler = symbol_handler(c + c2)
        elif c.isalpha() or c == ':':
            handler = symbol_handler(c)
        elif c in '[({#':
            if c == '#':
                c2 = (yield)
                if c2 != '{':
                    handler = tag_handler(c2, tag_handlers)
                    continue
            end_char = _END_CHARS[c]
            lst = []
            p = parser(appender(lst), tag_handlers, stop=end_char)
            try:
                while 1:
                    p.send((yield))
            except StopIteration:
                pass
            if c == '[':
                target.send(List(lst))
            elif c == '(':
                target.send(Tuple(lst))
            elif c == '{':
                if len(lst) % 2:
                    raise Exception("Map literal must contain an even "
                                    "number of elements")
                target.send(Dict(zip(lst[::2], lst[1::2])))
            else:
                target.send(Set(lst))
        else:
            raise ValueError("Unexpected character in edn", c)


def loads(s, tag_handlers=None):
    if not isinstance(s, str):
        raise TypeError('The EDN value must be "str", not {!r}'
                        .format(type(s).__name__))
    lst = []
    target = parser(appender(lst), dict(tag_handlers or (), **TAG_HANDLERS))
    for c in s:
        target.send(c)
    target.send(' ')
    if len(lst) != 1:
        raise ValueError("Expected exactly one top-level element "
                         "in edn string", s)
    return lst[0]


def _iterencode_items(items, default, encoder):
    items_iter = iter(items)
    try:
        first = next(items_iter)
    except StopIteration:
        return
    for chunk in _iterencode(first, default, encoder):
        yield chunk
    while True:
        try:
            next_item = next(items_iter)
        except StopIteration:
            return
        yield ' '
        for chunk in _iterencode(next_item, default, encoder):
            yield chunk


def _default(obj):
    raise ValueError('{!r} is not EDN serializable'.format(obj))


def _iterencode(obj, default, encoder):
    if obj is None:
        yield 'nil'
    elif obj is True:
        yield 'true'
    elif obj is False:
        yield 'false'
    elif isinstance(obj, int):
        yield str(int(obj))
    elif isinstance(obj, float):
        # FIXME: proper float encoding
        yield str(float(obj))
    elif isinstance(obj, Decimal):
        yield '{}M'.format(obj)
    elif isinstance(obj, Keyword):
        yield ':{}'.format(obj)
    elif isinstance(obj, Symbol):
        yield obj
    elif isinstance(obj, str):
        yield encoder(obj)
    elif isinstance(obj, (list, List)):
        # NOTE: `(list, List)` check should be before `(tuple, Tuple)`,
        # because `List` is implemented as tuple subclass
        yield '['
        for chunk in _iterencode_items(obj, default, encoder):
            yield chunk
        yield ']'
    elif isinstance(obj, (tuple, Tuple)):
        yield '('
        for chunk in _iterencode_items(obj, default, encoder):
            yield chunk
        yield ')'
    elif isinstance(obj, (dict, Dict)):
        yield '{'
        for chunk in _iterencode_items(chain.from_iterable(obj.items()),
                                       default, encoder):
            yield chunk
        yield '}'
    elif isinstance(obj, (set, Set)):
        yield '#{'
        for chunk in _iterencode_items(obj, default, encoder):
            yield chunk
        yield '}'
    elif isinstance(obj, datetime):
        # FIXME: proper RFC-3339 encoding
        assert not obj.tzinfo
        yield obj.strftime('#inst "%Y-%m-%dT%H:%M:%S.%fZ"')
    elif isinstance(obj, UUID):
        yield '#uuid "{}"'.format(obj)
    elif isinstance(obj, TaggedElement):
        yield '#{} '.format(obj.name)
        for chunk in _iterencode(obj.value, _default, encoder):
            yield chunk
    else:
        obj = default(obj)
        for chunk in _iterencode(obj, default, encoder):
            yield chunk


def dumps(obj, default=None, ensure_ascii=True):
    if default is None:
        default = _default
    if ensure_ascii:
        encoder = encode_basestring_ascii
    else:
        encoder = encode_basestring
    return ''.join(_iterencode(obj, default, encoder))
