from . import query
from .table import Table
from .doer import do
from .database_mixin import DatabaseMixin

class Database(DatabaseMixin):
    """
    Table names must be included **explicitly** when applying a SQL snippet.
    """
    def __init__(self, **tables):
        self.tables = {
            k: Table(v)
            for k,v in tables.items()
        }

    def sql(self, s: str):
        tables = {k: v.rel for k,v in self.tables.items()}
        rel = query(s, **tables)
        return Table(rel)

    def __getitem__(self, key):
        return self.tables[key].raw

    def do(self, *others):
        return do(self, *others)
