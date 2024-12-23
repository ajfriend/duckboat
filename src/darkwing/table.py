from .ddb import form_relation
from .mixin_do import DoMixin
from .mixin_table import TableMixin

from duckdb import DuckDBPyRelation


# IDEA: maybe a `_hide` flag on tables that infects downstream tables and databases?
# `_hide` is only relevant in the repr.
# actually, maybe we don't need it to infect. we can just pop it in when needed.
# repr = False

# we should probably cache the repr output, assume all table objects are immutable.
# we need to figure out how to handle the instance variables, since those will also be represented
# i think we can simplify to have table just have `rel` and no `raw`.
# if people want dataframes, they can get a dict of dfs from `database.df()) or something, but this can be utilized in a do sequence if they wanted to keep going
# if they want to see what a dict of dataframes looks like, they put it into a `Database(**d)`
# repr=False might need to pass down to child Tables

class Table(TableMixin, DoMixin):
    """
    The table name is always included implicitly when applying a SQL snippet.
    """
    rel: DuckDBPyRelation  # todo: we might have to hide even this from the prying eyes of Positron.
    _hide: bool

    def __init__(self, other, _hide=False):
        self._hide = _hide

        if isinstance(other, Table):
            self.rel = other.rel
        elif isinstance(other, DuckDBPyRelation):
            self.rel = other
        else:
            self.rel = form_relation(other)

    def __repr__(self):
        if self._hide:
            return f'<Table(..., _hide={self._hide})>'
        else:
            return repr(self.rel)

    def hide(self):
        return Table(self, _hide=True)

    def show(self):
        return Table(self, _hide=False)

    def sql(self, s: str):
        """
        Run a SQL snippet via DuckDB, prepended with `from <table_name>`,
        where `<table_name>` will be a unique and random name to avoid collisions.
        """
        name = TableMixin.random_table_name()
        rel = self.rel.query(name, f'from {name} ' + s)
        return Table(rel)
