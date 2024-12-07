import darkwing as dw
import pandas as pd

def test_str():
    t = dw.Table(pd.DataFrame({'a': [0]}))

    f = 'select a + 1 as a'

    assert t.do(f, int) == 1
    assert t.do(f,f,f, int) == 3
    assert t.do([f,f,f], int) == 3


def test_func():
    t = dw.Table(pd.DataFrame({'a': [0]}))

    def foo(t):
        return t.do('select a + 1 as a')
    
    assert t.do(foo, int) == 1
    assert t.do(foo,foo,foo, int) == 3
    assert t.do([foo,foo,foo], int) == 3


def test_filename():
    t = dw.Table(pd.DataFrame({'a': [0]}))
    f = 'tests/foo.sql'  # path is relative to where the test command is being run
    
    assert t.do(f, int) == 1
    assert t.do(f,f,f, int) == 3
    assert t.do([f,f,f], int) == 3


def test_path():
    from pathlib import Path
    t = dw.Table(pd.DataFrame({'a': [0]}))
    f = Path('tests/foo.sql')  # path is relative to where the test command is being run

    assert t.do(f, int) == 1
    assert t.do(f,f,f, int) == 3
    assert t.do([f,f,f], int) == 3