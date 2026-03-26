import duckboat as uck
import pandas as pd


def test_tstring_join():
    orders = pd.DataFrame({'id': [1, 2, 3], 'amount': [10, 20, 30]})
    customers = pd.DataFrame({'id': [1, 2, 3], 'name': ['a', 'b', 'c']})

    out = uck.do(
        t'select name from {orders} join {customers} using (id) order by name',
        list,
    )
    assert out == ['a', 'b', 'c']


def test_tstring_mid_chain():
    t1 = pd.DataFrame({'x': range(10), 'y': range(10)})
    t2 = pd.DataFrame({'x': range(5), 'z': [100, 200, 300, 400, 500]})

    out = uck.Table(t1).do(
        'where x < 5',
        t'join {t2} using (x)',
        'select sum(z)',
        int,
    )
    assert out == 1500


def test_tstring_self_join():
    t1 = pd.DataFrame({'x': [1, 2, 3]})

    out = uck.do(
        t'select count(*) from {t1} a cross join {t1} b',
        int,
    )
    assert out == 9


def test_tstring_scalar():
    df = pd.DataFrame({'x': [1, 2, 3, 4, 5]})
    threshold = 3

    out = uck.Table(df).do(
        t'where x > {threshold}',
        'select count(*)',
        int,
    )
    assert out == 2


def test_tstring_string():
    df = pd.DataFrame({'name': ['Alice', 'Bob', 'Charlie']})
    target = 'Bob'

    out = uck.Table(df).do(
        t'where name = {target}',
        'select count(*)',
        int,
    )
    assert out == 1


def test_tstring_string_escaping():
    df = pd.DataFrame({'name': ["it's", 'ok']})
    target = "it's"

    out = uck.Table(df).do(
        t'where name = {target}',
        'select count(*)',
        int,
    )
    assert out == 1


def test_tstring_bool():
    df = pd.DataFrame({'x': [1, 2, 3], 'active': [True, False, True]})

    out = uck.Table(df).do(
        t'where active = {True}',
        'select count(*)',
        int,
    )
    assert out == 2


def test_tstring_complex_expression():
    data = {'orders': pd.DataFrame({'id': [1, 2], 'amount': [10, 20]})}

    out = uck.do(
        t'select sum(amount) from {data["orders"]}',
        int,
    )
    assert out == 30


def test_tstring_mixed():
    orders = pd.DataFrame({'id': [1, 2, 3], 'amount': [10, 20, 30]})
    customers = pd.DataFrame({'id': [1, 2, 3], 'name': ['a', 'b', 'c']})
    min_amount = 15

    out = uck.do(
        t'select * from {orders} join {customers} using (id)',
        t'where amount > {min_amount}',
        'select name',
        'order by name',
        list,
    )
    assert out == ['b', 'c']
