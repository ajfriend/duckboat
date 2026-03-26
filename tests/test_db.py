import duckboat as uck
import pandas as pd
import pytest


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


def test_chained_steps_no_collision():
    """Ensure _ doesn't collide across chained steps."""
    df = pd.DataFrame({'a': [1, 2, 3]})

    out = uck.Table(df).do(
        'select a + 1 as a',
        'select a + 1 as a',
        'select a + 1 as a',
        'select sum(a)',
        int,
    )
    assert out == 15  # (1+3) + (2+3) + (3+3)


def test_self_join_underscore():
    df = pd.DataFrame({'x': [1, 2, 3]})

    out = uck.Table(df).do(
        'as a cross join _ as b select count(*)',
        int,
    )
    assert out == 9


def test_self_join_after_chain():
    """Ensure _ refers to the correct table after multiple chained steps."""
    df = pd.DataFrame({'x': [1, 2, 3, 4, 5]})

    out = uck.Table(df).do(
        'where x <= 3',
        'as a cross join _ as b select count(*)',
        int,
    )
    # after filter: 3 rows, cross join: 3*3 = 9
    assert out == 9


def test_rename_self_join():
    df = pd.DataFrame({'x': [1, 2, 3]})
    out = uck.Table(df).do(
        uck.rename('t'),
        'from t as a cross join t as b select count(*)',
        int,
    )
    assert out == 9


def test_rename_after_chain():
    df = pd.DataFrame({'x': [1, 2, 3, 4, 5]})
    out = uck.Table(df).do(
        'where x <= 3',
        uck.rename('t'),
        'from t as a cross join t as b select count(*)',
        int,
    )
    assert out == 9


def test_arrow_dict_value():
    import pyarrow as pa

    t = pa.table({'x': [1, 2, 3]})
    out = uck.do(
        {'t': t},
        'select sum(x) from t',
        int,
    )
    assert out == 6


def test_polars_dict_value():
    import polars as pl

    df = pl.DataFrame({'x': [1, 2, 3]})
    out = uck.do(
        {'t': df},
        'select sum(x) from t',
        int,
    )
    assert out == 6


def test_rename_no_table():
    with pytest.raises(ValueError, match='no implicit table'):
        uck.do({'a': pd.DataFrame({'x': [1]})}, uck.rename('b'))
