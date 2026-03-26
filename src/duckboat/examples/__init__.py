import io
import random


def penguins():
    """Palmer Penguins dataset (344 rows, 8 columns).

    Horst AM, Hill AP, Gorman KB (2020). palmerpenguins: Palmer
    Archipelago (Antarctica) penguin data. R package version 0.1.0.
    doi: 10.5281/zenodo.3960218. License: CC-0.
    """
    from ..table import Table
    from ._penguins import PENGUINS_CSV
    import pandas as pd

    df = pd.read_csv(io.StringIO(PENGUINS_CSV))
    return Table(df)


def store(n_orders=100, n_customers=20, seed=0):
    """Synthetic orders/customers dataset for join demos.

    Returns a dict of {'orders': Table, 'customers': Table} suitable
    for passing directly to uck.do().
    """
    from ..table import Table
    import pandas as pd

    rng = random.Random(seed)

    customer_ids = list(range(1, n_customers + 1))
    cities = ['New York', 'Chicago', 'Boston', 'Seattle', 'Denver']

    customers_data = {
        'id': customer_ids,
        'name': [f'Customer_{i}' for i in customer_ids],
        'city': [rng.choice(cities) for _ in customer_ids],
    }

    orders_data = {
        'id': list(range(1, n_orders + 1)),
        'customer_id': [rng.choice(customer_ids) for _ in range(n_orders)],
        'amount': [round(rng.uniform(1, 100), 2) for _ in range(n_orders)],
    }

    return {
        'orders': Table(pd.DataFrame(orders_data)),
        'customers': Table(pd.DataFrame(customers_data)),
    }
