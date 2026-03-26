from pathlib import Path

from ._query import __duckboat_query__ as query
from duckdb import DuckDBPyRelation


def form_relation(x) -> DuckDBPyRelation:
    if hasattr(x, '__arrow_c_stream__'):
        return query('select * from x', x=x)
    if isinstance(x, (str, Path)):
        try:
            return query(f'select * from "{x}"')
        except Exception as e:
            raise type(e)(f'Could not read {x!r}: {e}') from e
    raise TypeError(
        f'Expected a tabular object implementing __arrow_c_stream__ '
        f'or a filename string — got {type(x).__name__}'
    )
