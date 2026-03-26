# v0.19.0

- remove `Database`, `alias`, and `Table.sql()` from the API
- `do()` is now the single entry point for everything
- pass a dict to `do()` to register named tables for joins
- the current table is always available as `_` in SQL
- self-joins via `_` or `uck.rename()`
- step-level context dict replaces the `Table`/`Database` split

# v0.18.1

- fix CI publish workflow filename

# v0.18.0

- require Python >= 3.10
- require duckdb >= 1.5
- use `to_arrow_table()` for Arrow export (fixes deadlock with DuckDB 1.5)
- documentation updated

# v0.17.0

- try to convert leading argument to `Database` or `Table` if possible


# v0.16.0

- add `duckboat.do()` function
- try to convert leading arguments to `Table` if possible
