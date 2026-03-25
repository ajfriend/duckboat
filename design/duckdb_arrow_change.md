---
title: "DuckDB's Arrow API Change: RecordBatchReader"
date: 2026-03-25
toc: false
numbersections: false
---

# What is RecordBatchReader?

`RecordBatchReader` is a **PyArrow type** (`pyarrow.RecordBatchReader`), not a
DuckDB type. It is a streaming interface---a lazy iterator that yields
`pyarrow.RecordBatch` objects one at a time. Data is not materialized until you
explicitly consume it.

Key methods:

- `read_all()`: consumes the entire stream and returns a `pyarrow.Table`
- `read_next_batch()`: returns the next `RecordBatch`; raises `StopIteration` at end
- `schema`: property returning the shared schema of the stream


# PyArrow's Type Hierarchy

| Type                | Description                                          | Memory Model                             |
|---------------------|------------------------------------------------------|------------------------------------------|
| `RecordBatch`       | A single contiguous chunk of columnar data           | Fully materialized, single chunk         |
| `Table`             | A logical table of one or more `RecordBatch` chunks  | Fully materialized, possibly multi-chunk |
| `RecordBatchReader` | A streaming iterator yielding `RecordBatch`es lazily | Lazy/streaming, one batch at a time      |

A `Table` is like a list of `RecordBatch`es glued together. A
`RecordBatchReader` is a generator that produces them lazily.


# What Changed in DuckDB

DuckDB's `.arrow()` method historically returned a `pyarrow.Table`.
[PR #18642](https://github.com/duckdb/duckdb/pull/18642) (by Pedro Holanda,
merged Aug 19, 2025) changed it to return a `pyarrow.RecordBatchReader`. This
shipped in **DuckDB 1.4.0** (Sep 16, 2025).

## Motivation

From the PR description:

> "Users mostly want to interact with arrow in a streaming fashion. This is
> especially important to avoid OOM of naively calling `arrow()`."

The core reasons:

- **Memory efficiency:** users would call `.arrow()` on large datasets,
  materializing everything into memory and getting OOM errors.
  `RecordBatchReader` streams data in batches.
- **Streaming-first philosophy:** DuckDB's Arrow integration is designed around
  zero-copy streaming. Returning a reader aligns with this.
- **Dedicated alternatives exist:** `fetch_arrow_table()` was already available
  for users who explicitly wanted full materialization.

## DuckDB 1.5.0 API Cleanup (Mar 9, 2026)

The change was a breaking change that was not well documented initially, causing
significant user confusion
([#71](https://github.com/duckdb/duckdb-python/issues/71),
[#85](https://github.com/duckdb/duckdb-python/issues/85),
[#95](https://github.com/duckdb/duckdb-python/issues/95) in duckdb-python).

DuckDB 1.5.0 cleaned up the API:

- `to_arrow_reader()` -> `RecordBatchReader` (new, preferred)
- `to_arrow_table()` -> `Table` (new, preferred)
- `arrow()` -> `RecordBatchReader` (kept but discouraged)
- Deprecated: `fetch_record_batch()`, `fetch_arrow_table()`, `fetch_arrow_reader()`


# Why This Causes Problems

## One-shot consumption

A `RecordBatchReader` is **single-use**. Once you have read from it, the stream
is exhausted. You cannot rewind or re-read. If you pass a `RecordBatchReader` to
DuckDB as input (e.g., `SELECT * FROM reader`), DuckDB will consume it. Any
subsequent query against it finds an empty stream.

## Deadlocks

When DuckDB returns a `RecordBatchReader`, it holds a **streaming query** on
that connection. The reader is backed by a `StreamQueryResult` which starts an
execution pipeline that blocks until batches are consumed.

If you then try to execute a new query on the **same connection** that scans
that `RecordBatchReader`, two things happen:

1. The new query needs the `ClientContextLock` to execute.
2. The `RecordBatchReader`'s `GetNextChunk` also needs the `ClientContextLock`
   to produce data.

This creates a deadlock: the new query holds the lock waiting for data from
the reader, while the reader needs the lock to produce data. This was documented
in [duckdb-python #85](https://github.com/duckdb/duckdb-python/issues/85),
where stack traces showed two threads deadlocked on
`ResultArrowArrayStreamWrapper::MyStreamGetNext` and
`ArrowArrayStreamWrapper::GetNextChunk`.

## Workarounds

1. **Materialize first:** call `.read_all()` to consume the reader into a
   `Table` before passing it back to DuckDB.
2. **Use `to_arrow_table()`** (1.5.0+) to get a `Table` directly, bypassing
   the `RecordBatchReader` entirely.
3. **Use separate connections** if streaming is needed.


# Version Timeline

| Version   | Date             | `.arrow()` returns                               |
|-----------|------------------|--------------------------------------------------|
| <= 1.3    | through May 2025 | `pyarrow.Table`                                  |
| **1.4.0** | **Sep 16, 2025** | **`RecordBatchReader`** (breaking change)        |
| **1.5.0** | **Mar 9, 2026**  | `RecordBatchReader` + new `to_arrow_table()` API |


# Converting Between Types

```python
# RecordBatchReader -> Table (consumes the stream)
table = reader.read_all()

# Table -> RecordBatchReader (zero-copy)
reader = table.to_reader()

# Table -> list of RecordBatches
batches = table.to_batches()

# list of RecordBatches -> Table
table = pa.Table.from_batches(batches)
```
