import duckboat as uck
import pandas as pd
import duckdb
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

    with pytest.raises(duckdb.InvalidInputException):
        uck.Table(df).do(foo, 'select *')


def test_pandas():
    from pandas.testing import assert_frame_equal

    df = pd.DataFrame({'a': [0]})
    t = uck.Table(df)

    assert_frame_equal(
        t.do('pandas'),
        df,
    )


def test_arrow():
    from pandas.testing import assert_frame_equal

    df = pd.DataFrame({'a': range(10)})

    t1 = uck.Table(df)
    t2 = uck.Table(t1.do('arrow'))

    assert_frame_equal(t1.do('pandas'), t2.do('pandas'))


def test_to_from_csv():
    import tempfile

    df = pd.DataFrame({'a': range(10), 'b': range(10)})
    t1 = uck.Table(df)

    with tempfile.NamedTemporaryFile(suffix='.csv') as tf:
        name = tf.name
        t1.save(name)
        t2 = uck.Table(name)
        assert repr(t1) == repr(t2)


def test_to_from_parquet():
    import tempfile

    df = pd.DataFrame({'a': range(10), 'b': range(10)})
    t1 = uck.Table(df)

    with tempfile.NamedTemporaryFile(suffix='.parquet') as tf:
        name = tf.name
        t1.save(name)
        t2 = uck.Table(name)
        assert repr(t1) == repr(t2)


def test_to_unknown_format():
    df = pd.DataFrame({'a': range(10), 'b': range(10)})
    t1 = uck.Table(df)

    with pytest.raises(ValueError):
        t1.save('test.not_a_format')
