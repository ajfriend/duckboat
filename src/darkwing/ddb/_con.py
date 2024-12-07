import duckdb

# Create a DuckDB database connection specifically for use with Darkwing
__darkwing_con__ = duckdb.connect(database=':memory:')

# Load the H3 extension because we use it in many examples.
__darkwing_con__.execute("""
install h3 from community;
load h3;
""")
