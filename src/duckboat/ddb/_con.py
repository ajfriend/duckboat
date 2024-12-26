import duckdb

# Create a DuckDB database connection specifically for use with Duckboat
__duckboat_con__ = duckdb.connect(database=':memory:')

# Load the H3 extension because we use it in many examples.
__duckboat_con__.execute("""
install h3 from community;
load h3;
""")
