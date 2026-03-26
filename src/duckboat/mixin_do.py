from pathlib import Path

from .ddb import query

_PREV = '_'


def _read_file(s):
    if isinstance(s, Path):
        return s.read_text()

    if isinstance(s, str):
        try:
            if Path(s).is_file():
                with open(s) as f:
                    return f.read()
        except OSError:
            pass

    return s


def _to_context(A):
    from .table import Table

    if isinstance(A, dict):
        return {k: Table(v) for k, v in A.items()}
    return {_PREV: Table(A)}


def _do_one(ctx, x):
    from .table import Table

    if not isinstance(ctx, dict):
        ctx = _to_context(ctx)

    if isinstance(x, dict):
        named = {k: Table(v) for k, v in x.items()}
        return {**ctx, **named}

    if isinstance(x, list):
        for item in x:
            ctx = _do_one(ctx, item)
        return ctx

    tbl = ctx.get(_PREV)

    if isinstance(x, (str, Path)):
        x = _read_file(x)
        s = x.strip()

        if s in ('arrow', 'pandas'):
            return tbl.hold(kind=s)
        if s == 'hide':
            return {_PREV: tbl.hide()}
        if s == 'show':
            return {_PREV: tbl.show()}

        named = {k: v.rel for k, v in ctx.items()}
        if _PREV in ctx:
            sql = f'from _ ' + s
        else:
            sql = s
        result = Table(query(sql, **named))
        return {_PREV: result}

    if tbl is not None:
        if x in {int, str, bool, float}:
            return x(tbl.asitem())
        if x is list:
            return tbl.aslist()
        if x is dict:
            return tbl.asdict()

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
