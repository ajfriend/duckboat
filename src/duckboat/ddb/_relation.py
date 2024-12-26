from ._query import __duckboat_query__ as query
from duckdb import DuckDBPyRelation


def form_relation(x) -> DuckDBPyRelation:
    """
    inputs: string of filename, actual file, string of remote file, dataframe,
    dictionary, polars, pyarrow, filename of database
    """
    # if isinstance(df, Relation):
    #     df = df.arrow()
    if isinstance(x, str):
        return query(f'select * from "{x}"')
    else:
        return query('select * from x', x=x)
