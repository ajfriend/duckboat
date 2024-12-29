import duckboat as uck
import pandas as pd
import numpy as np


def dedent_helper(s):
    from textwrap import dedent
    s = dedent(s)
    s = s.strip()
    s += '\n'
    return s


def test_repr():
    df = pd.DataFrame({'a': [0]})
    out = """
    ┌───────┐
    │   a   │
    │ int64 │
    ├───────┤
    │     0 │
    └───────┘
    """
    out = dedent_helper(out)

    t = uck.Table(df)
    assert repr(t) == out

    t = uck.Table(df, _hide=False)
    assert repr(t) == out

    t = uck.Table(df, _hide=True)
    assert repr(t) == '<Table(..., _hide=True)>'

    t = uck.Table(df).hide()
    assert repr(t) == '<Table(..., _hide=True)>'

    t = uck.Table(df).hide().show()
    assert repr(t) == out

    t = uck.Table(df).do('hide', 'show')
    assert repr(t) == out


def test_rowcols():
    shape = (17, 4)

    df = pd.DataFrame(np.zeros(shape))
    t = uck.Table(df)

    assert t.rowcols() == "17 x ['0', '1', '2', '3']"

    t = uck.Table(df).hide()
    assert t.rowcols() == '<Table(..., _hide=True)>'
