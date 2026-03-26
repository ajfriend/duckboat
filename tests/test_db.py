import duckboat as uck
import pandas as pd


def test_dict_join():
    a = pd.DataFrame({'x': range(10)})
    b = pd.DataFrame({'x': range(20)})

    out = uck.do(
        {'a': a, 'b': b},
        """
        select count(*) from a
        union all
        select count(*) from b
        """,
        list,
    )
    assert out == [10, 20]


def test_dict_chain():
    a = pd.DataFrame({'x': range(10)})
    b = pd.DataFrame({'x': range(20)})

    out = uck.do({'a': a, 'b': b}, 'select * from a', 'pandas', list)
    assert out == list(range(10))


def test_mid_chain_join():
    t1 = pd.DataFrame({'x': range(10), 'y': range(10)})
    t2 = pd.DataFrame({'x': range(5), 'z': [100, 200, 300, 400, 500]})

    out = uck.Table(t1).do(
        'where x < 5',
        {'t2': t2},
        'join t2 using (x)',
        'select sum(z)',
        int,
    )
    assert out == 1500


def test_self_join():
    df = pd.DataFrame({'x': [1, 2, 3]})

    out = uck.do(
        {'t': df},
        'select count(*) from t a cross join t b',
        int,
    )
    assert out == 9
