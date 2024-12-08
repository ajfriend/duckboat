import random
import string

from .ddb import form_relation
from .do_mixin import DoMixin
from .table_mixin import TableMixin

class Table(TableMixin, DoMixin):
    """
    The table name is always included implicitly when applying a SQL snippet.
    """
    def __init__(self, other):
        if isinstance(other, Table):
            self.raw = other.raw
            self.rel = other.rel
        else:
            self.raw = other
            self.rel = form_relation(other)

    def __repr__(self):
        return repr(self.rel)

    def sql(self, s: str):
        """
        Run a SQL snippet via DuckDB, prepended with `from <table_name>`,
        where `<table_name>` will be a unique and random name to avoid collisions.
        """
        name = '_tlb_' + ''.join(random.choices(string.ascii_lowercase, k=10))
        rel = self.rel.query(name, f'from {name} ' + s)
        return Table(rel)


