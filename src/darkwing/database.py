from . import query
from .table import Table
from .mixin_do import DoMixin
from .mixin_database import DatabaseMixin

class Database(DatabaseMixin, DoMixin):
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
