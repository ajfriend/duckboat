# v0.20.0 (2026-03-26)

- t-string support (Python 3.14+): `t'select * from {orders} join {customers} using (id)'`
- scalars, strings, and tables dispatch automatically in t-strings
- `uck.examples` module: `penguins()` dataset and `store()` synthetic join data
- remove `hold()` method; use `do('pandas')` and `do('arrow')` instead
- multi-version coverage via tox (3.13 + 3.14 combined, 100% coverage required)
- documentation rewrite

# v0.19.0 (2026-03-26)

- remove `Database`, `alias`, and `Table.sql()` from the API
- `do()` is now the single entry point for everything
- pass a dict to `do()` to register named tables for joins
- the current table is always available as `_` in SQL
- self-joins via `_` or `uck.rename()`
- step-level context dict replaces the `Table`/`Database` split

# v0.18.1 (2026-03-25)

- fix CI publish workflow filename

# v0.18.0 (2026-03-25)

- require Python >= 3.10
- require duckdb >= 1.5
- use `to_arrow_table()` for Arrow export (fixes deadlock with DuckDB 1.5)
- documentation updated

# v0.17.0 (2025-03-01)

- try to convert leading argument to `Database` or `Table` if possible

# v0.16.0 (2025-02-28)

- add `duckboat.do()` function
- try to convert leading arguments to `Table` if possible
