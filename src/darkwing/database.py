from . import query
from .table import Table
from .mixin_do import DoMixin
from .mixin_database import DatabaseMixin


class Database(DatabaseMixin, DoMixin):
    """
    Table names must be included **explicitly** when applying a SQL snippet.
    """
    tables: dict[str, Table]

    def __init__(self, _hide=False, **tables):
        self.tables = {
            k: Table(v, _hide=_hide)
            for k,v in tables.items()
        }

    def sql(self, s: str):
        tables = {k: v.rel for k,v in self.tables.items()}
        rel = query(s, **tables)
        return Table(rel)

    def hide(self):
        return Database(**self, _hide=True)

    def show(self):
        return Database(**self, _hide=False)

    def keys(self):
        return self.tables.keys()

    def __getitem__(self, key):
        return self.tables[key]
