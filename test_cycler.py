from __future__ import (absolute_import, division, print_function)

import six
from six.moves import zip, range
from cycler import cycler, Cycler, RememberTheStyle as RTS
from nose.tools import (assert_equal, assert_not_equal,
                        assert_raises, assert_true)
from itertools import product, cycle
from operator import add, iadd, mul, imul


def _cycler_helper(c, length, keys, values):
    assert_equal(len(c), length)
    assert_equal(len(c), len(list(c)))
    assert_equal(c.keys, set(keys))

    for k, vals in zip(keys, values):
        for v, v_target in zip(c, vals):
            assert_equal(v[k], v_target)


def _cycles_equal(c1, c2):
    assert_equal(list(c1), list(c2))


def test_creation():
    c = cycler(c='rgb')
    yield _cycler_helper, c, 3, ['c'], [['r', 'g', 'b']]
    c = cycler(c=list('rgb'))
    yield _cycler_helper, c, 3, ['c'], [['r', 'g', 'b']]
    c = cycler(cycler(c='rgb'))
    yield _cycler_helper, c, 3, ['c'], [['r', 'g', 'b']]


def test_compose():
    c1 = cycler(c='rgb')
    c2 = cycler(lw=range(3))
    c3 = cycler(lw=range(15))
    # addition
    yield _cycler_helper, c1+c2, 3, ['c', 'lw'], [list('rgb'), range(3)]
    yield _cycler_helper, c2+c1, 3, ['c', 'lw'], [list('rgb'), range(3)]
    yield _cycles_equal, c2+c1, c1+c2
    # miss-matched add lengths
    assert_raises(ValueError, add, c1, c3)
    assert_raises(ValueError, add, c3, c1)

    # multiplication
    target = zip(*product(list('rgb'), range(3)))
    yield (_cycler_helper, c1 * c2, 9, ['c', 'lw'], target)

    target = zip(*product(range(3), list('rgb')))
    yield (_cycler_helper, c2 * c1, 9, ['lw', 'c'], target)

    target = zip(*product(range(15), list('rgb')))
    yield (_cycler_helper, c3 * c1, 45, ['lw', 'c'], target)


def test_inplace():
    c1 = cycler(c='rgb')
    c2 = cycler(lw=range(3))
    c2 += c1
    yield _cycler_helper, c2, 3, ['c', 'lw'], [list('rgb'), range(3)]

    c3 = cycler(c='rgb')
    c4 = cycler(lw=range(3))
    c3 *= c4
    target = zip(*product(list('rgb'), range(3)))
    yield (_cycler_helper, c3, 9, ['c', 'lw'], target)


def test_constructor():
    c1 = cycler(c='rgb')
    c2 = cycler(ec=c1)
    yield _cycler_helper, c1+c2, 3, ['c', 'ec'], [['r', 'g', 'b']]*2
    c3 = cycler(c=c1)
    yield _cycler_helper, c3+c2, 3, ['c', 'ec'], [['r', 'g', 'b']]*2
    # Using a non-string hashable
    c4 = cycler(1, range(3))
    yield _cycler_helper, c4+c1, 3, [1, 'c'], [range(3), ['r', 'g', 'b']]

    # addition using cycler()
    yield (_cycler_helper, cycler(c='rgb', lw=range(3)),
            3, ['c', 'lw'], [list('rgb'), range(3)])
    yield (_cycler_helper, cycler(lw=range(3), c='rgb'),
            3, ['c', 'lw'], [list('rgb'), range(3)])
    # Purposely mixing them
    yield (_cycler_helper, cycler(c=range(3), lw=c1),
            3, ['c', 'lw'], [range(3), list('rgb')])


def test_failures():
    c1 = cycler(c='rgb')
    c2 = cycler(c=c1)
    assert_raises(ValueError, add, c1, c2)
    assert_raises(ValueError, iadd, c1, c2)
    assert_raises(ValueError, mul, c1, c2)
    assert_raises(ValueError, imul, c1, c2)

    c3 = cycler(ec=c1)

    assert_raises(ValueError, cycler, c=c2+c3)


def test_simplify():
    c1 = cycler(c='rgb')
    c2 = cycler(ec=c1)
    for c in [c1 * c2, c2 * c1, c1 + c2]:
        yield _cycles_equal, c, c.simplify()


def test_multiply():
    c1 = cycler(c='rgb')
    yield _cycler_helper, 2*c1, 6, ['c'], ['rgb'*2]

    c2 = cycler(ec=c1)
    c3 = c1 * c2

    yield _cycles_equal, 2*c3, c3*2


def test_mul_fails():
    c1 = cycler(c='rgb')
    assert_raises(TypeError, mul, c1,  2.0)
    assert_raises(TypeError, mul, c1,  'a')
    assert_raises(TypeError, mul, c1,  [])


def test_getitem():
    c1 = cycler(3, range(15))
    widths = list(range(15))
    for slc in (slice(None, None, None),
                slice(None, None, -1),
                slice(1, 5, None),
                slice(0, 5, 2)):
        yield _cycles_equal, c1[slc], cycler(3, widths[slc])


def test_fail_getime():
    c1 = cycler(lw=range(15))
    assert_raises(ValueError, Cycler.__getitem__, c1, 0)
    assert_raises(ValueError, Cycler.__getitem__, c1, [0, 1])


def _repr_tester_helper(rpr_func, cyc, target_repr):
    test_repr = getattr(cyc, rpr_func)()

    assert_equal(six.text_type(test_repr),
                 six.text_type(target_repr))


def test_repr():
    c = cycler(c='rgb')
    # Using an identifier that would be not valid as a kwarg
    c2 = cycler('3rd', range(3))

    c_sum_rpr = "(cycler('c', ['r', 'g', 'b']) + cycler('3rd', [0, 1, 2]))"
    c_prod_rpr = "(cycler('c', ['r', 'g', 'b']) * cycler('3rd', [0, 1, 2]))"

    yield _repr_tester_helper, '__repr__', c + c2, c_sum_rpr
    yield _repr_tester_helper, '__repr__', c * c2, c_prod_rpr

    sum_html = "<table><th>'3rd'</th><th>'c'</th><tr><td>0</td><td>'r'</td></tr><tr><td>1</td><td>'g'</td></tr><tr><td>2</td><td>'b'</td></tr></table>"
    prod_html = "<table><th>'3rd'</th><th>'c'</th><tr><td>0</td><td>'r'</td></tr><tr><td>1</td><td>'r'</td></tr><tr><td>2</td><td>'r'</td></tr><tr><td>0</td><td>'g'</td></tr><tr><td>1</td><td>'g'</td></tr><tr><td>2</td><td>'g'</td></tr><tr><td>0</td><td>'b'</td></tr><tr><td>1</td><td>'b'</td></tr><tr><td>2</td><td>'b'</td></tr></table>"

    yield _repr_tester_helper, '_repr_html_', c + c2, sum_html
    yield _repr_tester_helper, '_repr_html_', c * c2, prod_html


def test_call():
    c = cycler(c='rgb')
    c_cycle = c()
    assert_true(isinstance(c_cycle, cycle))
    j = 0
    for a, b in zip(2*c, c_cycle):
        j += 1
        assert_equal(a, b)

    assert_equal(j, len(c) * 2)


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

    assert_equal(c1, cycler('c', [1, 2, 3]))
    assert_equal(c2, cycler('lw', ['r', 'g', 'b']))
    assert_equal(c3, cycler('foo', [['y', 'g', 'blue'], ['b', 'k']]))
    assert_equal(c_before, (cycler(c=[1, 2, 3], lw=['r', 'g', 'b']) *
                            cycler('foo', [['y', 'g', 'blue'], ['b', 'k']])))
    assert_equal(c_after, (cycler(c=[1, 2, 3], lw=['r', 'g', 'b']) *
                           cycler('foo', [['y', 'g', 'blue'], ['b', 'k']])))

    # Make sure that changing the key for a specific cycler
    # doesn't break things for a composed cycler
    c = (c1 + c2) * c3
    c4 = cycler('bar', c3)
    assert_equal(c, (cycler(c=[1, 2, 3], lw=['r', 'g', 'b']) *
                     cycler('foo', [['y', 'g', 'blue'], ['b', 'k']])))
    assert_equal(c3, cycler('foo', [['y', 'g', 'blue'], ['b', 'k']]))


def _eq_test_helper(a, b, res):
    if res:
        assert_equal(a, b)
    else:
        assert_not_equal(a, b)


def test_eq():
    a = cycler(c='rgb')
    b = cycler(c='rgb')
    yield _eq_test_helper, a, b, True
    yield _eq_test_helper, a, b[::-1], False
    c = cycler(lw=range(3))
    yield _eq_test_helper, a+c, c+a, True
    yield _eq_test_helper, a+c, c+b, True
    yield _eq_test_helper, a*c, c*a, False
    yield _eq_test_helper, a, c, False
    d = cycler(c='ymk')
    yield _eq_test_helper, b, d, False


def test_RTS():
    cy = cycler
    testing_cache = {}
    rts = RTS(cy('c', 'rgb') + cy('lw', range(3)))
    test_keys = ['cat', 'dog', 'aardvark']

    assert_equal(0, len(rts))
    assert_equal(set(), set(rts))
    assert_equal(testing_cache, dict(rts))

    for j, key in enumerate(test_keys):
        testing_cache[key] = rts[key]

        assert_equal(j + 1, len(rts))
        assert_equal(set(test_keys[:j+1]), set(rts))
        assert_equal(testing_cache, dict(rts))

    assert_raises(RuntimeError, RTS.__getitem__, rts, 'ant')

    for key in test_keys:
        assert_equal(len(test_keys), len(rts))
        assert_equal(testing_cache[key], rts[key])
        assert_equal(len(test_keys), len(rts))


def test_RTS_loop():
    cy = cycler
    testing_cache = {}
    rts = RTS(cy('c', 'rgb') + cy('lw', range(3)), loop=True)
    test_keys = ['cat', 'dog', 'aardvark']
    test_keys2 = ['mouse', 'duck', 'python']

    assert_equal(0, len(rts))
    assert_equal(set(), set(rts))
    assert_equal(testing_cache, dict(rts))

    all_keys = test_keys + test_keys2

    for j, key in enumerate(all_keys):
        testing_cache[key] = rts[key]

        assert_equal(j + 1, len(rts))
        assert_equal(set(all_keys[:j+1]), set(rts))
        assert_equal(testing_cache, dict(rts))

    for key in all_keys:
        assert_equal(len(all_keys), len(rts))
        assert_equal(testing_cache[key], rts[key])
        assert_equal(len(all_keys), len(rts))

    for k1, k2 in zip(test_keys, test_keys2):
        assert_equal(rts[k1], rts[k2])


def test_RTS_pre_cache():
    cy = cycler
    testing_cache = {}
    existing_cache = {'ant': {'c': 'k', 'lw': .5},
                      'duck': {'c': 'gray', 'lw': 3}}
    orig = dict(existing_cache)
    rts = RTS(cy('c', 'rgb') + cy('lw', range(3)),
              cache=existing_cache)
    assert_true(existing_cache is rts.style_cache)
    test_keys = ['cat', 'dog', 'aardvark']

    assert_equal(2, len(rts))
    assert_equal(set(['ant', 'duck']), set(rts))
    assert_equal(existing_cache, dict(rts))

    for j, key in enumerate(test_keys):
        testing_cache[key] = rts[key]
        rts['ant']
        rts['duck']
        assert_equal(j + 1 + 2, len(rts))
        assert_equal(set(test_keys[:j+1]) | set(['ant', 'duck']),
                     set(rts))
        res = dict(rts)
        for k in list(testing_cache):
            assert_equal(testing_cache[k], res[k])

        for k in ['ant', 'duck']:
            assert_equal(orig[k], res[k])

    assert_raises(RuntimeError, RTS.__getitem__, rts, 'hippo')

    for key in test_keys:
        assert_equal(len(test_keys) + 2, len(rts))
        assert_equal(testing_cache[key], rts[key])
        assert_equal(len(test_keys) + 2, len(rts))


def test_cycler_exceptions():
    assert_raises(TypeError, cycler)
    assert_raises(TypeError, cycler, 'c', 'rgb', lw=range(3))
    assert_raises(TypeError, cycler, 'c')
    assert_raises(TypeError, cycler, 'c', 'rgb', 'lw', range(3))


def test_starange_init():
    c = cycler('r', 'rgb')
    c2 = cycler('lw', range(3))
    cy = Cycler(list(c), list(c2), zip)
    assert_equal(cy, c + c2)
