import random
import string

from . import query, _sfo_con
from . import util as u



class Databoose:
    """
    TODO: can we make it so we can use .dot access to tables?
    TODO: maybe a .materialize to get a copy to memory? have a databoose be nothing more than a fancy dictionary. convert to relations late. materialize does the conversion, and gives you a new databoose with dfs or arrow or pl
    TODO: materialize also gives users a more concrete way to interact with the databoose. pin fix bind hold. i like hold
    """
    def __init__(self, **tables):
        self.tables = {
            name: load(t)
            for name, t in tables.items()
        }

    def sql(self, s):
        s = u._get_if_file(s)

        tables = {k: v._rel for k,v in self.tables.items()}
        rel = query(s, **tables)
        return Relation(rel)


    def __myop__(self, other):
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

        out = 'Databoose:' + tables

        return out
    
    def _yield_table_lines(self):
        for name, tbl in self.tables.items():
            n = tbl.sql('select count()').asitem()
            tbl = tbl.df()  # TODO: probably much faster if we just get the columns of the relation rather than fully materialize
            columns = list(tbl.columns)
            yield f'{name}: {n} x {columns}'


class Relation:
    """
    TOOD: allow you to do `>> pd.DataFrame` or `>> list` or `>> dict` or `>> 'dataframe'`. can replace `aslist()`, `asdict()`
    """
    def __init__(self, rel=None):
        self._rel = rel

    def __repr__(self):
        return repr(self._rel)

    def sql(self, s):
        s = s.strip()
        if s.startswith('as '):
            # TODO: there might be a way to do this that avoids the materialization and returns a new kind of relation
            # TODONE? i think the new design does it
            s = s[3:]
            d = {s: self}
            return Databoose(**d)

        name = '_tlb_' + ''.join(random.choices(string.ascii_lowercase, k=10))
        return Relation(
            rel = self._rel.query(name, f'from {name} ' + s)
        )

    def __myop__(self, other):
        if callable(other):
            return other(self)
        else:
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

        out = self.aslist()[0]

        return out


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

class Load:
    def __call__(self, x):
        return _load(x)
    
    def __rrshift__(self, other):
        return _load(other)

load = Load()

