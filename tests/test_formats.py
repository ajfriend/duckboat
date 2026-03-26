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

    with pytest.raises(TypeError, match='__arrow_c_stream__'):
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


def test_arrow_c_stream_roundtrip():
    import pyarrow as pa

    df = pd.DataFrame({'a': [1, 2, 3], 'b': ['x', 'y', 'z']})
    t = uck.Table(df)

    reader = pa.RecordBatchReader.from_stream(t)
    table = reader.read_all()
    assert table.column_names == ['a', 'b']
    assert table['a'].to_pylist() == [1, 2, 3]
    assert table['b'].to_pylist() == ['x', 'y', 'z']


def test_bad_type_error():
    with pytest.raises(TypeError, match='__arrow_c_stream__'):
        uck.Table(42)


def test_missing_file_error():
    with pytest.raises(duckdb.IOException, match='nonexistent.parquet'):
        uck.Table('nonexistent.parquet')


def test_to_unknown_format():
    df = pd.DataFrame({'a': range(10), 'b': range(10)})
    t1 = uck.Table(df)

    with pytest.raises(ValueError):
        t1.save('test.not_a_format')
