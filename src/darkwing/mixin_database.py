# TODO: how to create dummy table objects that raise an error if their repr is called?

class DatabaseMixin:
    def __repr__(self):
        tables = self._yield_table_lines()
        tables = [
            f'\n    {t}'
            for t in tables
        ]
        tables = ''.join(tables)
        tables = tables or ' None'

        out = 'Database:' + tables

        return out

    def _yield_table_lines(self):
        for name, tbl in self.tables.items():
            yield f'{name}: {tbl.rowcols()}'

    def hold(self, kind='arrow'):
        """
        TODO: maybe i don't need this function. or change its name
        Materialize the Database as a collection of PyArrow Tables or Pandas DataFrames
        """
        return {
            name: tbl.hold(kind)
            for name, tbl in self.tables.items()
        }
