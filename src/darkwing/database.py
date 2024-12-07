from . import query
from .table import Table
from .doer import do

class DatabaseMixin:
    def __repr__(self):
        tables = self._yield_table_lines()
        tables = [
            f'\n    {t}'
            for t in tables
        ]
        tables = ''.join(tables)
        tables = tables or ' None'

        out = 'Database:' + tables

        return out
    
    def _yield_table_lines(self):
        for name, tbl in self.tables.items():
            if isinstance(tbl.raw, str):
                yield f"{name}: '{tbl.raw}'"
            else:
                n = self.do(f'select count() from {name}', int)
                yield f'{name}: {n} x {tbl.columns}'

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

    def hold(self, kind='arrow'):
        """
        Materialize the Database as a collection of PyArrow Tables or Pandas DataFrames
        """
        return Database(**{
            name: self.do(f'from {name}', kind)
            for name in self.tables
        })
