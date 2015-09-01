"""
Cycler
======

Cycling through combinations of values, producing dictionaries.

You can add cyclers::

    from cycler import cycler
    cc = (cycler(color=list('rgb')) +
          cycler(linestyle=['-', '--', '-.']))
    for d in cc:
        print(d)

Results in::

    {'color': 'r', 'linestyle': '-'}
    {'color': 'g', 'linestyle': '--'}
    {'color': 'b', 'linestyle': '-.'}


You can multiply cyclers::

    from cycler import cycler
    cc = (cycler(color=list('rgb')) *
          cycler(linestyle=['-', '--', '-.']))
    for d in cc:
        print(d)

Results in::

    {'color': 'r', 'linestyle': '-'}
    {'color': 'r', 'linestyle': '--'}
    {'color': 'r', 'linestyle': '-.'}
    {'color': 'g', 'linestyle': '-'}
    {'color': 'g', 'linestyle': '--'}
    {'color': 'g', 'linestyle': '-.'}
    {'color': 'b', 'linestyle': '-'}
    {'color': 'b', 'linestyle': '--'}
    {'color': 'b', 'linestyle': '-.'}

RememberTheStyle
================

Helper class for mapping keys -> styles::

   from cycler import RememberTheStyle, cycler

   rts = RememberTheStyle((cycler('c', 'rgb') +
                           cycler('ls', ['-', '--', ':']))

   rts['cat']
   rts['aardvark']
   rts['aardvark']
   rts['dog']

Results in ::

   {'c': 'r', 'ls': '-'}
   {'c': 'g', 'ls': '--'}
   {'c': 'g', 'ls': '--'}
   {'c': 'b', 'ls': ':'}


"""

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import six
from itertools import product, cycle
from six.moves import zip, reduce
from operator import mul, add
from collections import Mapping
import copy

__version__ = '0.9.0.post1'


def _process_keys(left, right):
    """
    Helper function to compose cycler keys

    Parameters
    ----------
    left, right : iterable of dictionaries or None
        The cyclers to be composed
    Returns
    -------
    keys : set
        The keys in the composition of the two cyclers
    """
    l_peek = next(iter(left)) if left is not None else {}
    r_peek = next(iter(right)) if right is not None else {}
    l_key = set(l_peek.keys())
    r_key = set(r_peek.keys())
    if l_key & r_key:
        raise ValueError("Can not compose overlapping cycles")
    return l_key | r_key


class Cycler(object):
    """
    Composable cycles

    This class has compositions methods:

    ``+``
      for 'inner' products (zip)

    ``+=``
      in-place ``+``

    ``*``
      for outer products (itertools.product) and integer multiplication

    ``*=``
      in-place ``*``

    and supports basic slicing via ``[]``

    Calling a `Cycler` instance returns an infinite repeating cycle.

    Parameters
    ----------
    left : Cycler or None
        The 'left' cycler

    right : Cycler or None
        The 'right' cycler

    op : func or None
        Function which composes the 'left' and 'right' cyclers.

    """
    def __call__(self):
        """Infinitely loop through contents of Cycler
        """
        return cycle(self)

    def __init__(self, left, right=None, op=None):
        """Semi-private init

        Do not use this directly, use `cycler` function instead.
        """
        if isinstance(left, Cycler):
            self._left = Cycler(left._left, left._right, left._op)
        elif left is not None:
            # Need to copy the dictionary or else that will be a residual
            # mutable that could lead to strange errors
            self._left = [copy.copy(v) for v in left]
        else:
            self._left = None

        if isinstance(right, Cycler):
            self._right = Cycler(right._left, right._right, right._op)
        elif right is not None:
            # Need to copy the dictionary or else that will be a residual
            # mutable that could lead to strange errors
            self._right = [copy.copy(v) for v in right]
        else:
            self._right = None

        self._keys = _process_keys(self._left, self._right)
        self._op = op

    @property
    def keys(self):
        """
        The keys this Cycler knows about
        """
        return set(self._keys)

    def change_key(self, old, new):
        """
        Change a key in this cycler to a new name.
        Modification is performed in-place.

        Does nothing if the old key is the same as the new key.
        Raises a ValueError if the new key is already a key.
        Raises a KeyError if the old key isn't a key.

        """
        if old == new:
            return
        if new in self._keys:
            raise ValueError("Can't replace %s with %s, %s is already a key" %
                             (old, new, new))
        if old not in self._keys:
            raise KeyError("Can't replace %s with %s, %s is not a key" %
                           (old, new, old))

        self._keys.remove(old)
        self._keys.add(new)

        if self._right is not None and old in self._right.keys:
            self._right.change_key(old, new)

        # self._left should always be non-None
        # if self._keys is non-empty.
        elif isinstance(self._left, Cycler):
            self._left.change_key(old, new)
        else:
            # It should be completely safe at this point to
            # assume that the old key can be found in each
            # iteration.
            self._left = [{new: entry[old]} for entry in self._left]

    def _compose(self):
        """
        Compose the 'left' and 'right' components of this cycle
        with the proper operation (zip or product as of now)
        """
        for a, b in self._op(self._left, self._right):
            out = dict()
            out.update(a)
            out.update(b)
            yield out

    @classmethod
    def _from_iter(cls, label, itr):
        """
        Class method to create 'base' Cycler objects
        that do not have a 'right' or 'op' and for which
        the 'left' object is not another Cycler.

        Parameters
        ----------
        label : str
            The property key.

        itr : iterable
            Finite length iterable of the property values.

        Returns
        -------
        cycler : Cycler
            New 'base' `Cycler`
        """
        ret = cls(None)
        ret._left = list({label: v} for v in itr)
        ret._keys = set([label])
        return ret

    def __getitem__(self, key):
        # TODO : maybe add numpy style fancy slicing
        if isinstance(key, slice):
            trans = self._transpose()
            return reduce(add, (_cycler(k, v[key])
                                for k, v in six.iteritems(trans)))
        else:
            raise ValueError("Can only use slices with Cycler.__getitem__")

    def __iter__(self):
        if self._right is None:
            return iter(dict(l) for l in self._left)

        return self._compose()

    def __add__(self, other):
        """
        Pair-wise combine two equal length cycles (zip)

        Parameters
        ----------
        other : Cycler
           The second Cycler
        """
        if len(self) != len(other):
            raise ValueError("Can only add equal length cycles, "
                             "not {0} and {1}".format(len(self), len(other)))
        return Cycler(self, other, zip)

    def __mul__(self, other):
        """
        Outer product of two cycles (`itertools.product`) or integer
        multiplication.

        Parameters
        ----------
        other : Cycler or int
           The second Cycler or integer
        """
        if isinstance(other, Cycler):
            return Cycler(self, other, product)
        elif isinstance(other, int):
            trans = self._transpose()
            return reduce(add, (_cycler(k, v*other)
                                for k, v in six.iteritems(trans)))
        else:
            return NotImplemented

    def __rmul__(self, other):
        return self * other

    def __len__(self):
        op_dict = {zip: min, product: mul}
        if self._right is None:
            return len(self._left)
        l_len = len(self._left)
        r_len = len(self._right)
        return op_dict[self._op](l_len, r_len)

    def __iadd__(self, other):
        """
        In-place pair-wise combine two equal length cycles (zip)

        Parameters
        ----------
        other : Cycler
           The second Cycler
        """
        if not isinstance(other, Cycler):
            raise TypeError("Cannot += with a non-Cycler object")
        # True shallow copy of self is fine since this is in-place
        old_self = copy.copy(self)
        self._keys = _process_keys(old_self, other)
        self._left = old_self
        self._op = zip
        self._right = Cycler(other._left, other._right, other._op)
        return self

    def __imul__(self, other):
        """
        In-place outer product of two cycles (`itertools.product`)

        Parameters
        ----------
        other : Cycler
           The second Cycler
        """
        if not isinstance(other, Cycler):
            raise TypeError("Cannot *= with a non-Cycler object")
        # True shallow copy of self is fine since this is in-place
        old_self = copy.copy(self)
        self._keys = _process_keys(old_self, other)
        self._left = old_self
        self._op = product
        self._right = Cycler(other._left, other._right, other._op)
        return self

    def __eq__(self, other):
        """
        Check equality
        """
        if len(self) != len(other):
            return False
        if self.keys ^ other.keys:
            return False

        return all(a == b for a, b in zip(self, other))

    def __repr__(self):
        op_map = {zip: '+', product: '*'}
        if self._right is None:
            lab = self.keys.pop()
            itr = list(v[lab] for v in self)
            return "cycler({lab!r}, {itr!r})".format(lab=lab, itr=itr)
        else:
            op = op_map.get(self._op, '?')
            msg = "({left!r} {op} {right!r})"
            return msg.format(left=self._left, op=op, right=self._right)

    def _repr_html_(self):
        # an table showing the value of each key through a full cycle
        output = "<table>"
        sorted_keys = sorted(self.keys)
        for key in sorted_keys:
            output += "<th>{key!r}</th>".format(key=key)
        for d in iter(self):
            output += "<tr>"
            for k in sorted_keys:
                output += "<td>{val!r}</td>".format(val=d[k])
            output += "</tr>"
        output += "</table>"
        return output

    def _transpose(self):
        """
        Internal helper function which iterates through the
        styles and returns a dict of lists instead of a list of
        dicts.  This is needed for multiplying by integers and
        for __getitem__

        Returns
        -------
        trans : dict
            dict of lists for the styles
        """

        # TODO : sort out if this is a bottle neck, if there is a better way
        # and if we care.

        keys = self.keys
        # change this to dict comprehension when drop 2.6
        out = dict((k,  list()) for k in keys)

        for d in self:
            for k in keys:
                out[k].append(d[k])
        return out

    def simplify(self):
        """Simplify the Cycler

        Returned as a composition using only sums (no multiplications)

        Returns
        -------
        simple : Cycler
            An equivalent cycler using only summation"""
        # TODO: sort out if it is worth the effort to make sure this is
        # balanced.  Currently it is is
        # (((a + b) + c) + d) vs
        # ((a + b) + (c + d))
        # I would believe that there is some performance implications

        trans = self._transpose()
        return reduce(add, (_cycler(k, v) for k, v in six.iteritems(trans)))


def cycler(*args, **kwargs):
    """Public constructor function for Cycler objects

    Create a new `Cycler` object from a single positional argument,
    a pair of positional arguments, or the combination of keyword arguments.

    cycler(arg)
    cycler(label1=itr1[, label2=iter2[, ...]])
    cycler(label, itr)

    Form 1 simply copies a given `Cycler` object.

    Form 2 composes a `Cycler` as an inner product of the
    pairs of keyword arguments. In other words, all of the
    iterables are cycled simultaneously, as if through zip().

    Form 3 creates a `Cycler` from a label and an iterable.
    This is useful for when the label cannot be a keyword argument
    (e.g., an integer or a name that has a space in it).

    Parameters
    ----------
    arg : Cycler
        Copy constructor for Cycler (does a shallow copy of iterables).

    label : name
        The property key. In the 2-arg form of the function,
        the label can be any hashable object. In the keyword argument
        form of the function, it must be a valid python identifier.

    itr : iterable
        Finite length iterable of the property values.
        Can be a single-property `Cycler` that would
        be like a key change, but as a shallow copy.

    Returns
    -------
    cycler : Cycler
        New `Cycler` for the given property

    """
    if args and kwargs:
        raise TypeError("cyl() can only accept positional OR keyword "
                        "arguments -- not both.")

    if len(args) == 1:
        if not isinstance(args[0], Cycler):
            raise TypeError("If only one positional argument given, it must "
                            " be a Cycler instance.")
        return Cycler(args[0])
    elif len(args) == 2:
        return _cycler(*args)
    elif len(args) > 2:
        raise TypeError("Only a single Cycler can be accepted as the lone "
                        "positional argument. Use keyword arguments instead.")

    if kwargs:
        return reduce(add, (_cycler(k, v) for k, v in six.iteritems(kwargs)))

    raise TypeError("Must have at least a positional OR keyword arguments")


def _cycler(label, itr):
    """
    Create a new `Cycler` object from a property name and
    iterable of values.

    Parameters
    ----------
    label : hashable
        The property key.

    itr : iterable
        Finite length iterable of the property values.

    Returns
    -------
    cycler : Cycler
        New `Cycler` for the given property
    """
    if isinstance(itr, Cycler):
        keys = itr.keys
        if len(keys) != 1:
            msg = "Can not create Cycler from a multi-property Cycler"
            raise ValueError(msg)

        lab = keys.pop()
        # Doesn't need to be a new list because
        # _from_iter() will be creating that new list anyway.
        itr = (v[lab] for v in itr)

    return Cycler._from_iter(label, itr)


class RememberTheStyle(Mapping):
    """Persistent style by key

    This is a class for easily managing consistent style across for
    classes of data across many plots.

    The first time you use `rts[key]` it gets the next style
    dictionary from it's internal `Cycler`.  Subsequent calls to
    `rts[key]` will return an identical dictionary.

    Parameters
    ----------
    sty_cylr : Cycler
        Anything that yields dictionaries when iterated over

    loop : bool, optional
        Defaults to `False`.  If True, loop over the input `sty_cylr`
        when more keys are requested that the length of `sty_cyclr`.
        If `False` will raise `RuntimeError` if available styles are
        exhausted.


    cache : dict-like or None, optional
        MuttableMapping instance to use as the internal key -> style cache.

        The purpose of this is provide a pre-populated cache or
        to share a cache between multiple `RememberTheStyle` instances.

        Use this at your own risk.
    """
    def __init__(self, sty_cylr, loop=False, cache=None):
        if cache is None:
            cache = {}

        self._cache = cache
        # make a shallow copy of the style cycle just to be safe
        sty_cylr = Cycler(sty_cylr)
        if loop:
            self._style_cycler = sty_cylr()
        else:
            self._style_cycler = iter(sty_cylr)

    @property
    def style_cache(self):
        """Access to style cache instance

        This is a reference to the underlying object, mutate
        this with caution.
        """
        return self._cache

    def __getitem__(self, key):
        try:
            return dict(self.style_cache[key])
        except KeyError:
            # pass instead of handling in here to make stack trace
            # nicer
            pass
        try:
            new_style = next(self._style_cycler)
        except StopIteration:
            raise RuntimeError("Asked for more style than we have")

        self.style_cache[key] = dict(new_style)
        return dict(new_style)

    def __iter__(self):
        return iter(self.style_cache)

    def __len__(self):
        return len(self.style_cache)

    def named(self, val):
        return self[val]
