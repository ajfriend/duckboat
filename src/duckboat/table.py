from .ddb import form_relation
from .mixin_do import DoMixin
from .mixin_table import TableMixin

from duckdb import DuckDBPyRelation


class Table(TableMixin, DoMixin):
    """
    The table name is always included implicitly when applying a SQL snippet.
    """
    # TODO: we might have to hide even this from the prying eyes of Positron.
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
            return '<Table(..., _hide=True)>'
        else:
            return repr(self.rel)

    def hide(self):
        return Table(self, _hide=True)

    def show(self):
        return Table(self, _hide=False)

    def sql(self, s: str):
        """
        Run a SQL snippet via DuckDB, prepended with `from <table_name>`,
        where `<table_name>` will be a unique and random name to avoid collisions.
        """
        name = TableMixin.random_table_name()
        rel = self.rel.query(name, f'from {name} ' + s)
        return Table(rel)

    def rowcols(self):
        if self._hide:
            s = '<Table(..., _hide=True)>'
        else:
            n = self.do('select count(*)', int)
            s = f'{n} x {self.columns}'

        return s
