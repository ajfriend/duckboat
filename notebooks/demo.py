# /// script
# requires-python = '>=3.10'
# dependencies = [
#     'marimo',
#     'duckboat',
# ]
# ///

import marimo

__generated_with = "0.21.1"
app = marimo.App()


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell
def _(mo):
    mo.md("""
    # Duckboat Demo

    *Ugly to some, but gets the job done.*

    Chain SQL snippets into composable data pipelines with DuckDB.
    """)
    return


@app.cell
def _():
    import duckboat as uck

    return (uck,)


@app.cell
def _(mo):
    mo.md("""
    ## Chaining SQL snippets

    Each step takes the previous result as input. `from _` is prepended automatically.
    """)
    return


@app.cell
def _(uck):
    penguins = uck.examples.penguins()
    penguins
    return (penguins,)


@app.cell
def _(penguins):
    penguins.do(
        "where sex = 'female'",
        'where body_mass_g is not null',
        'select species, island, avg(body_mass_g) as avg_mass group by 1, 2',
        'select * replace (round(avg_mass, 1) as avg_mass)',
        'order by avg_mass',
    )
    return


@app.cell
def _(mo):
    mo.md("""
    ## Materializing results

    Extract scalars, lists, or DataFrames.
    """)
    return


@app.cell
def _(penguins):
    penguins.do('select count(*)', int)
    return


@app.cell
def _(penguins):
    penguins.do('select distinct species', list)
    return


@app.cell
def _(mo):
    mo.md("""
    ## Joins

    Pass a dict to register named tables.
    """)
    return


@app.cell
def _(uck):
    store = uck.examples.store()

    uck.do(
        store,
        'select name, sum(amount) as total from orders join customers on customer_id = customers.id group by 1',
        'order by total desc',
        'limit 5',
    )
    return


@app.cell
def _(mo):
    mo.md("""
    ## Self-joins

    The current table is always available as `_`.
    """)
    return


@app.cell
def _(penguins, uck):
    penguins.do(
        'select distinct species',
        uck.rename('sp'),
        'select a.species as sp1, b.species as sp2 from sp a cross join sp b where a.species < b.species',
    )
    return


@app.cell
def _(mo):
    mo.md("""
    ## Reusable fragments

    Store pipeline steps as lists.
    """)
    return


@app.cell
def _(penguins):
    clean = [
        'where body_mass_g is not null',
        'where sex is not null',
    ]

    summarize = [
        'select species, sex, avg(body_mass_g) as avg_mass group by 1, 2',
        'select * replace (round(avg_mass, 1) as avg_mass)',
        'order by species, sex',
    ]

    penguins.do(clean, summarize)
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
