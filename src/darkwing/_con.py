import duckdb

def _create_con():
    con = duckdb.connect(database=':memory:')
    con.execute("""
    install h3 from community;
    load h3;
    """)

    return con


_darkwing_con = _create_con()
