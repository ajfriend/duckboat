import duckboat as uck
import pandas as pd

import pytest


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

def test_bad_object():
    def foo(x):
        return 1

    df = pd.DataFrame({'a': [0]})

    with pytest.raises(ValueError):
        uck.Table(df).do(foo, 'select *')
