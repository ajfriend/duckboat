# Dev Notes

## Publishing a release

1. Update version in `pyproject.toml` and `changelog.md`
2. Merge PR to `main`
3. Create a GitHub release at https://github.com/ajfriend/duckboat/releases/new
   - Tag: `v0.18.0` (matching the version in `pyproject.toml`)
   - Title: `v0.18.0`
   - Description: copy from `changelog.md`
4. The `build` workflow builds the package and publishes to PyPI automatically

## Running tests locally

```
just test
```

## Linting

```
just lint
just fix   # auto-fix
```

## Publishing docs

```
just publish
```

This renders the Quarto docs and pushes to the `gh-pages` branch, which deploys to https://ajfriend.com/duckboat/.

Note: `tut_nyc_join.qmd` executes Python code against large parquet files in `docs/data/` (gitignored, ~1.4GB). You need those files locally for the tutorial to render.
