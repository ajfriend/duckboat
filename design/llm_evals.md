---
title: "Design: LLM Evals for duckboat"
date: 2026-03-25
toc: false
numbersections: false
---

# Motivation

duckboat is a thin composition layer over DuckDB. It encourages a pipe-style
workflow---chaining SQL snippets with `do()`---rather than writing monolithic
SQL queries or using pandas/polars method chains. This is a new interaction
pattern that LLMs have not been trained on.

Key questions:

- Can LLMs use duckboat effectively given its docs?
- Do they need an `llms.txt` or targeted context?
- How does duckboat compare to pandas, polars, raw DuckDB SQL, and raw SQL on
  the same tasks---from the LLM's perspective?
- Does duckboat's pipe-style composition lead to fewer errors, fewer retries, or
  shorter solutions when an LLM generates the code?


# What to Compare

The same data manipulation tasks, solved five ways:

1. **duckboat** --- `do()` chains with SQL snippets
2. **Raw DuckDB SQL** --- single monolithic queries via `duckdb.sql()`
3. **pandas** --- method chains and DataFrame operations
4. **polars** --- expression API and lazy frames
5. **Raw SQL (standard)** --- portable SQL without DuckDB extensions

duckboat and raw DuckDB are especially interesting to compare. Both use DuckDB
under the hood. The question is whether the `do()` composition style leads to
better LLM-generated code than writing full SQL queries directly.


# Task Suite

50--100 data manipulation tasks of increasing complexity:

## Tier 1: Single-table operations

- Filter rows (`where`)
- Select/rename columns
- Add computed columns
- Sort and limit
- Aggregation with `group by`
- Window functions

## Tier 2: Multi-step pipelines

- Filter, then aggregate, then sort
- Compute a column, then group by it
- Multiple aggregations at different granularities
- Deduplication and ranking

## Tier 3: Multi-table operations

- Inner/left/outer joins
- Self-joins
- Aggregation after join
- Multiple joins in sequence

## Tier 4: Real-world scenarios

- "Find the top 5 customers by total spend"
- "Compare this month's sales to last month's"
- "Find duplicate records across two tables"
- "Pivot long data to wide format"

Each task has:

- A natural language description
- Test data (small DataFrames or CSV/parquet files)
- Expected output
- Reference solutions in all five target libraries


# Metrics

## Primary

- **Pass rate:** does the generated code produce the correct output?
- **Retry count:** in an agentic loop (generate, run, see error, retry), how
  many turns to reach a correct solution?
- **Token usage:** total input + output tokens to solve the task. Measures cost
  and conciseness.

## Secondary

- **API hallucination rate:** how often does the LLM invent function or method
  names that do not exist in the library?
- **Solution length:** lines of code in the final correct solution.
- **Error categories:** what kinds of errors does the LLM make? Syntax errors,
  wrong column names, wrong API calls, logic errors?

## Documentation sensitivity

Run every task twice:

1. **Without docs:** LLM relies on training data only.
2. **With docs in context:** provide the library's documentation (or
   `llms.txt`).

The delta measures how much documentation helps. A large delta for duckboat
(compared to pandas) would indicate that duckboat is underrepresented in
training data but learnable from docs---which is the expected result for a
niche library.


# Eval Setup

## Framework

[Inspect AI](https://inspect.ai-safety-institute.org.uk/) is the best fit:

- Python-native task definitions with custom scoring
- Sandboxed code execution (Docker)
- Multiple LLM providers (Claude, GPT, Gemini, open-source)
- Solver pipelines (single-shot, chain-of-thought, agentic retry)

## Sandbox

Each eval run installs the target library in a Docker container with the test
data. The LLM generates code, it runs in the sandbox, and the output is compared
to the expected result.

## Models to test

- Claude Sonnet (latest)
- Claude Opus (latest)
- GPT-4o
- Gemini Pro
- At least one open-source model (Llama, Qwen, etc.)


# Hypotheses

1. **pandas will have the highest baseline pass rate** (without docs) because it
   dominates training data.
2. **duckboat will have a low baseline but high with-docs pass rate**, because
   the API is simple and learnable from a small amount of context.
3. **duckboat will have fewer retries than raw DuckDB SQL** for multi-step
   tasks, because errors are localized to individual steps (especially with
   step-index error messages).
4. **duckboat solutions will be shorter** than pandas or polars equivalents for
   the same tasks.
5. **Raw DuckDB SQL will struggle on multi-step pipelines** where LLMs tend to
   produce deeply nested subqueries that are hard to debug.
6. **polars will have a high hallucination rate** because its API is large,
   changing, and underrepresented relative to pandas.


# Providing Context to LLMs

## llms.txt

Create `ajfriend.com/duckboat/llms.txt` following the
[llms.txt convention](https://llmstxt.org/). This is a Markdown file with:

- H1 title and blockquote summary
- Sections with H2 headers linking to detailed docs
- Concise enough for an LLM to consume in a single context window

Also consider `llms-full.txt`---the complete docs in a single file for models
with large context windows.

## Targeted LLM guide

A short document (separate from user docs) that teaches the `do()` pattern with
examples. Optimized for LLM consumption: minimal prose, maximum code examples,
covering the common patterns (filter, aggregate, join, materialize).

## Eval-driven iteration

Use the eval results to identify where LLMs struggle and improve the docs
accordingly. If LLMs consistently fail at joins, add more join examples. If they
hallucinate `do()` arguments, clarify the dispatch rules. The eval suite becomes
a feedback loop for documentation quality.


# What Would Be Novel

No one has published a systematic comparison of LLM performance across data
libraries for the same task set. Specifically:

- **Library-LLM compatibility benchmarking** as a concept does not exist yet.
- **Token efficiency** as a metric for library design has not been studied.
- **Retry count** as a proxy for API ergonomics (from the LLM's perspective) is
  unexplored.
- **Documentation sensitivity** (performance delta with/without docs) as a
  measure of training data representation is intuitive but unpublished.

A paper or blog post titled something like "Which Python data library do LLMs
use best?" based on this eval suite would be genuinely novel and likely to get
attention.
