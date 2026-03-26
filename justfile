export UV_NO_EDITABLE := "1"
export UV_OFFLINE := "0"

_:
    @just --list

clean:
    just _rm '__pycache__'
    just _rm '*.egg-info'
    just _rm '*.ipynb_checkpoints'
    just _rm '.pytest_cache'
    just _rm 'docs_output'
    just _rm 'site_libs'
    just _rm '.quarto'
    just _rm '*.quarto_ipynb'
    just _rm '*.DS_Store'
    just _rm '*.pyc'
    just _rm '.coverage'
    just _rm '.ruff_cache'
    just _rm 'uv.lock'

purge: clean
    -rm -rf .venv
    just _rm '.claude'


_rm pattern:
    -@find . -name "{{pattern}}" -prune -exec rm -rf {} +

reinstall:
    uv sync --reinstall-package duckboat

test: reinstall
    uv run pytest

lint:
    uv run ruff check

fix:
    uv run ruff check --fix

[group('extra')]
lab: reinstall
    uv run jupyter lab


[group('docs')]
render: reinstall
    uv run quarto render docs/
    open docs_output/index.html

[group('docs')]
publish: reinstall
    cd docs && uv run quarto publish gh-pages


