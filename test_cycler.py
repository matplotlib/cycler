from __future__ import (absolute_import, division, print_function)

from collections import defaultdict
from operator import add, iadd, mul, imul
from itertools import product, cycle, chain
import sys

import pytest

from cycler import cycler, Cycler, concat

if sys.version_info < (3,):
    from itertools import izip as zip
    range = xrange
    str = unicode


def _cycler_helper(c, length, keys, values):
    assert len(c) == length
    assert len(c) == len(list(c))
    assert c.keys == set(keys)
    for k, vals in zip(keys, values):
        for v, v_target in zip(c, vals):
            assert v[k] == v_target


def _cycles_equal(c1, c2):
    assert list(c1) == list(c2)
    assert c1 == c2


@pytest.mark.parametrize('c', [cycler(c='rgb'),
                               cycler(c=list('rgb')),
                               cycler(cycler(c='rgb'))],
                         ids=['from string',
                              'from list',
                              'from cycler'])
def test_creation(c):
    _cycler_helper(c, 3, ['c'], [['r', 'g', 'b']])


def test_add():
    c1 = cycler(c='rgb')
    c2 = cycler(lw=range(3))
    # addition
    _cycler_helper(c1+c2, 3, ['c', 'lw'], [list('rgb'), range(3)])
    _cycler_helper(c2+c1, 3, ['c', 'lw'], [list('rgb'), range(3)])
    _cycles_equal(c2+c1, c1+c2)


def test_add_len_mismatch():
    # miss-matched add lengths
    c1 = cycler(c='rgb')
    c3 = cycler(lw=range(15))
    with pytest.raises(ValueError):
        c1 + c3
    with pytest.raises(ValueError):
        c3 + c1


def test_prod():
    c1 = cycler(c='rgb')
    c2 = cycler(lw=range(3))
    c3 = cycler(lw=range(15))
    # multiplication
    target = zip(*product(list('rgb'), range(3)))
    _cycler_helper(c1 * c2, 9, ['c', 'lw'], target)

    target = zip(*product(range(3), list('rgb')))
    _cycler_helper(c2 * c1, 9, ['lw', 'c'], target)

    target = zip(*product(range(15), list('rgb')))
    _cycler_helper(c3 * c1, 45, ['lw', 'c'], target)


def test_inplace():
    c1 = cycler(c='rgb')
    c2 = cycler(lw=range(3))
    c2 += c1
    _cycler_helper(c2, 3, ['c', 'lw'], [list('rgb'), range(3)])

    c3 = cycler(c='rgb')
    c4 = cycler(lw=range(3))
    c3 *= c4
    target = zip(*product(list('rgb'), range(3)))
    _cycler_helper(c3, 9, ['c', 'lw'], target)


def test_constructor():
    c1 = cycler(c='rgb')
    c2 = cycler(ec=c1)
    _cycler_helper(c1+c2, 3, ['c', 'ec'], [['r', 'g', 'b']]*2)
    c3 = cycler(c=c1)
    _cycler_helper(c3+c2, 3, ['c', 'ec'], [['r', 'g', 'b']]*2)
    # Using a non-string hashable
    c4 = cycler(1, range(3))
    _cycler_helper(c4+c1, 3, [1, 'c'], [range(3), ['r', 'g', 'b']])

    # addition using cycler()
    _cycler_helper(cycler(c='rgb', lw=range(3)),
                   3, ['c', 'lw'], [list('rgb'), range(3)])
    _cycler_helper(cycler(lw=range(3), c='rgb'),
                   3, ['c', 'lw'], [list('rgb'), range(3)])
    # Purposely mixing them
    _cycler_helper(cycler(c=range(3), lw=c1),
                   3, ['c', 'lw'], [range(3), list('rgb')])


def test_failures():
    c1 = cycler(c='rgb')
    c2 = cycler(c=c1)
    pytest.raises(ValueError, add, c1, c2)
    pytest.raises(ValueError, iadd, c1, c2)
    pytest.raises(ValueError, mul, c1, c2)
    pytest.raises(ValueError, imul, c1, c2)
    pytest.raises(TypeError, iadd, c2, 'aardvark')
    pytest.raises(TypeError, imul, c2, 'aardvark')

    c3 = cycler(ec=c1)

    pytest.raises(ValueError, cycler, c=c2+c3)


def test_simplify():
    c1 = cycler(c='rgb')
    c2 = cycler(ec=c1)
    for c in [c1 * c2, c2 * c1, c1 + c2]:
        _cycles_equal(c, c.simplify())


def test_multiply():
    c1 = cycler(c='rgb')
    _cycler_helper(2*c1, 6, ['c'], ['rgb'*2])

    c2 = cycler(ec=c1)
    c3 = c1 * c2

    _cycles_equal(2*c3, c3*2)


def test_mul_fails():
    c1 = cycler(c='rgb')
    pytest.raises(TypeError, mul, c1, 2.0)
    pytest.raises(TypeError, mul, c1, 'a')
    pytest.raises(TypeError, mul, c1, [])


def test_getitem():
    c1 = cycler(3, range(15))
    widths = list(range(15))
    for slc in (slice(None, None, None),
                slice(None, None, -1),
                slice(1, 5, None),
                slice(0, 5, 2)):
        _cycles_equal(c1[slc], cycler(3, widths[slc]))


def test_fail_getime():
    c1 = cycler(lw=range(15))
    pytest.raises(ValueError, Cycler.__getitem__, c1, 0)
    pytest.raises(ValueError, Cycler.__getitem__, c1, [0, 1])


def _repr_tester_helper(rpr_func, cyc, target_repr):
    test_repr = getattr(cyc, rpr_func)()

    assert str(test_repr) == str(target_repr)


def test_repr():
    c = cycler(c='rgb')
    # Using an identifier that would be not valid as a kwarg
    c2 = cycler('3rd', range(3))

    c_sum_rpr = "(cycler('c', ['r', 'g', 'b']) + cycler('3rd', [0, 1, 2]))"
    c_prod_rpr = "(cycler('c', ['r', 'g', 'b']) * cycler('3rd', [0, 1, 2]))"

    _repr_tester_helper('__repr__', c + c2, c_sum_rpr)
    _repr_tester_helper('__repr__', c * c2, c_prod_rpr)

    sum_html = "<table><th>'3rd'</th><th>'c'</th><tr><td>0</td><td>'r'</td></tr><tr><td>1</td><td>'g'</td></tr><tr><td>2</td><td>'b'</td></tr></table>"
    prod_html = "<table><th>'3rd'</th><th>'c'</th><tr><td>0</td><td>'r'</td></tr><tr><td>1</td><td>'r'</td></tr><tr><td>2</td><td>'r'</td></tr><tr><td>0</td><td>'g'</td></tr><tr><td>1</td><td>'g'</td></tr><tr><td>2</td><td>'g'</td></tr><tr><td>0</td><td>'b'</td></tr><tr><td>1</td><td>'b'</td></tr><tr><td>2</td><td>'b'</td></tr></table>"

    _repr_tester_helper('_repr_html_', c + c2, sum_html)
    _repr_tester_helper('_repr_html_', c * c2, prod_html)


def test_call():
    c = cycler(c='rgb')
    c_cycle = c()
    assert isinstance(c_cycle, cycle)
    j = 0
    for a, b in zip(2*c, c_cycle):
        j += 1
        assert a == b

    assert j == len(c) * 2


def test_copying():
    # Just about everything results in copying the cycler and
    # its contents (shallow). This set of tests is intended to make sure
    # of that. Our iterables will be mutable for extra fun!
    i1 = [1, 2, 3]
    i2 = ['r', 'g', 'b']
    # For more mutation fun!
    i3 = [['y', 'g'], ['b', 'k']]

    c1 = cycler('c', i1)
    c2 = cycler('lw', i2)
    c3 = cycler('foo', i3)

    c_before = (c1 + c2) * c3

    i1.pop()
    i2.append('cyan')
    i3[0].append('blue')

    c_after = (c1 + c2) * c3

    assert c1 == cycler('c', [1, 2, 3])
    assert c2 == cycler('lw', ['r', 'g', 'b'])
    assert c3 == cycler('foo', [['y', 'g', 'blue'], ['b', 'k']])
    assert c_before == (cycler(c=[1, 2, 3], lw=['r', 'g', 'b']) *
                        cycler('foo', [['y', 'g', 'blue'], ['b', 'k']]))
    assert c_after == (cycler(c=[1, 2, 3], lw=['r', 'g', 'b']) *
                       cycler('foo', [['y', 'g', 'blue'], ['b', 'k']]))

    # Make sure that changing the key for a specific cycler
    # doesn't break things for a composed cycler
    c = (c1 + c2) * c3
    c4 = cycler('bar', c3)
    assert c == (cycler(c=[1, 2, 3], lw=['r', 'g', 'b']) *
                 cycler('foo', [['y', 'g', 'blue'], ['b', 'k']]))
    assert c3 == cycler('foo', [['y', 'g', 'blue'], ['b', 'k']])


def test_keychange():
    c1 = cycler('c', 'rgb')
    c2 = cycler('lw', [1, 2, 3])
    c3 = cycler('ec', 'yk')

    c3.change_key('ec', 'edgecolor')
    assert c3 == cycler('edgecolor', c3)

    c = c1 + c2
    c.change_key('lw', 'linewidth')
    # Changing a key in one cycler should have no
    # impact in the original cycler.
    assert c2 == cycler('lw', [1, 2, 3])
    assert c == c1 + cycler('linewidth', c2)

    c = (c1 + c2) * c3
    c.change_key('c', 'color')
    assert c1 == cycler('c', 'rgb')
    assert c == (cycler('color', c1) + c2) * c3

    # Perfectly fine, it is a no-op
    c.change_key('color', 'color')
    assert c == (cycler('color', c1) + c2) * c3

    # Can't change a key to one that is already in there
    pytest.raises(ValueError, Cycler.change_key, c, 'color', 'lw')
    # Can't change a key you don't have
    pytest.raises(KeyError, Cycler.change_key, c, 'c', 'foobar')


def _eq_test_helper(a, b, res):
    if res:
        assert a == b
    else:
        assert a != b


def test_eq():
    a = cycler(c='rgb')
    b = cycler(c='rgb')
    _eq_test_helper(a, b, True)
    _eq_test_helper(a, b[::-1], False)
    c = cycler(lw=range(3))
    _eq_test_helper(a+c, c+a, True)
    _eq_test_helper(a+c, c+b, True)
    _eq_test_helper(a*c, c*a, False)
    _eq_test_helper(a, c, False)
    d = cycler(c='ymk')
    _eq_test_helper(b, d, False)
    e = cycler(c='orange')
    _eq_test_helper(b, e, False)


def test_cycler_exceptions():
    pytest.raises(TypeError, cycler)
    pytest.raises(TypeError, cycler, 'c', 'rgb', lw=range(3))
    pytest.raises(TypeError, cycler, 'c')
    pytest.raises(TypeError, cycler, 'c', 'rgb', 'lw', range(3))


def test_starange_init():
    c = cycler('r', 'rgb')
    c2 = cycler('lw', range(3))
    cy = Cycler(list(c), list(c2), zip)
    assert cy == c + c2


def test_concat():
    a = cycler('a', range(3))
    b = cycler('a', 'abc')
    for con, chn in zip(a.concat(b), chain(a, b)):
        assert con == chn

    for con, chn in zip(concat(a, b), chain(a, b)):
        assert con == chn


def test_concat_fail():
    a = cycler('a', range(3))
    b = cycler('b', range(3))
    pytest.raises(ValueError, concat, a, b)
    pytest.raises(ValueError, a.concat, b)


def _by_key_helper(cy):
    res = cy.by_key()
    target = defaultdict(list)
    for sty in cy:
        for k, v in sty.items():
            target[k].append(v)

    assert res == target


def test_by_key_add():
    input_dict = dict(c=list('rgb'), lw=[1, 2, 3])
    cy = cycler(c=input_dict['c']) + cycler(lw=input_dict['lw'])
    res = cy.by_key()
    assert res == input_dict
    _by_key_helper(cy)


def test_by_key_mul():
    input_dict = dict(c=list('rg'), lw=[1, 2, 3])
    cy = cycler(c=input_dict['c']) * cycler(lw=input_dict['lw'])
    res = cy.by_key()
    assert input_dict['lw'] * len(input_dict['c']) == res['lw']
    _by_key_helper(cy)


def test_contains():
    a = cycler('a', range(3))
    b = cycler('b', range(3))

    assert 'a' in a
    assert 'b' in b
    assert 'a' not in b
    assert 'b' not in a

    ab = a+b

    assert 'a' in ab
    assert 'b' in ab
