---
title: "Proposal: Unifying the duckboat API with do() Chain Dispatch"
date: 2026-03-25
toc: false
numbersections: false
---

# Background

duckboat previously had two main objects: `Table` and `Database`. `Database`
existed only to give tables names for SQL queries (joins). Stage 1 replaced it
with dict-in-chain dispatch and `uck.rename()`, simplifying the API to a single
entry point: `do()`.

This document covers both Stage 1 (implemented) and Stage 2 (planned).


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
  `{'_': raw_value}` and only unwrapping at the end of `_do()`. This would
  make `ctx` always a dict, remove the `isinstance(ctx, dict)` guard in
  `_do_one`, and make the variable name honest. Rename to `env` or `scope` to
  reflect that it's a name-to-table mapping.


# Stage 2: T-string syntactic sugar (Python 3.14+)

Stage 2 depends on Stage 1 being stable. It adds t-string as another dispatch
type---syntactic sugar that builds the dict automatically from interpolated
variables.

## Backwards compatibility

The library never contains t-string syntax itself. It only receives `Template`
objects from user code. The `Template` class is imported with a try/except
guard:

```python
try:
    from string.templatelib import Template as _Template
except ImportError:
    _Template = type(None)  # will never match isinstance
```

On Python < 3.14, `_Template` is `type(None)`, so the `isinstance` check in
`_do_one` never matches. On 3.14+, users can pass `t'...'` and it works. No
version-specific files, no feature flags. The library works on all supported
Python versions.

## What changes

A [t-string](https://peps.python.org/pep-0750/) (template string, Python 3.14)
in the `do()` chain is processed as follows:

1. Walk the template's interpolations.
2. For each interpolation, dispatch on the **value type**:
   - **Scalar** (`int`, `float`, `bool`): inline as a SQL literal.
   - **String** (`str`): inline as a quoted SQL string.
   - **Table-like** (DataFrame, Table, Arrow, etc.): register as a named table.
     If `.expression` is a valid Python identifier (checked via
     `str.isidentifier()`), use it as the table name. Otherwise, generate a
     unique random name.
3. Reconstruct the SQL from the template's static strings and resolved
   fragments.
4. Merge any registered tables into the current context.
5. Execute and return a `Table`.

This means t-strings handle both table references and parameterized values:

```python
# Table references
t.do(t'join {customers} using (id)')
# customers is a DataFrame → registered as 'customers'
# becomes: join customers using (id)

# Scalar parameters
name = 'Alice'
min_age = 25
t.do(t'where name = {name} and age > {min_age}')
# becomes: where name = 'Alice' and age > 25
```

```python
# Multi-table join
uck.do(
    t'select * from {orders} join {customers} using (id)',
    'where total > 100',
)

# Mid-chain join
t1.do(
    'where total_amount > 0',
    t'join {zones} on zid = zones.id',
    'select zone_name, avg(total_amount) group by 1',
)

# Self-join (start from uck.do, no _ in context)
uck.do(
    t'select * from {t1} a join {t1} b using (hexid)',
)

# Self-join (mid-chain, use rename to name the current table)
t1.do(
    uck.rename('t1'),
    t'from t1 as a join t1 as b using (hexid)',
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

For table references, the t-string step is equivalent to a dict step followed by
a SQL string step. This t-string:

```python
t1.do(t'join {zones} on zid = zones.id')
```

is equivalent to:

```python
t1.do({'zones': zones}, 'join zones on zid = zones.id')
```

For scalar parameters, t-strings have no dict equivalent---they inline values
directly into the SQL. This replaces what users currently do with f-strings, but
with the safety of type-based dispatch instead of raw string interpolation.

## Testing

T-string syntax won't parse on Python < 3.14, so t-string tests live in a
separate file from the dict tests:

```
tests/test_db.py           # dict tests (all versions)
tests/test_tstrings.py     # t-string tests (3.14+ only)
```

`test_tstrings.py` has a module-level skip at the top:

```python
import sys
import pytest
if sys.version_info < (3, 14):
    pytest.skip('t-strings require 3.14+', allow_module_level=True)
```

Each t-string test mirrors a corresponding dict test in `test_db.py`, making it
easy to verify they produce the same results.


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
| T-string                                    | 2     | Scalars inline as literals, tables registered by name, SQL reconstructed and executed               |
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
