import re
import keyword
from itertools import chain
import builtins

from collections import OrderedDict


def isidentifier(s, rx=re.compile(r'[a-zA-Z_]\w*')):
    return rx.match(s) is not None and ' ' not in s


class Dict(OrderedDict):
    def __init__(self, items):
        super(Dict, self).__init__(items)

    def __repr__(self):
        return '%s!%s' % (List(*self.keys()), List(*self.values()))


class Atom(object):
    def __init__(self, s):
        assert isinstance(s, (basestring, Atom, String))
        self.s = getattr(s, 's', s)

    def __hash__(self):
        return hash(str(self))

    def __eq__(self, other):
        return type(self) == type(other) and self.s == other.s

    def __repr__(self):
        return self.s


class String(Atom):
    def __init__(self, s):
        super(String, self).__init__(str(s))

    def __repr__(self):
        return '"%s"' % self.s


class Symbol(Atom):
    def __init__(self, *args):
        """
        Examples
        --------
        >>> from kdbpy import q
        >>> t = q.Symbol('t', 's', 'a')
        >>> t
        `t.s.a
        """
        super(Symbol, self).__init__(args[0])
        self.fields = args[1:]
        self.str = '.'.join(chain([self.s], self.fields))

    def __getitem__(self, name):
        """
        Examples
        --------
        >>> from kdbpy import q
        >>> t = q.Symbol('t')
        >>> t['s']['a']
        `t.s.a
        """
        return type(self)(*list(chain([self.s], self.fields, [name])))

    def __repr__(self):
        joined = self.str
        if not isidentifier(joined) and not keyword.iskeyword(joined):
            return '`$"%s"' % joined
        return '`' + joined


def binop(op):
    return lambda x, y: List(op, x, y)


def unop(op):
    return lambda x: List(op, x)


eq = binop('=')
ne = binop('<>')
lt = binop('<')
gt = binop('>')
le = binop('<=')
ge = binop('>=')

add = binop('+')
sub = binop('-')
mul = binop('*')
div = binop('%')
pow = binop('xexp')
mod = binop('mod')

take = binop('#')
partake = binop('.Q.ind')
and_ = binop('&')
or_ = binop('|')

neg = unop('-:')
null = unop('^:')
not_ = unop('~:')
floor = unop('_:')
ceil = unop('-_-:')
count = unop('#:')
til = unop('til')
distinct = unop('?:')


unary_ops = {'-': neg,
             '~': not_,
             'floor': floor,
             'ceil': ceil,
             'sum': unop('sum'),
             'mean': unop('avg'),
             'std': unop('dev'),
             'var': unop('var'),
             'min': unop('min'),
             'max': unop('max'),
             'count': count,
             'nelements': count}


def symlist(*args):
    return List(*list(map(Symbol, args)))


def slice(obj, *keys):
    return List(obj, '::', symlist(*keys))


def sort(x, key, ascending):
    sort_func = Atom('xasc' if ascending else 'xdesc')
    return List(sort_func, symlist(key), x)


def try_(f, x, onfail):
    """q's horrible version of try except, where any error is caught"""
    return List('@', f, x, onfail)


def cast(typ):
    return lambda x: List('$', symlist(typ), x)


long = cast('long')
int = cast('int')
float = cast('float')


def select(child, constraints=None, by=None, aggregates=None):
    if constraints is None:
        constraints = List()
    if by is None:
        by = Bool()
    if aggregates is None:
        aggregates = List()
    return List('?', child, constraints, by, aggregates)


class List(object):
    def __init__(self, *items):
        self.items = items

    def __repr__(self):
        if len(self) == 1:
            return '(,:[%s])' % self[0]
        return '(%s)' % '; '.join(map(str, self.items))

    def __getitem__(self, key):
        result = self.items[key]
        if isinstance(key, builtins.slice):
            return List(*result)
        return result

    def __len__(self):
        return len(self.items)

    def __iter__(self):
        return iter(self.items)

    def __eq__(self, other):
        return type(self) == type(other) and self.items == other.items

    def __add__(self, other):
        return List(*list(chain(self.items, other.items)))

    def append(self, other):
        return self + type(self)(other)


class Bool(object):
    def __init__(self, value=False):
        self.value = bool(value)

    def __repr__(self):
        return '%ib' % self.value

    def __eq__(self, other):
        return type(self) == type(other) and self.value == other.value

    def __ne__(self, other):
        return not (self == other)


Expr = Dict, Atom, List, Bool
