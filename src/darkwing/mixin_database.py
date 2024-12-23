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
            if isinstance(tbl.raw, str):
                yield f"{name}: '{tbl.raw}'"
            else:
                n = self.do(f'select count() from {name}', int)
                yield f'{name}: {n} x {tbl.columns}'

    def __getitem__(self, key):
        return self.tables[key].raw

    def hold(self, kind='arrow'):
        """
        Materialize the Database as a collection of PyArrow Tables or Pandas DataFrames
        """
        from .database import Database
        return Database(**{
            name: self.do(f'from {name}', kind)
            for name in self.tables
        })
