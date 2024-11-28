from ._query import __darkwing_query__ as query
from duckdb import DuckDBPyRelation

def form_relation(x) -> DuckDBPyRelation:
    """
    inputs: string of filename, actual file, string of remote file, dataframe, dictionary, polars, pyarrow, filename of database
    """
    # intention: take a pandas, polars, or string/URL and convert it to something that we can register
    # also convert relations from other connections to something we can register.
    # if isinstance(df, Relation):
    #     df = df.arrow()
    if isinstance(x, str):
        return query(f'select * from "{x}"')
    else:
        return query('select * from x', x=x)