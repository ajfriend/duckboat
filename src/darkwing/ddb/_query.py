import inspect as __inspect__
from ._con import __darkwing_con__

def __darkwing_query__(__s__, **kwargs):
    """
    Runs a query on our DuckDB database and returns the DuckDB Relation.

    We mangle the names in this file because `__darkwing_con__.query()` will,
    by default, look for any names in the Python namespace.
    We want to isolate it from finding any symbols unexpectedly, so
    we're forced to hide this query away in its own file.

    The intention is that the only Python symbols that are visible
    to the DuckDB query should be those given in `kwargs`.

    Ideally, DuckDB would provide this function instead of
    us hacking it together like we do here.
    """
    __inspect__.currentframe().f_locals.update(kwargs)
    return __darkwing_con__.query(__s__)
