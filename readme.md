# Duckboat

*Ugly to some, but gets the job done.*

[GitHub](https://github.com/ajfriend/duckboat) | [Docs](https://ajfriend.com/duckboat/) | [PyPI](https://pypi.org/project/duckboat/) | [![coverage](https://img.shields.io/badge/coverage-100%25-brightgreen)](https://github.com/ajfriend/duckboat/actions/workflows/coverage.yml)

Duckboat is a SQL-based Python dataframe library for ergonomic interactive
data analysis and exploration.


```python
pip install duckboat
```

Duckboat allows you to chain SQL snippets (meaning you can usually omit `select *` and `from ...`)
to incrementally and lazily build up complex queries.

Duckboat is a light wrapper around the
[DuckDB relational API](https://duckdb.org/docs/api/python/relational_api),
so
expressions are evaluated lazily and optimized by DuckDB prior to execution.
The resulting queries are fast, avoiding the need to materialize intermediate tables or
perform data transfers.
You can leverage all the SQL syntax improvements provided by DuckDB:
[1](https://duckdb.org/2022/05/04/friendlier-sql.html)
[2](https://duckdb.org/2023/08/23/even-friendlier-sql.html)
[3](https://duckdb.org/docs/sql/dialect/friendly_sql.html)

## Examples

```python
import duckboat as uck

uck.do(
    'https://raw.githubusercontent.com/allisonhorst/palmerpenguins/main/inst/extdata/penguins.csv',
    "where sex = 'female' ",
    'where year > 2008',
    'select *, cast(body_mass_g as double) as grams',
    'select species, island, avg(grams) as avg_grams group by 1,2',
    'select * replace (round(avg_grams, 1) as avg_grams)',
    'order by avg_grams',
)
```

```
┌───────────┬───────────┬───────────┐
│  species  │  island   │ avg_grams │
│  varchar  │  varchar  │  double   │
├───────────┼───────────┼───────────┤
│ Adelie    │ Torgersen │    3193.8 │
│ Adelie    │ Dream     │    3357.5 │
│ Adelie    │ Biscoe    │    3446.9 │
│ Chinstrap │ Dream     │    3522.9 │
│ Gentoo    │ Biscoe    │    4786.3 │
└───────────┴───────────┴───────────┘
```

### To and from other data formats

We can translate to and from other data formats like Pandas DataFrames, Polars, or Arrow Tables.

```python
import pandas as pd

df = pd.DataFrame({'a': [0]})
t = uck.do(df)
t
```

```
┌───────┐
│   a   │
│ int64 │
├───────┤
│     0 │
└───────┘
```

Translate back to a pandas dataframe:

```python
t.do('pandas')
```

You can mix duckboat with pandas or polars mid-workflow. Do the heavy lifting in
SQL, pop into pandas for fiddly column operations, then come back:

```python
df = t.do('where body_mass_g between 3500 and 4000', 'pandas')
df = df.rename(columns=str.upper)
result = uck.do(df, 'select SPECIES, count(*) as n group by 1')
```


### Chaining expressions

You can chain calls to `Table.do()`:


```python
f = 'select a + 1 as a'
t.do(f).do(f).do(f)
```

```
┌───────┐
│   a   │
│ int64 │
├───────┤
│     3 │
└───────┘
```

Alternatively, `Table.do()` accepts a sequence of arguments:

```
t.do(f, f, f)
```

It also accepts lists of expressions, and will apply them recursively:

```python
fs = [f, f, f]
t.do(fs)
```

Note, you could also still call this as:

```python
t.do(*fs)
```

Use lists to group expressions, which Duckboat will apply recursively:

```python
t.do(f, [f], [f, [[f, f], f]])
```

```
┌───────┐
│   a   │
│ int64 │
├───────┤
│     6 │
└───────┘
```

Duckboat will also apply functions:

```python
def foo(x):
    return x.do('select a + 2 as a')

# the following are equivalent
foo(t)
t.do(foo)
```

Of course, you can mix functions, SQL strings, and lists:

```python
uck.do(df, foo, [f, foo])
```

```
┌───────┐
│   a   │
│ int64 │
├───────┤
│     5 │
└───────┘
```


### Joins

Pass a dict to register named tables, then write SQL that references them:

```python
orders = pd.DataFrame({'id': [1, 2, 3], 'customer_id': [10, 20, 10], 'amount': [5.0, 12.0, 8.0]})
customers = pd.DataFrame({'id': [10, 20], 'name': ['Alice', 'Bob']})

uck.do(
    {'orders': orders, 'customers': customers},
    '''
    select c.name, sum(o.amount) as total
    from orders o
    join customers c on o.customer_id = c.id
    group by 1
    ''',
)
```

```
┌─────────┬────────┐
│  name   │ total  │
│ varchar │ double │
├─────────┼────────┤
│ Alice   │   13.0 │
│ Bob     │   12.0 │
└─────────┴────────┘
```

You can also join mid-chain. The current table is always available as `_`:

```python
store = uck.examples.store()

store['orders'].do(
    'where amount > 10',
    {'customers': store['customers']},
    'join customers on customer_id = customers.id',
    'select name, sum(amount) as total group by 1',
)
```

Since `from _` is always prepended, you can also self-join by aliasing both
sides directly:

```python
t.do('as a join _ as b using (hexid)')
```

Or use `uck.rename()` to give the current table a name and write full SQL:

```python
t.do(
    uck.rename('trips'),
    'from trips as a join trips as b using (hexid)',
)
```

### Dispatch rules

`do()` dispatches on the type of each argument.

**SQL:**

```python
t.do('where x > 5')                # SQL snippet (from _ is prepended)
t.do('queries/transform.sql')      # .sql file path (loaded and executed)
```

**Composition:**

```python
t.do(my_func)                      # callable — receives Table, returns Table
t.do([step1, step2, step3])        # list — applied recursively as a pipeline
t.do({'other': other_df})          # dict — registers named tables for next step
t.do(uck.rename('trips'))          # rename — gives _ a name, removes auto-wrap
```

**T-strings (Python 3.14+):**

On Python 3.14+, t-strings can replace the dict syntax for joins and inline
scalar parameters. See the [t-string guide](https://ajfriend.com/duckboat/tstrings.html)
for details.

**Output:**

```python
t.do('select count(*)', int)       # Python int
t.do('select distinct a', list)    # Python list
t.do('limit 1', dict)              # Python dict
t.do('pandas')                     # Pandas DataFrame
t.do('arrow')                      # PyArrow Table
```

**Display:**

```python
t.do('hide')                       # suppress repr (useful for large lazy tables)
t.do('show')                       # re-enable repr
```


### Objects

#### Table

`Table` wraps a DuckDB `DuckDBPyRelation`. The easiest way to create one is
through `do()`:

```python
t = uck.do('data.parquet')
t = uck.do(pd.DataFrame({'x': [1, 2, 3]}))
t = uck.do('https://example.com/data.csv')
```

`.do()` chains operations and dispatches on argument type (strings, functions,
lists, dicts, type conversions). Access the underlying DuckDB relation with
`t.rel`.

#### Eager evaluation and `hide`/`show`

Calling `repr()` on a `Table` triggers query evaluation. In Jupyter, this happens when an object is the last expression in a cell. In IDEs like Positron, the variable explorer proactively inspects objects, which can trigger expensive computations.

Use `hide()` to suppress evaluation:

```python
big = uck.examples.penguins().do('hide')
# Positron's variable explorer will see: <Table(..., _hide=True)>
# instead of evaluating the full query
```

Call `show()` (or `.do('show')`) when you're ready to see results.

## Philosophy

Duckboat bets that SQL is already the right language for tabular data manipulation -- you just need a way to compose SQL snippets into pipelines. This results in a mixture of Python and SQL that is semantically similar to [Google's Pipe Syntax for SQL](https://research.google/pubs/sql-has-problems-we-can-fix-them-pipe-syntax-in-sql/).

**Strengths:**

- **Zero new API to learn.** If you know SQL, you know duckboat. There are no new method chains, expression builders, or DSLs to memorize.
- **Minimal surface area.** The library is essentially `Table` and `.do()`. The codebase is small and stays out of your way.
- **Snippet composability.** SQL fragments chain naturally through `do()`, letting you build complex queries incrementally and interactively.

**Tradeoffs:**

- **No IDE autocomplete on column names.** Column references live inside SQL strings, so you don't get tab-completion or type checking. Typos surface at runtime, not in your editor.
- **Discoverability.** The `do()` dispatch conventions (`int`, `list`, `"pandas"`, `"hide"`, etc.) are terse but must be learned -- they can't be discovered through autocomplete.

**Where duckboat fits best:**

Duckboat is ideal for interactive exploration and notebook workflows, especially for teams already fluent in SQL. If you need strong static analysis, IDE support, or production-grade type safety, a fluent API like [Polars](https://pola.rs/) or [Ibis](https://ibis-project.org/) may be a better fit. If some operation is easier in another library, duckboat makes it straightforward to translate between them via Pandas, Arrow, or Polars.

## Feedback

I'd love to hear any feedback on the approach here, so feel free to reach out through
[Issues](https://github.com/ajfriend/duckboat/issues)
or
[Discussions](https://github.com/ajfriend/duckboat/discussions).
