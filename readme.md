# Duckboat

*Ugly to some, but gets the job done.*

[GitHub](https://github.com/ajfriend/duckboat) | [Docs](https://ajfriend.github.io/duckboat/) | [PyPI](https://pypi.org/project/duckboat/)

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

csv = 'https://raw.githubusercontent.com/allisonhorst/palmerpenguins/main/inst/extdata/penguins.csv'

uck.Table(csv).do(
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
t = uck.Table(df)
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

Translate back to a pandas dataframe with any of the following:

```python
t.df()
t.hold('pandas')
t.do('pandas')
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
t.do([foo, f])
```


### Databases and joins

TODO

### Extravagant affordances

TODO


### Objects

(probably in the docstrings, rather than the readme)

#### Table

The core functionality comes from `.sql`, where we allow snippets.
"Shell" functionality comes from the `duckboat.do()` method, allowing for things like...

#### Database

The core functionality comes from the `.sql`, which loads *only* the Tables listed. No other Python objects are loaded.
A full duckdb sql expression is expected here, with table names provided explicitly.

"Shell" functionality comes from the `duckboat.do()` function/method, allowing for things like...


#### eager

The duckboat library makes some efforts to protect against unintentionally evaluating expressions eagerly, rather
than letting them rest lazily. For example, calling the `__repr__` method on a `Table` or `Database` will
trigger an evaluation of that object, which could include pulling a large table, or showing a large intermediate result.

in `ipython` or `jupyterlab`, we can typically avoid this by not ending a cell with an object. doing so
triggers the objects `__repr__`. However, these tactics don't work when using an IDE like Positron,
which eagerly inspects objects in the namespace to provide insight into what you're working with. This is often useful,
but not always what you want when working with large datasets or expensive computations.

## Philosophy

This approach results in a mixture of Python and SQL that, I think, is semantically very similar to
[Google's Pipe Syntax for SQL](https://research.google/pubs/sql-has-problems-we-can-fix-them-pipe-syntax-in-sql/):
We can leverage our existing knowledge of SQL, while making a few small changes to make it more ergonomic and composable.

When doing interactive data analysis, I find this approach easier to read and write than
fluent APIs (like in [Polars](https://pola.rs/) or [Ibis](https://ibis-project.org/)) or typical [Pandas](https://pandas.pydata.org/) code.
If some operation is easier in other libraries, Duckboat makes it straightforward translate between them, either directly or through Apache Arrow.

## Feedback

I'd love to hear any feedback on the approach here, so feel free to reach out through
[Issues](https://github.com/ajfriend/duckboat/issues)
or
[Discussions](https://github.com/ajfriend/duckboat/discussions).
