# v0.18.0

- require Python >= 3.10
- require duckdb >= 1.5
- use `to_arrow_table()` for Arrow export (fixes deadlock with DuckDB 1.5)

# v0.17.0

- try to convert leading argument to `Database` or `Table` if possible


# v0.16.0

- add `duckboat.do()` function
- try to convert leading arguments to `Table` if possible
