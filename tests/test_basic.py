import darkwing as dw
import pandas as pd

def test_1():
    t = dw.Table(pd.DataFrame({'a': [0]}))

    f = 'select a + 1 as a'

    assert t.do(f, int) == 1
    assert t.do(f,f,f, int) == 3
    assert t.do([f,f,f], int) == 3


def test_2():
    t = dw.Table(pd.DataFrame({'a': [0]}))

    def foo(t):
        return t.do('select a + 1 as a')
    
    assert t.do(foo, int) == 1
    assert t.do(foo,foo,foo, int) == 3
    assert t.do([foo,foo,foo], int) == 3
