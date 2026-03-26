import inspect as __inspect__
from ._con import __duckboat_con__


def __duckboat_query__(__s__, **kwargs):
    """
    Runs a query on our DuckDB database and returns the DuckDB Relation.

    We mangle the names in this file because `__duckboat_con__.query()` will,
    by default, look for any names in the Python namespace.
    We want to isolate it from finding any symbols unexpectedly, so
    we're forced to hide this query away in its own file.

    The intention is that the only Python symbols that are visible
    to the DuckDB query should be those given in `kwargs`.

    Ideally, DuckDB would provide a way to pass named tables
    directly to a query (e.g., con.query(sql, tables={'a': rel}))
    instead of relying on replacement scans that inspect the
    caller's frame. The f_locals.update() hack is CPython-specific
    and fragile under PEP 667 (Python 3.13+).
    See: https://github.com/duckdb/duckdb/discussions/14041
    """
    __inspect__.currentframe().f_locals.update(kwargs)
    return __duckboat_con__.query(__s__)
