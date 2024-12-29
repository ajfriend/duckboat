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


def test_hold():
    from pandas.testing import assert_frame_equal

    df = pd.DataFrame({'a': [0]})
    t = uck.Table(df)

    assert_frame_equal(
        t.do('pandas'),
        df,
    )


def test_arrow():
    df = pd.DataFrame({'a': range(10)})

    t1 = uck.Table(df)
    t2 = uck.Table(t1.do('arrow'))

    assert repr(t1) == repr(t2)


def test_alias():
    df = pd.DataFrame({'a': [0]})
    t = uck.Table(df)
    assert repr(t.do('alias bah')) == "Database:\n    bah: 1 x ['a']"


def test_db_hold():
    from pandas.testing import assert_frame_equal

    df = pd.DataFrame({'a': [0]})
    db = uck.Database(df=df)

    d = db.hold('pandas')

    assert isinstance(d, dict)
    assert_frame_equal(
        d['df'],
        df,
    )


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
