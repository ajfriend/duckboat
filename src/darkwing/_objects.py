import random
import string

from . import query, _sfo_con
from ._get_if_file import _get_if_file


class Database:
    """
    TODO: can we make it so we can use .dot access to tables?
    TODO: maybe a .materialize to get a copy to memory? have a databoose be nothing more than a fancy dictionary. convert to relations late. materialize does the conversion, and gives you a new databoose with dfs or arrow or pl
    TODO: materialize also gives users a more concrete way to interact with the databoose. pin fix bind hold. i like hold
    """
    def __init__(self, **tables):
        self.tables = {**tables}
        self._rel_cache = {}  # TODO: oooh! maybe move the relation caching to the relation object

    def _do_cache(self):
        if not self._rel_cache:
            self._rel_cache = {
                k: load(v)._rel  # TODO: code smell on this ._rel thing
                for k,v in self.tables.items()
            }

    def sql(self, s):
        s = _get_if_file(s)
        self._do_cache()
        rel = query(s, **self._rel_cache)
        return Relation(rel)


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


class Relation:
    """
    TOOD: get rid of load and just use this constructor?
    """
    def __init__(self, rel=None):
        self._rel = rel

    def __repr__(self):
        return repr(self._rel)

    def sql(self, s):
        s = s.strip()
        if s.startswith('as '):
            s = s[3:]
            d = {s: self}
            return Database(**d)

        name = '_tlb_' + ''.join(random.choices(string.ascii_lowercase, k=10))
        return Relation(
            rel = self._rel.query(name, f'from {name} ' + s)
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
        return self._rel.df()

    def arrow(self):
        return self._rel.arrow()

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


def _load_string(s):    
    rel = _sfo_con.sql(f'select * from "{s}"')
    return Relation(rel)

def _load_other(x):
    rel = _sfo_con.sql('select * from x')
    return Relation(rel)

def _load(x) -> Relation:
    """
    inputs: string of filename, actual file, string of remote file, dataframe, dictionary, polars, pyarrow, filename of database
    """
    # intention: take a pandas, polars, or string/URL and convert it to something that we can register
    # also convert relations from other connections to something we can register.
    # if isinstance(df, Relation):
    #     df = df.arrow()
    if isinstance(x, str):
        return _load_string(x)
    elif isinstance(x, Relation):
        return x
    else:
        return _load_other(x)

# TODO: do we need a separate `load`? or is this just a `Relation` constructor?
class Load:
    def __call__(self, x):
        return _load(x)
    
    def __rrshift__(self, other):
        return _load(other)

load = Load()

