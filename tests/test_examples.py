import duckboat as uck
from duckboat import examples


def test_penguins():
    t = examples.penguins()
    assert isinstance(t, uck.Table)
    assert t.do('select count(*)', int) == 344
    assert 'species' in t.columns


def test_store():
    store = examples.store()
    assert isinstance(store, dict)
    assert 'orders' in store
    assert 'customers' in store
    assert isinstance(store['orders'], uck.Table)
    assert isinstance(store['customers'], uck.Table)


def test_store_sizes():
    store = examples.store(n_orders=50, n_customers=10)
    assert store['orders'].do('select count(*)', int) == 50
    assert store['customers'].do('select count(*)', int) == 10


def test_store_deterministic():
    s1 = examples.store(seed=42)
    s2 = examples.store(seed=42)
    a1 = s1['orders'].do('select sum(amount)', float)
    a2 = s2['orders'].do('select sum(amount)', float)
    assert a1 == a2


def test_store_join():
    store = examples.store()
    result = uck.do(
        store,
        """
        select name, sum(amount) as total
        from orders
        join customers on orders.customer_id = customers.id
        group by 1
        """,
        'select count(*)',
        int,
    )
    assert result == 20  # one row per customer
