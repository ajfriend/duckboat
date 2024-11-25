# Darkwing

statelessly duckdb different kinds of tables with affordances to make it as ergonomic as possible with minimal boilerplate.


```shell
pip install git+https://github.com/ajfriend/darkwing
```

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