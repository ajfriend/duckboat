import duckboat as uck
import pandas as pd


def test_repr():
    from textwrap import dedent

    df = pd.DataFrame({'a': [0]})
    out = """
    ┌───────┐
    │   a   │
    │ int64 │
    ├───────┤
    │     0 │
    └───────┘
    """
    out = dedent(out)
    out = out.strip()
    out += '\n'


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


def test_rowcols():
    import numpy as np
    shape = (17, 4)

    df = pd.DataFrame(np.zeros(shape))
    t = uck.Table(df)

    assert t.rowcols() == "17 x ['0', '1', '2', '3']"

    t = uck.Table(df).hide()
    assert t.rowcols() == '<Table(..., _hide=True)>'
