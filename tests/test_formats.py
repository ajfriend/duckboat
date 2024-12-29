import duckboat as uck
import pandas as pd


def test_dict():
    d = dict(
        a = [1],
        b = [2],
        c = [3],
    )

    df = pd.DataFrame(d)
    t = uck.Table(df)

    assert t.asdict() == d
    assert t.do(dict) == d
