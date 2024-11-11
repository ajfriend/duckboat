import inspect as __inspect__
from . import _sfo_con as __con__

def __sfo_query__(__s__, **kwargs):
    __inspect__.currentframe().f_locals.update(kwargs)
    return __con__.query(__s__)
