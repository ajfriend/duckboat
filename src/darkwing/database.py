from . import query
from .table import Table
from .mixin_do import DoMixin
from .mixin_database import DatabaseMixin

class Database(DatabaseMixin, DoMixin):
    """
    Table names must be included **explicitly** when applying a SQL snippet.
    """
    _hide: bool
    tables: dict[str, Table]

    def __init__(self, _hide=False, **tables):
        self._hide = _hide
        self.tables = {
            k: Table(v)
            for k,v in tables.items()
        }

    def sql(self, s: str):
        tables = {k: v.rel for k,v in self.tables.items()}
        rel = query(s, **tables)
        return Table(rel)

    def hide(self):
        return Database(_hide=True, **self)

    def show(self):
        return Database(_hide=False, **self)

    def keys(self):
        return self.tables.keys()

    def __getitem__(self, key):
        return self.tables[key]
