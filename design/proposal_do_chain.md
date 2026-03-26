---
title: "Proposal: Unifying the duckboat API with do() Chain Dispatch"
date: 2026-03-25
toc: false
numbersections: false
---

# Background

duckboat currently has two main objects:

- **`Table`:** A single lazy DuckDB relation. `Table.do()` chains SQL snippets,
  auto-wrapping each as `SELECT * FROM _prev_ <step>`.
- **`Database`:** A named dict of tables. `Database.do()` and `Database.sql()`
  run SQL with explicit table names. Used for joins.

There is also `alias`, which wraps a single `Table` into a `Database` with a
given name (used for self-joins).

The `Database` object exists only to give tables names for SQL queries. This
proposal replaces it with two simpler mechanisms in the `do()` chain, rolled out
in two stages.


# Stage 1: Dict dispatch (any Python version)

## What changes

The `do()` chain gains dict as a new argument type. A dict in the chain
registers named tables for the next SQL step. After the SQL executes, the names
are forgotten---only the result carries forward.

```python
# Multi-table join
uck.do(
    {'orders': orders_df, 'customers': customers_df},
    'select * from orders join customers using (id)',
    'where total > 100',
)

# Mid-chain join
t1.do(
    'where total_amount > 0',
    'select *, pickup_zone_id as zid',
    {'zones': zones_df},
    'join zones on zid = zones.id',
    'select zone_name, avg(total_amount) group by 1',
)

# Self-join
t1.do(
    uck.rename('t1'),
    'from t1 as a join t1 as b using (hexid)',
)
```

## What gets removed

- **`Database` class** (public API): replaced by dict-in-chain.
- **`alias` method:** replaced by dict-in-chain.
- **`Database.sql()`:** replaced by dict + SQL string in chain.
- **`Database.hold()`:** users materialize individual tables instead.
- **`Database.__repr__()`**, **`keys()`**, **`__getitem__()`:** no longer needed
  when the user holds the dict themselves.

## Migration

**Multi-table query:**

```python
# before
Database(a=df1, b=df2).sql('select ...')

# after
uck.do({'a': df1, 'b': df2}, 'select ...')
```

**Self-join:**

```python
# before
t.alias('name').do('select ...')

# after
t.do(uck.rename('t'), 'from t as a join t as b using (hexid)')
```

**Materialize all tables:**

```python
# before
Database(a=df1, b=df2).hold('pandas')

# after -- call .do('pandas') on each table individually
```

## What stays

- **`Table`:** unchanged, still the core object.
- **`Table.do()` / `uck.do()`:** unchanged interface, new dispatch cases.
- **`Table.hold()`:** materialize a single table.
- **`Table.sql()`:** removed. `do()` handles all SQL execution.

The internal `query()` function that registers named relations with DuckDB
stays---it is the backend for the dict step.

## Internal cleanup

With `Database` removed, the `do()` internals get simpler. The context is
always a `dict[str, Table]`. The key `'_'` holds the implicit table. The
presence of `'_'` in the context is the sole signal for whether to auto-wrap
SQL with `from _`.

- No more `isinstance(A, Table)` vs `isinstance(A, Database)`.
- `DatabaseMixin`, `mixin_database.py`, `Table.sql()`, and
  `random_table_name()` are removed entirely.
- `DoMixin` stays but gets simplified---one code path instead of two.
- `_do_one()` dispatches on the argument type only, not the accumulator type.

## Design decisions for Stage 1

- **Dict scope:** next step only. After the SQL executes, named tables are
  forgotten. No hidden state accumulation.

## Future work

- **Arrow detection:** detect `__arrow_c_stream__` on dict values to accept any
  Arrow-compatible tabular object. Separate PR.
- **Consistent context type:** currently the internal context (`ctx`) is a dict
  most of the time, but materializers return raw values (int, DataFrame, etc.),
  breaking the invariant. Consider wrapping materializer returns as
  `{_PREV: raw_value}` and only unwrapping at the end of `_do()`. This would
  make `ctx` always a dict, remove the `isinstance(ctx, dict)` guard in
  `_do_one`, and make the variable name honest. Rename to `env` or `scope` to
  reflect that it's a name-to-table mapping.


# Stage 2: T-string syntactic sugar (Python 3.14+)

Stage 2 depends on Stage 1 being stable. It adds t-string as another dispatch
type---syntactic sugar that builds the dict automatically from interpolated
variables.

## What changes

A [t-string](https://peps.python.org/pep-0750/) (template string, Python 3.14)
in the `do()` chain is processed as follows:

1. Walk the template's interpolations.
2. For each interpolation, use `.expression` as the table name and `.value` as
   the data.
3. Build a dict from these pairs.
4. Merge into the current context.
5. Reconstruct the SQL from the template's static strings and expression names.
6. Execute and return a `Table`.

This is exactly the dict step from Stage 1, with the dict built implicitly from
variable names.

```python
# Multi-table join
uck.do(
    t"select * from {orders} join {customers} using (id)",
    'where total > 100',
)

# Mid-chain join
t1.do(
    'where total_amount > 0',
    t"join {zones} on zid = zones.id",
    'select zone_name, avg(total_amount) group by 1',
)

# Self-join (same variable referenced twice is fine)
t1.do(
    t"select * from {t1} a join {t1} b using (hexid)",
)
```

## Why Stage 2 is separate

- **Python 3.14 is pre-release** as of this writing. Requiring it would limit
  adoption. The dict syntax from Stage 1 works on any Python version.
- **The dict syntax validates the design.** If the "register, use, forget"
  semantics work well with dicts, adding t-string sugar is low-risk. If
  something needs to change, it is better to learn that before adding a second
  syntax for the same thing.
- **T-strings are sugar, not substance.** They produce the same dict
  internally. No new semantics, just ergonomics.

## Relationship between dict and t-string

The t-string step is equivalent to a dict step followed by a SQL string step.
This t-string:

```python
t1.do(t"join {zones} on zid = zones.id")
```

is equivalent to:

```python
t1.do({'zones': zones}, 'join zones on zid = zones.id')
```

The t-string just infers the dict and reconstructs the SQL from the template.

## Open question for Stage 2

- **Minimum Python version:** should duckboat bump `requires-python` to 3.14
  when t-string support ships, or should t-strings be an optional feature that
  works if available?


# Dispatch rules (both stages combined)

The `do()` chain processes arguments left to right. At each step, it has a
"current context"---a `dict[str, Table]` mapping names to tables. The
implicit/current table is stored under the key `'_'`. This means the current
table is always available as `_` in SQL, and `from _` is always prepended to
SQL snippets when `'_'` is in the context.

| Argument type                               | Stage | Behavior                                                                                            |
|---------------------------------------------|-------|-----------------------------------------------------------------------------------------------------|
| DataFrame, filename, or Arrow object        | --    | Wrap as a `Table`, set as `{'_': table}`                                                            |
| SQL string                                  | --    | If `'_'` in context, prepend `from _`. Execute against named tables. Result becomes `{'_': result}` |
| Dict                                        | 1     | Merge into the current context. Names available for the next SQL step only                          |
| T-string                                    | 2     | Build dict from interpolations, merge, reconstruct SQL, execute. Result becomes `{'_': result}`     |
| `uck.rename('name')`                        | 1     | Rename `'_'` to `'name'` in context, removing `'_'`. Enables self-joins with natural SQL            |
| List                                        | --    | Recursively call `do()` with the list contents (reusable pipeline fragments)                        |
| Callable                                    | --    | Call with the current table, result becomes `{'_': result}`                                         |
| Type (`list`, `dict`, `int`, etc.)          | --    | Materialize the current table as that type and return                                               |
| String materializer (`'pandas'`, `'arrow'`) | --    | Materialize the current table via `hold()` and return                                               |


# Benefits

- **One entry point** (`do`) instead of two objects with different SQL
  semantics.
- **Nothing new to learn.** No `Database`, `alias`, or decision about when to
  use `sql()` vs `do()`.
- **Dict syntax works on all Python versions.** T-strings are a bonus for
  3.14+.
- **Self-joins are natural.** Use `uck.rename('t')` to name the current table,
  then write standard SQL.
- **No hidden state.** "Register, use, forget"---names exist only for the next
  step.
- **Chaining always works.** Every step produces a `Table`.
- **Incremental rollout.** Stage 1 validates the design on stable Python. Stage
  2 adds sugar once the foundation is solid.
