from .ddb import query


class TableMixin:
    def asitem(self):
        return self.aslist()[0]

    def asdict(self):
        df = self.df()
        return dict(df.iloc[0])

    def hold(self, kind='arrow'):
        if kind == 'arrow':
            return self.arrow()
        if kind == 'pandas':
            return self.df()
        raise ValueError(f'Unknown kind: {kind!r}')

    def df(self):
        return self.rel.df()

    def arrow(self):
        return self.rel.to_arrow_table()

    def aslist(self):
        df = self.df()
        if len(df.columns) == 1:
            col = df.columns[0]
            out = list(df[col])
        elif len(df) == 1:
            out = list(df.loc[0])
        else:
            raise ValueError(
                'DataFrame should have a single row or column, '
                f'but has shape {df.shape}'
            )

        return out

    @property
    def columns(self):
        return self.rel.columns

    def save_parquet(self, filename):
        _save_format(self, filename, '(format parquet)')

    def save_csv(self, filename):
        _save_format(self, filename, "(header, delimiter ',')")

    def save(self, filename: str):
        if filename.endswith('.parquet'):
            self.save_parquet(filename)
        elif filename.endswith('.csv'):
            self.save_csv(filename)
        else:
            raise ValueError(f'Unrecognized filetype: {filename}')


def _save_format(tbl, filename, format):
    s = f"copy (select * from tbl) to '{filename}' {format};"
    query(s, tbl=tbl.rel)
