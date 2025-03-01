import duckboat as uck
import pandas as pd


def dedent_helper(s):
    from textwrap import dedent
    s = dedent(s)
    s = s.strip()
    # s += '\n'
    return s


def test_db():
    a = pd.DataFrame({'x': range(10)})
    b = pd.DataFrame({'x': range(20)})
    db = uck.Database(a=a, b=b)

    out = db.do("""
    select count(*) from a
    union all
    select count(*) from b
    """, list)

    assert out == [10, 20]


def test_db2():
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

    out = uck.do({'a': a, 'b': b}, 'select * from a', 'pandas', list)
    assert out == list(range(10))


def test_hide_show():
    a = pd.DataFrame({'x': range(10)})
    b = pd.DataFrame({'x': range(20)})

    db = uck.Database(a=a, b=b)

    s_hide = dedent_helper("""
    Database:
        a: <Table(..., _hide=True)>
        b: <Table(..., _hide=True)>
    """)

    assert repr(db.hide()) == s_hide

    s_show = dedent_helper("""
    Database:
        a: 10 x ['x']
        b: 20 x ['x']
    """)

    assert repr(db.show()) == s_show
