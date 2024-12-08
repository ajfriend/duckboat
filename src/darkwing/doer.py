from pathlib import Path

def _is_file(s: str) -> bool:
    try:
        return Path(s).is_file()
    except (OSError, TypeError):
        # catches `OSError: [Errno 63] File name too long`
        return False

def _get_if_file(s) -> str:
    if isinstance(s, Path):
        s = s.read_text()

    if _is_file(s):
        with open(s) as f:
            s = f.read()

    return s

def do_one(A, x):
    from .table import Table
    from .database import Database

    x = _get_if_file(x)

    if isinstance(A, Table):
        if isinstance(x, str):
            s = x.strip()
            if s.startswith('as '):
                name = s[3:].strip()
                return A.alias(name)

        if isinstance(x, list):
            return A.do(*x)

        if x in {'arrow', 'pandas'}:
            return A.hold(kind=x)
        if x in {int, str, bool, float}:
            return x(A.asitem())
        if x is list:
            return A.aslist()
        if x is dict:
            return A.asdict()
        if callable(x):
            return x(A)
        
        return A.sql(x)

    if isinstance(A, Database):
        if x in {'arrow', 'pandas'}:
            return A.hold(kind=x)
        if callable(x):
            return x(A)

        return A.sql(x)

    raise ValueError(f'Expected to be Table or Database: {A}')

def _do(A, *xs):
    for x in xs:
        A = do_one(A, x)
    return A

class DoMixin:
    def do(self, *others):
        return _do(self, *others)
