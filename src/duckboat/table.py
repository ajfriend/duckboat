from .ddb import form_relation
from .mixin_do import DoMixin
from .mixin_table import TableMixin

from duckdb import DuckDBPyRelation

_HIDDEN_REPR = '<Table(..., _hide=True)>'


class Table(TableMixin, DoMixin):
    rel: DuckDBPyRelation
    _hide: bool

    def __init__(self, other, _hide=False):
        self._hide = _hide

        if isinstance(other, Table):
            self.rel = other.rel
        elif isinstance(other, DuckDBPyRelation):
            self.rel = other
        else:
            self.rel = form_relation(other)

    def __repr__(self):
        if self._hide:
            return _HIDDEN_REPR
        return repr(self.rel)

    def hide(self):
        return Table(self, _hide=True)

    def show(self):
        return Table(self, _hide=False)

    def rowcols(self):
        if self._hide:
            return _HIDDEN_REPR
        n = self.do('select count(*)', int)
        return f'{n} x {self.columns}'
