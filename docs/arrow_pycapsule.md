---
title: "The Arrow PyCapsule Interface: __arrow_c_stream__"
date: 2026-03-25
toc: false
numbersections: false
---

# What Problem Does It Solve?

The Python data ecosystem has many DataFrame libraries---pandas, Polars,
PyArrow, DuckDB, cuDF---and passing tabular data between them has always been
awkward. Each library has its own types, and converting between them meant
copies, wrappers, or library-specific glue code.

The [Data APIs Consortium](https://data-apis.org/) tried to solve this with the
`__dataframe__` interchange protocol around 2022. It never quite worked: the
implementation had
[critical bugs](https://github.com/pandas-dev/pandas/issues/57643) with
nullable PyArrow dtypes, the spec was complex, and the consortium repo went
dormant by late 2023.

The [Arrow PyCapsule Interface](https://arrow.apache.org/docs/format/CDataInterface/PyCapsuleInterface.html)
replaced it. It is simpler, truly zero-copy, and now universally adopted. It is
the standard way for a Python object to say "I am tabular data---consume me."


# The Three Dunder Methods

The interface defines three methods. For dataframe interchange,
`__arrow_c_stream__` is the one that matters.

| Method               | Returns                                 | Use case                                   |
|----------------------|-----------------------------------------|--------------------------------------------|
| `__arrow_c_stream__` | PyCapsule (ArrowArrayStream pointer)    | Tabular data: dataframes, record batches   |
| `__arrow_c_array__`  | Tuple of two PyCapsules (schema, array) | A single array or record batch (one chunk) |
| `__arrow_c_schema__` | PyCapsule (ArrowSchema pointer)         | Schema/type information only               |

All three accept an optional `requested_schema` parameter that lets the consumer
request a specific type or schema, enabling negotiation between producer and
consumer.


# How It Works Under the Hood

The [Arrow C Data Interface](https://arrow.apache.org/docs/format/CDataInterface.html)
defines C structs---`ArrowArrayStream`, `ArrowArray`, `ArrowSchema`---for
sharing columnar data across language boundaries. These structs describe memory
layout, types, and ownership without copying data.

Python's `PyCapsule` is a built-in type that wraps a raw C pointer so it can be
passed between Python objects. When a library calls `obj.__arrow_c_stream__()`,
it gets back a PyCapsule containing a pointer to an `ArrowArrayStream`. The
consuming library unwraps the capsule and reads directly from that memory---no
copying, no intermediate Python objects, no serialization.

The flow:

1. **Producer** exposes `__arrow_c_stream__()`, which returns a PyCapsule.
2. **Consumer** calls something like `pa.RecordBatchReader.from_stream(obj)` or
   `pl.from_arrow(obj)`, which internally calls `__arrow_c_stream__()`.
3. Data stays in memory exactly where it is. The PyCapsule is just a handle.


# Who Implements It

As of 2026, the major libraries all support the PyCapsule interface:

| Library             | Version  | Produces                        | Consumes |
|---------------------|----------|---------------------------------|----------|
| PyArrow             | >= 14.0  | Table, RecordBatchReader, Array | Yes      |
| Polars              | >= 0.20  | DataFrame, Series               | Yes      |
| DuckDB              | >= 0.10  | Query results, relations        | Yes      |
| cuDF (RAPIDS)       | >= 24.02 | DataFrame, Series               | Yes      |
| pandas              | >= 2.1   | Via ArrowDtype backend          | Yes      |
| nanoarrow           | >= 0.1   | Full support                    | Yes      |
| ADBC drivers        | Various  | Query results                   | Yes      |
| DataFusion (Python) | Various  | Query results                   | Yes      |


# Practical Usage

## Producing: exporting data

Any object with `__arrow_c_stream__` can be consumed by any Arrow-aware library:

```python
import polars as pl
import pyarrow as pa

# Polars DataFrame -> PyArrow Table (zero-copy via PyCapsule)
df = pl.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
table = pa.RecordBatchReader.from_stream(df).read_all()
```

## Consuming: importing data

Libraries that accept Arrow data call `__arrow_c_stream__` automatically:

```python
# PyArrow Table -> Polars (zero-copy)
arrow_table = pa.table({"a": [1, 2, 3]})
df = pl.from_arrow(arrow_table)

# Any __arrow_c_stream__ object -> DuckDB
import duckdb
result = duckdb.sql("SELECT * FROM df")
```

## Duck-typing check

To test whether an object is tabular data that speaks Arrow:

```python
def is_tabular(obj):
    return hasattr(obj, '__arrow_c_stream__')
```

No need to check `isinstance` for pandas, Polars, or PyArrow separately.
Anything that speaks Arrow will have this method.


# How It Replaced `__dataframe__`

The `__dataframe__` protocol was designed to be Arrow-agnostic, supporting
non-Arrow memory layouts. In theory this was more general. In practice, Arrow
won as the universal in-memory columnar format, and the generality became
unnecessary complexity.

The timeline:

- **2022:** `__dataframe__` interchange protocol introduced. Adopted by pandas
  1.5, Polars, Vaex, cuDF.
- **Late 2023:** Arrow PyCapsule interface ships in PyArrow 14.0. Rapid
  adoption across the ecosystem.
- **Dec 2023:** Last substantive commit to the
  [Data APIs Consortium repo](https://github.com/data-apis/dataframe-api).
- **Jan 2025:** cuDF
  [fully removes](https://github.com/rapidsai/cudf/issues/17403)
  `__dataframe__` support.
- **Jan 2026:** pandas 3.0
  [officially deprecates](https://github.com/pandas-dev/pandas/pull/62920)
  `__dataframe__`, pointing users to PyCapsule.
- **Mar 2026:** Polars has
  [deprecation on its roadmap](https://github.com/pola-rs/polars/issues/20065).

The PyCapsule interface won because it is simpler (C pointers, no Python-level
buffer protocol), faster (true zero-copy), and backed by the format that
everything already uses internally.


# Why This Matters for Library Authors

If you are building a library that accepts tabular data from users, check for
`__arrow_c_stream__`. It is the universal "I am a table" signal. DuckDB can
consume any object that implements it directly---no conversion code needed on
your end.

```python
import duckdb

def query(sql, **tables):
    con = duckdb.connect()
    for name, obj in tables.items():
        con.register(name, obj)
    return con.sql(sql)

# Works with pandas, Polars, PyArrow, cuDF, or anything else
# that implements __arrow_c_stream__
result = query(
    "SELECT * FROM orders JOIN customers USING (id)",
    orders=polars_df,
    customers=pandas_df,
)
```

You write the registration logic once. The Arrow PyCapsule interface handles the
rest.
