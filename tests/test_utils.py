import pytest

from hiku.utils import kw_only


class Eliza(object):

    def normal(self, a, b=None, c=-1, **kwargs):
        d, e, f, g = kw_only(self.normal, kwargs, ['d', 'e'],
                             [('f', None), ('g', 'pooh')])
        return [a, b, c, d, e, f, g]


def planter(a, b=None, c=-1, **kwargs):
    d, e, f, g = kw_only(planter, kwargs, ['d', 'e'],
                         [('f', None), ('g', 'pooh')])
    return [a, b, c, d, e, f, g]


@pytest.mark.parametrize('fn, name', [(Eliza().normal, 'Eliza.normal'),
                                      (planter, 'planter')])
def test_kw_only(fn, name):
    assert fn(1, d=4, e=5) == [1, None, -1, 4, 5, None, 'pooh']
    assert fn(1, 2, d=4, e=5) == [1, 2, -1, 4, 5, None, 'pooh']
    assert fn(1, 2, 3, d=4, e=5) == [1, 2, 3, 4, 5, None, 'pooh']
    assert fn(1, d=4, e=5, f=6) == [1, None, -1, 4, 5, 6, 'pooh']
    assert fn(1, d=4, e=5, f=6, g='dinghy') == [1, None, -1, 4, 5, 6, 'dinghy']

    with pytest.raises(TypeError) as m1_err:
        fn(1, d=4)
    m1_err.match('{}\\(\\) missing 1 required keyword-only argument: {!r}'
                 .format(name, 'e'))

    with pytest.raises(TypeError) as m2_err:
        fn(1)
    m2_err.match('{}\\(\\) missing 2 required keyword-only arguments: {!r} and '
                 '{!r}'.format(name, 'd', 'e'))

    with pytest.raises(TypeError) as u1_err:
        fn(1, d=4, e=5, h=6)
    u1_err.match('{}\\(\\) got 1 unexpected keyword argument: {!r}'
                 .format(name, 'h'))

    with pytest.raises(TypeError) as u3_err:
        fn(1, d=4, e=5, h=6, j=7, k=8)
    u3_err.match('{}\\(\\) got 3 unexpected keyword arguments: {!r}, {!r} and '
                 '{!r}'.format(name, 'h', 'j', 'k'))
