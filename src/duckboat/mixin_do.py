from pathlib import Path

from .ddb import query

try:
    from string.templatelib import Template as _Template  # pragma: no cover
    from ._tstrings import _process_template  # pragma: no cover
except ImportError:  # pragma: no cover
    _Template = type(None)  # pragma: no cover
    _process_template = None  # pragma: no cover

_PREV = '_'


class _Rename:
    __slots__ = ('name',)

    def __init__(self, name):
        self.name = name


def rename(name):
    return _Rename(name)


def _is_file(s):
    if len(s) > 255:
        return False
    return Path(s).is_file()


def _read_file(s):
    if isinstance(s, Path):
        return s.read_text()

    if isinstance(s, str) and _is_file(s):
        return Path(s).read_text()

    return s


def _wrap_tables(d):
    from .table import Table
    return {k: Table(v) for k, v in d.items()}


def _to_context(A):
    from .table import Table

    if isinstance(A, dict):
        return _wrap_tables(A)
    return {_PREV: Table(A)}


def _do_one(ctx, x):
    from .table import Table

    if not isinstance(ctx, dict):
        ctx = _to_context(ctx)

    if isinstance(x, dict):
        return {**ctx, **_wrap_tables(x)}

    if isinstance(x, list):
        for item in x:
            ctx = _do_one(ctx, item)
        return ctx

    if isinstance(x, _Rename):
        if _PREV not in ctx:
            raise ValueError('rename: no implicit table to rename')
        tbl = ctx.pop(_PREV)
        return {**ctx, x.name: tbl}

    if isinstance(x, _Template):  # pragma: no cover
        sql, tables = _process_template(x)  # pragma: no cover
        if tables:  # pragma: no cover
            ctx = _do_one(ctx, tables)  # pragma: no cover
        return _do_one(ctx, sql)  # pragma: no cover

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

        # TODO: if DuckDB ever exposes a way to detect whether SQL already
        # has a FROM clause (e.g., parse AST), we could skip prepending
        # 'from _' when the user writes a complete query like
        # 'select * from _ as a join _ as b ...'. For now, users write
        # 'as a join _ as b ...' and we prepend 'from _' unconditionally.
        named = {k: v.rel for k, v in ctx.items()}
        if _PREV in ctx:
            sql = 'from _ ' + s
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
    if isinstance(A, _Template):  # pragma: no cover
        ctx = _do_one({}, A)  # pragma: no cover
    else:
        ctx = _to_context(A)
    for x in xs:
        ctx = _do_one(ctx, x)
    if isinstance(ctx, dict) and _PREV in ctx:
        return ctx[_PREV]
    return ctx


class DoMixin:
    def do(self, *others):
        return _do(self, *others)
