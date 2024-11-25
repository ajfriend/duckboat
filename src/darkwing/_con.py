import duckdb

_darkwing_con = duckdb.connect(database=':memory:')
_darkwing_con.execute("""
install h3 from community;
load h3;
""")
