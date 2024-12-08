import random
import string

from .ddb import form_relation
from .doer import DoMixin
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

    @property
    def columns(self):
        # NOTE: is this an example where direct access to the relation is helpful?
        rel = self.rel.query('_x_', 'select column_name from (describe from _x_)')
        df = rel.df()
        return list(df['column_name'])
