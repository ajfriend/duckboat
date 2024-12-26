# Duckboat

[ajfriend.github.io/duckboat](https://ajfriend.github.io/duckboat/) | [github.com/ajfriend/duckboat](https://github.com/ajfriend/duckboat)

*Unsightly to some, but gets the job done.*

Duckboat is a SQL-based Python dataframe library for ergonomic interactive
data analysis and exploration.


```python
pip install git+https://github.com/ajfriend/duckboat
```

Duckboat allows you to chain SQL snippets (often omitting `select *` and `from ...`)
to incrementally and lazily build up complex queries.

Duckboat is a light wrapper around the
[DuckDB relational API](https://duckdb.org/docs/api/python/relational_api),
which is easily accessible if you'd like to use DuckDB more directly.
Expressions are evaluated lazily and optimized by DuckDB,
so queries are fast, avoiding materializing intermediate tables and data transfers.


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
