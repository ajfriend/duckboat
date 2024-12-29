import random
import string
from .ddb import query


class TableMixin:
    def asitem(self):
        """Transform a df with one row and one column to single element"""
        # _insist_single_row(df)
        # _insist_single_col(df)
        return self.aslist()[0]

    def asdict(self):
        """Transform a df with one row to a dict
        """
        # TODO: _insist_single_row(df)
        df = self.df()
        return dict(df.iloc[0])

    def hold(self, kind='arrow'):
        """
        Materialize the Table as a PyArrow Table or Pandas DataFrame.
        """
        if kind == 'arrow':
            return self.arrow()
        if kind == 'pandas':
            return self.df()

    def df(self):
        return self.rel.df()

    def arrow(self):
        return self.rel.arrow()

    def aslist(self):
        """Transform a df with one row or one column to a list"""
        df = self.df()
        if len(df.columns) == 1:
            col = df.columns[0]
            out = list(df[col])
        elif len(df) == 1:
            out = list(df.loc[0])
        else:
            raise ValueError(
                'DataFrame should have a single row or column,'
                f'but has shape f{df.shape}'
            )

        return out

    def alias(self, name):
        from .database import Database
        return Database(**{name: self})

    @property
    def columns(self):
        # NOTE: is this an example where direct access to the relation is helpful?
        rel = self.rel.query('_x_', 'select column_name from (describe from _x_)')
        df = rel.df()
        return list(df['column_name'])

    @staticmethod
    def random_table_name():
        name = '_tlb_' + ''.join(random.choices(string.ascii_lowercase, k=10))
        return name

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
