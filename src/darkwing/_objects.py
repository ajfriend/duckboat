import random
import string

from . import query, _darkwing_con
from ._get_if_file import _get_if_file

from duckdb import DuckDBPyRelation


class Database:
    """
    The table/relation names must be included **explicitly** when applying a SQL snippet.
    """
    def __init__(self, **tables):
        self.tables = {**tables}
        self._rel_cache = {}  # TODO: oooh! maybe move the relation caching to the relation object

    def _do_cache(self):
        if not self._rel_cache:
            self._rel_cache = {
                k: Table(v).rel  # TODO: code smell on this ._rel thing
                for k,v in self.tables.items()
            }

    def sql(self, s):
        s = _get_if_file(s)
        self._do_cache()
        rel = query(s, **self._rel_cache) # TODO: is this a code smell?
        return Table(rel)

    def __getitem__(self, key):
        return self.tables[key]

    def __myop__(self, other):
        if other in {'arrow', 'pandas'}:
            return self.hold(type=other)
        if callable(other):
            return other(self)
        else:
            return self.sql(other)

    def __or__(self, other):
        return self.__myop__(other)
    def __rshift__(self, other):
        return self.__myop__(other)

    # TODO: how best to hide the majority of the surface-level code here so we can have people focus on the core mechanics?
    #   seems like good hygine. most of this stuff is functional, not object-oriented. make that separation clear
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
            if isinstance(tbl, str):
                yield f"{name}: '{tbl}'"
            else:
                n = self >> f'select count() from {name}' >> int
                columns = self >> f'select column_name from (describe from {name})' >> list
                yield f'{name}: {n} x {columns}'

    def hold(self, type='arrow'):
        # TODO: allow for different materialization types
        return Database(**{
            name: self >> f'from {name}' >> type
            for name in self.tables
        })


class RightShiftMeta(type):
    def __rrshift__(cls, other):
        return cls(other)

class Table(metaclass=RightShiftMeta):
    """
    The table/relation name is always included implicitly when applying a SQL snippet.

    TOOD: get rid of load and just use this constructor?
    """
    def __init__(self, other):
        if isinstance(other, Table):
            self.raw = other.raw
            self.rel = other.rel
        else:
            self.raw = other
            self.rel = _load(other)

    def __repr__(self):
        return repr(self.rel)

    def sql(self, s):
        s = s.strip()
        if s.startswith('as '):
            s = s[3:]
            d = {s: self}
            return Database(**d)

        name = '_tlb_' + ''.join(random.choices(string.ascii_lowercase, k=10))
        return Table(
            self.rel.query(name, f'from {name} ' + s)
        )

    def __myop__(self, other):
        if other == 'arrow':
            return self.arrow()
        if other == 'pandas':
            return self.df()
        if other in {int, str, bool}:
            return self.asitem()
        if other is list:
            return self.aslist()
        if other is dict:
            return self.asdict()
        if callable(other):
            return other(self)
        
        return self.sql(other)

    def __or__(self, other):
        return self.__myop__(other)

    def __rshift__(self, other):
        return self.__myop__(other)

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


def _load_string(s) -> DuckDBPyRelation:
    return _darkwing_con.sql(f'select * from "{s}"') # TODO: this should probably just be the safe query guy

def _load_other(x) -> DuckDBPyRelation:
    return _darkwing_con.sql('select * from x')  # TODO: this should probably just be the safe query guy

def _load(x) -> DuckDBPyRelation:
    """
    inputs: string of filename, actual file, string of remote file, dataframe, dictionary, polars, pyarrow, filename of database
    """
    # intention: take a pandas, polars, or string/URL and convert it to something that we can register
    # also convert relations from other connections to something we can register.
    # if isinstance(df, Relation):
    #     df = df.arrow()
    if isinstance(x, str):
        return _load_string(x)
    else:
        return _load_other(x)
