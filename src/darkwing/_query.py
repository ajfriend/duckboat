import inspect as __inspect__
from . import _darkwing_con as __con__

def __darkwing_query__(__s__, **kwargs):
    """
    Runs a query on our DuckDB database and returns the DuckDB Relation.

    TOOD: should we even expose this to the user?
    """
    __inspect__.currentframe().f_locals.update(kwargs)
    return __con__.query(__s__)
