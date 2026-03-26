---
title: "Design: Error Messages in do() Chains"
date: 2026-03-25
toc: false
numbersections: false
---

# The Problem

A `do()` chain can have many steps:

```python
t.do(
    'where total > 0',
    'select *, pickup_zone_id as zid',
    {'zones': zones_df},
    'join zones on zid = zones.id',
    'select zone_name, avg(total) group by 1',
    'order by 2 desc',
)
```

When step 3 fails (maybe `zones_df` has the wrong schema), the user sees a raw
DuckDB error with no indication of which step in the chain caused it. They have
to manually bisect the chain to find the failing step.


# Proposal: Step Index in Error Messages

Wrap `do_one()` calls in the `_do()` loop with a try/except that adds the step
index and the failing argument to the error:

```python
def _do(A, *xs):
    for i, x in enumerate(xs):
        try:
            A = do_one(A, x)
        except Exception as e:
            raise type(e)(
                f'do() failed at step {i}: {_repr_step(x)}\n{e}'
            ) from e
    return A
```

Instead of a bare DuckDB error, the user sees:

```
do() failed at step 3: 'join zones on zid = zones.id'
Catalog Error: Table with name zones does not exist!
```

This immediately answers "which step broke?" and "what was the step?"


# Additional Ideas

## Truncate long SQL

If the step is a multi-line SQL string, show just the first line in the error so
it does not overwhelm:

```python
def _repr_step(x):
    r = repr(x)
    if len(r) > 80:
        return r[:77] + '...'
    return r
```

## Hint at the prefix property

The error message could remind the user that they can inspect the intermediate
result by evaluating the chain up to the failing step:

```
do() failed at step 3: 'join zones on zid = zones.id'
Hint: inspect the intermediate result with t.do(*steps[:3])
```

This might be too verbose. The step index alone is usually enough for a notebook
user to manually trim the chain.

## Preserve the original traceback

Use `from e` (exception chaining) so the full DuckDB error and stack trace
remain visible. The step context is added information, not a replacement for the
original error.

## pytest integration

Setting `__tracebackhide__ = True` on the `_do()` and `do_one()` wrapper frames
makes pytest skip the library internals and show the user's test code directly.
A small quality-of-life improvement for test output.


# Recommendation

Start with the step index in error messages. It is a few lines of code, answers
the most common debugging question ("which step broke?"), and does not obscure
the original error. The other ideas are nice-to-have but not essential for a
first pass.
