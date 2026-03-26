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


def test_unexpected_argument():
    t = uck.Table(pd.DataFrame({'a': [0]}))
    with pytest.raises(ValueError, match='Unexpected argument'):
        t.do(42)


def test_hold_unknown_kind():
    t = uck.Table(pd.DataFrame({'a': [0]}))
    with pytest.raises(ValueError, match='Unknown kind'):
        t.hold('json')
