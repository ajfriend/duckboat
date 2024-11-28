import random
import string

from . import query
from ._get_if_file import _get_if_file

from duckdb import DuckDBPyRelation
from .duckdb_part import form_relation

class DatabaseHelper:
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
                columns = self.do(f'select column_name from (describe from {name})', list)
                yield f'{name}: {n} x {columns}'

class Database(DatabaseHelper):
    """
    Table names must be included **explicitly** when applying a SQL snippet.
    """
    def __init__(self, **tables):
        self.tables = {
            k: Table(v)
            for k,v in tables.items()
        }

    def sql(self, s: str):
        s = _get_if_file(s)
        tables = {k: v.rel for k,v in self.tables.items()}
        rel = query(s, **tables)
        return Table(rel)

    def __getitem__(self, key):
        return self.tables[key].raw

    def _do_one(self, other: 'Any'):
        if other in {'arrow', 'pandas'}:
            return self.hold(kind=other)
        if callable(other):
            return other(self)
        else:
            return self.sql(other)

    def do(self, *others):
        cur = self
        for other in others:
            cur = cur._do_one(other)
        return cur

    def hold(self, kind='arrow'):
        """
        Materialize the Database as a collection of PyArrow Tables or Pandas DataFrames
        """
        return Database(**{
            name: self.do(f'from {name}', kind)
            for name in self.tables
        })


class TableTransforms:
    def asitem(self):
        """Transform a df with one row and one column to single element"""
        # _insist_single_row(df)
        # _insist_single_col(df)
        return self.aslist()[0]

    def asdict(self):
        """Transform a df with one row to a dict
        """
        # _insist_single_row(df)
        df = self.df()
        return dict(df.iloc[0])

    def hold(self, kind='arrow'):
        """
        Materialize the Table as a PyArrow Table or Pandas DataFrame.
        """
        if kind == 'arrow':
            return self.arrow()
        if kind == 'pandas':
            return self.df()

    def df(self):
        return self.rel.df()

    def arrow(self):
        return self.rel.arrow()

    def aslist(self):
        """Transform a df with one row or one column to a list"""
        df = self.df()
        if len(df.columns) == 1:
            col = df.columns[0]
            out = list(df[col])
        elif len(df) == 1:
            out = list(df.loc[0])
        else:
            raise ValueError(f'DataFrame should have a single row or column, but has shape f{df.shape}')

        return out

class Table(TableTransforms):
    """
    The table name is always included implicitly when applying a SQL snippet.
    """
    def __init__(self, other):
        if isinstance(other, Table):
            self.raw = other.raw
            self.rel = other.rel
        else:
            self.raw = other
            self.rel = form_relation(other)

    def __repr__(self):
        return repr(self.rel)

    def sql(self, s: str):
        """
        Run a SQL snippet via DuckDB, prepended with `from <table_name>`,
        where `<table_name>` will be a unique and random name to avoid collisions.
        """
        name = '_tlb_' + ''.join(random.choices(string.ascii_lowercase, k=10))
        rel = self.rel.query(name, f'from {name} ' + s)
        return Table(rel)

    def _do_one(self, other: 'Any'):
        if isinstance(other, str):
            s = other.strip()
            if s.startswith('as '):
                name = s[3:].strip()
                return self.alias(name)

        if isinstance(other, list):
            return self.do(*other)

        if other in {'arrow', 'pandas'}:
            return self.hold(kind=other)
        if other in {int, str, bool, float}:
            return self.asitem()
        if other is list:
            return self.aslist()
        if other is dict:
            return self.asdict()
        if callable(other):
            return other(self)
        
        return self.sql(other)

    # TODO: do and do_one is just `eval`. clean it up!
    # TODO: should `eval` just be a separate? we may hit a recursion limit... cool!
    # TODO: we can maybe combine the `eval` for both table and database into a single function
    def do(self, *others):
        cur = self
        for other in others:
            cur = cur._do_one(other)
        return cur

    def alias(self, name):
        return Database(**{name: self})

