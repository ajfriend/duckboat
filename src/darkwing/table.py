from .ddb import form_relation
from .mixin_do import DoMixin
from .mixin_table import TableMixin

from duckdb import DuckDBPyRelation


# IDEA: maybe a `hide_repr` flag on tables that infects downstream tables and databases?
# `hide_repr` is only relevant in the repr.
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
    hide_repr: bool

    def __init__(self, other, hide_repr=False):
        self.hide_repr = hide_repr

        if isinstance(other, Table):
            self.rel = other.rel
        elif isinstance(other, DuckDBPyRelation):
            self.rel = other
        else:
            self.rel = form_relation(other)

    def __repr__(self):
        if self.hide_repr:
            return f'<Table(..., hide_repr={self.hide_repr})>'
        else:
            return repr(self.rel)

    def hide(self):
        return Table(self, hide_repr=True)

    def show(self):
        return Table(self, hide_repr=False)

    def sql(self, s: str):
        """
        Run a SQL snippet via DuckDB, prepended with `from <table_name>`,
        where `<table_name>` will be a unique and random name to avoid collisions.
        """
        name = TableMixin.random_table_name()
        rel = self.rel.query(name, f'from {name} ' + s)
        return Table(rel)
