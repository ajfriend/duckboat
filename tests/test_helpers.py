import duckboat as uck
import pandas as pd


def test_repr():
    xs = list(range(10))

    df = pd.DataFrame({'a': xs})
    t = uck.Table(df)

    assert t.do(list) == xs
