# Darkwing

Darkwing is an experimental data-wrangling library built on DuckDB, enabling lazy pipelining of SQL snippets into larger analytical transformations.

I write a lot of SQL and Python to do data analysis. I find SQL easy to write, but it can be verbose and hard to compose.
Python dataframe libraries are natural because I'm usually already working in Python, but I often need to look up specific synatax
and the resulting code can be awkward.
I liked the composability of
[PRQL](https://prql-lang.org/) and
[Google's Pipe Syntax for SQL](https://research.google/pubs/sql-has-problems-we-can-fix-them-pipe-syntax-in-sql/),
and especially that the latter reused the SQL syntax I was already fluent in.
DuckDB is an incredibly powerful tool with [its own SQL improvements](https://duckdb.org/2022/05/04/friendlier-sql.html) that I was already using,
but with some undesireable boilerplate when you're
focused on analytical transformations of data frames.
However, a few tweaks can bring the best of all of these together, which is why `darkwing` is not much more than a small, lightweight wrapper around DuckDB that, for me, makes interactive data analysis a little more ergonomic.

## Databases and Tables

The library revolves around two objects and a function: `Database`, `Table`.

- `Database` is essentially a dictionary mapping names to objects that will get resolved to tables. Those objects might be a Pandas or Polars dataframe, a PyArrow Table, the local filename of a Parquet or CSV file, or a URL to a remote data file. These objects are used by `darkwing` and Duckdb lazily, so operations on them are deffered until a final result is requested.
- `Table` is a wrapper around a DuckDB Relation.


## Piping

You can use both `|` and `>>` to pipe SQL snippets and some other operations.
Be careful When mixing `|` and `>>`, and note the operator precedence rules.
Note you can always use parenthesis to specify evaluation order, or build up expressions in a fluent style like `a.sql(s1).sql(s2)`.

For example:

- `a | b` maps to `a.sql(b)` when `a` is a `Database` or `Table` and `b` is a query string
- `a >> f` resolves to `f(a)` if `f` is a callable

In the "use whichever form is most horrifying to your peers" syntax category, we have:
- `'filename.parquet' >> dw.Table` is the same as `dw.Table('filename.parquet')`. 
- `a >> 'as table_name'` resolves to a `Database(table_name = a)`
- `a >> list`
- `a >> dict`
- `a >> int`
- `a >> float`
- `a >> str`
- `a >> bool`
- `a >> pd.DataFrame`

## Laziness

Since all operations are done through `DuckDBPyRelation`, the expressions are evaluated lazily, or only at the end when we want a table or want to display results to the console.

If you would like to materialze a `Table` or a `Database` concretely in terms of Pandas DataFrames or PyArrow Tables, you can use `x.hold(kind='arrow')` or ` x >> 'arrow'`.

When you materialize a `Database` you can access the underlying tables with `db[table_name]`.

## Examples

TODO