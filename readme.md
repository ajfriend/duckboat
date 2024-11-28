# Darkwing

Darkwing is a work-in-progress "dataframe library" that
I use in personal interactive data analysis projects.
(I use quotes because it's really just a light wrapper around the
[DuckDB relational API](https://duckdb.org/docs/api/python/relational_api).)

You can concatenate SQL snippets (often omitting `select *` and `from ...`) to incrementally build up complex queries.
Expressions are evaluated lazily and optimized by DuckDB, so queries are fast, without the need for intermediate tables or data transfers.

This approach results in a mixture of Python and SQL that, I think, is semantically very similar to
[Google's Pipe Syntax for SQL](https://research.google/pubs/sql-has-problems-we-can-fix-them-pipe-syntax-in-sql/):
We can leverage our existing knowledge of SQL, while making a few small changes to make it more ergonomic and composable.

When doing interactive data analysis, I find this approach easier to read and write than
fluent APIs (like in [Polars](https://pola.rs/) or [Ibis](https://ibis-project.org/)) or typical [Pandas](https://pandas.pydata.org/) code.
If some operation is easier in other libraries, Darking makes it straightforward translate between them, either directly or through Apache Arrow.

I'd love to hear any feedback on the approach here, so feel free to reach out through
[Issues](https://github.com/ajfriend/darkwing/issues)
or
[Discussions](https://github.com/ajfriend/darkwing/discussions).

## Installing

```shell
pip install git+https://github.com/ajfriend/darkwing
```

## Loading, saving, and transferring tables

```python
import darkwing as dw

# read from a remote CSV file
tbl = dw.Table('https://raw.githubusercontent.com/mcnakhaee/palmerpenguins/refs/heads/master/palmerpenguins/data/penguins.csv')
tbl = dw.Table('data/penguins.csv')  # read from a local CSV file

df = tbl.df()  # write to Pandas DataFrame
dw.Table(df)  # read from Pandas DataFrame

df.to_parquet('data/penguins.parquet')  # use Pandas to write to a Parquet file
tbl = dw.Table('data/penguins.parquet')  # read from a local Parquet file

tbl_arrow = tbl.arrow()  # write to an  Arrow Table
tbl = dw.Table(tbl_arrow)  # read from an Arrow Table
```


## Databases and Tables

The library revolves around two objects and a function: `Database`, `Table`.

- `Database` is essentially a dictionary mapping names to objects that will get resolved to tables. Those objects might be a Pandas or Polars dataframe, a PyArrow Table, the local filename of a Parquet or CSV file, or a URL to a remote data file. These objects are used by `darkwing` and Duckdb lazily, so operations on them are deffered until a final result is requested.
- `Table` is a wrapper around a DuckDB Relation.


## Laziness

Since all operations are done through `DuckDBPyRelation`, the expressions are evaluated lazily, or only at the end when we want a table or want to display results to the console.

If you would like to materialze a `Table` or a `Database` concretely in terms of Pandas DataFrames or PyArrow Tables, you can use `x.hold(kind='arrow')` or ` x.do('arrow')`.

When you materialize a `Database` you can access the underlying tables with `db[table_name]`.

## Examples

### Chaining

`darkwing` uses DuckDB to build up Relation expressions through chaining, which DuckDB
will then execute after running the entire expression through a query planner to optimize
execution.

```python
import darkwing as dw

# dw.Table('https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2010-01.parquet')
dw.Table('yellow_tripdata_2010-01.parquet').do(
    'select *, pickup_latitude as lat, pickup_longitude as lng',
    'select *, h3_latlng_to_cell(lat, lng, 8) as hexid',
    'select hexid, avg(tip_amount) as tip  group by 1',
    'select h3_h3_to_string(hexid) as hexid, tip',
    'where tip between 10 and 20',
    'order by hexid',
)
```

Gives the output:

```
┌─────────────────┬────────────────────┐
│      hexid      │        tip         │
│     varchar     │       double       │
├─────────────────┼────────────────────┤
│ 881bb2a0b5fffff │              12.22 │
│ 882a100299fffff │  10.02818181818182 │
│ 882a10029dfffff │ 11.666666666666666 │
│ 882a1002c3fffff │               10.0 │
│ 882a10034bfffff │               16.0 │
│ 882a100353fffff │               17.6 │
│ 882a10045bfffff │               10.0 │
│ 882a100487fffff │             11.525 │
│ 882a10060dfffff │               16.1 │
│ 882a100611fffff │               10.0 │
│        ·        │                 ·  │
│        ·        │                 ·  │
│        ·        │                 ·  │
│ 882a13c4d9fffff │               11.5 │
│ 882a13d281fffff │               20.0 │
│ 882a13d529fffff │               15.0 │
│ 882a1438c3fffff │               10.0 │
│ 882a15663bfffff │               10.0 │
│ 882a1ab9c1fffff │              10.01 │
│ 882a353927fffff │              11.05 │
│ 882aa16327fffff │              12.51 │
│ 882aaab9ebfffff │              10.01 │
│ 882ad09327fffff │              12.51 │
├─────────────────┴────────────────────┤
│ 193 rows (20 shown)        2 columns │
└──────────────────────────────────────┘
```

#### Alternatives

You can also write the above as

```python
dw.Table('data/yellow_tripdata_2010-01.parquet').do(
    'select *, pickup_latitude as lat, pickup_longitude as lng',
    'select *, h3_latlng_to_cell(lat, lng, 8) as hexid',
    'select hexid, avg(tip_amount) as tip  group by 1',
    'select h3_h3_to_string(hexid) as hexid, tip',
    'where tip between 10 and 20',
    'order by hexid',
)
```

or

```python
dw.Table('data/yellow_tripdata_2010-01.parquet').do(
    'select *, pickup_latitude as lat, pickup_longitude as lng',
).do(
    'select *, h3_latlng_to_cell(lat, lng, 8) as hexid',
).do(
    'select hexid, avg(tip_amount) as tip  group by 1',
).do(
    'select h3_h3_to_string(hexid) as hexid, tip',
).do(
   'where tip between 10 and 20',
).do(
    'order by hexid',
)
```

### Pivot

TODO

### Storing procedures

You might store a sequence of steps as a function like

```python
def foo(rel, res=6):
    return (rel
    | 'select pickup_latitude as lat, pickup_longitude as lng, tip_amount'       
    | f'select h3_latlng_to_cell(lat, lng, {res}) as hexid, tip_amount as tip'
    | 'select hexid, avg(tip) as tip group by 1'
    | 'select h3_h3_to_string(hexid) as hexid, tip'
    | 'where tip > 0'
    )
```

which you could apply with any of the following syntax:

- `table.do(foo)`
- `table | foo` or `table >> foo`

Alternatively, you could store this as a sequence of strings:

```python
foo_list = [
    'select pickup_latitude as lat, pickup_longitude as lng, tip_amount'       
    'select h3_latlng_to_cell(lat, lng, 6}) as hexid, tip_amount as tip'
    'select hexid, avg(tip) as tip group by 1'
    'select h3_h3_to_string(hexid) as hexid, tip'
    'where tip > 0'
]
```

which you could apply with something like

```python
table.do(*foo_list)
```

or

```python
table.do(foo_list)
```

or even

```python
table | foo_list
```

# Notes

TODO: you can mix in functions with string lists!
TODO: can we also allow for mixing in pandas/polars/ibis code? maybe a function wrapper? That would be crazy powerful!


# Notes

TOOD: drop the binary operator stuff, and just use the functional API
`as` to `alias`

(Think this is mostly done now.)


# Old

## Piping

You can use both `|` and `>>` to pipe SQL snippets and some other operations.
Be careful When mixing `|` and `>>`, and note the operator precedence rules.
Note you can always use parenthesis to specify evaluation order, or build up expressions in a fluent style like `a.sql(s1).sql(s2)`.

these are equivalent to `.do()`, which can also take in a multiple arguments.

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

## References

- [PRQL](https://prql-lang.org/)
- [DuckDB's SQL improvements](https://duckdb.org/2022/05/04/friendlier-sql.html)


## What's different from DuckDB's relational api

- avoid connection objects