import duckboat as uck
import pandas as pd
import numpy as np
import pytest


def test_repr():
    xs = list(range(10))

    df = pd.DataFrame({'a': xs})
    t = uck.Table(df)

    assert t.do(list) == xs

def test_list():
    df = pd.DataFrame(np.zeros((1,10)))
    t = uck.Table(df)
    assert t.do(list) == [0.0]*10


    df = pd.DataFrame(np.zeros((10,10)))
    t = uck.Table(df)

    with pytest.raises(ValueError):
        t.do(list)
