from pathlib import Path

from .ddb import query


class _Prev:
    __slots__ = ()
    def __repr__(self):  # pragma: no cover
        return '_Prev'

_PREV = _Prev()


def _is_file(s: str) -> bool:
    try:
        return Path(s).is_file()
    except (OSError, TypeError):
        return False


def _get_if_file(s) -> str:
    if isinstance(s, Path):
        s = s.read_text()

    if _is_file(s):
        with open(s) as f:
            s = f.read()

    return s


def _to_context(A):
    from .table import Table

    if isinstance(A, dict):
        return {k: Table(v) for k, v in A.items()}
    if isinstance(A, Table):
        return {_PREV: A}
    return {_PREV: Table(A)}


def _sql_with_prev(tbl, s, **named):
    from .table import Table

    name = tbl.random_table_name()
    sql = f'from {name} ' + s
    rel = query(sql, **{name: tbl.rel, **named})
    return Table(rel)


def _do_one(ctx, x):
    from .table import Table

    # If ctx is not a dict, wrap it back into one
    if not isinstance(ctx, dict):
        ctx = _to_context(ctx)

    # Dict: merge named tables into context for next step
    if isinstance(x, dict):
        named = {k: Table(v) for k, v in x.items()}
        return {**ctx, **named}

    # List: recursively apply as pipeline fragment
    if isinstance(x, list):
        for item in x:
            ctx = _do_one(ctx, item)
        return ctx

    x = _get_if_file(x)

    tbl = ctx.get(_PREV)

    # String dispatch
    if isinstance(x, str):
        s = x.strip()

        if s in ('arrow', 'pandas'):
            return tbl.hold(kind=s)
        if s == 'hide':
            return {_PREV: tbl.hide()}
        if s == 'show':
            return {_PREV: tbl.show()}

        # SQL execution
        if _PREV in ctx:
            named = {k: v.rel for k, v in ctx.items() if k is not _PREV}
            result = _sql_with_prev(tbl, s, **named)
        else:
            named = {k: v.rel for k, v in ctx.items()}
            result = Table(query(s, **named))
        return {_PREV: result}

    # Type materializers
    if tbl is not None:
        if x in {int, str, bool, float}:
            return x(tbl.asitem())
        if x is list:
            return tbl.aslist()
        if x is dict:
            return tbl.asdict()

    # Callable
    if callable(x):
        result = x(tbl)
        if isinstance(result, Table):
            return {_PREV: result}
        return result

    raise ValueError(f'Unexpected argument in do() chain: {x!r}')


def _do(A, *xs):
    ctx = _to_context(A)
    for x in xs:
        ctx = _do_one(ctx, x)
    if isinstance(ctx, dict) and _PREV in ctx:
        return ctx[_PREV]
    return ctx


class DoMixin:
    def do(self, *others):
        return _do(self, *others)
