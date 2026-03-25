default:
      @just --list

# remove extranous files
clear:
	just _remove d '__pycache__'
	just _remove d '*.egg-info'
	just _remove d '*.ipynb_checkpoints'
	just _remove d '.pytest_cache'

	just _remove d 'docs_output'
	just _remove d 'site_libs'
	just _remove d '.quarto'
	just _remove f '*.quarto_ipynb'

	just _remove f '*.DS_Store'
	just _remove f '*.pyc'
	just _remove f '.coverage'

# remove venv
purge:
	-rm -rf .venv
	just clear

test:
	uv run pytest

lab:
	uv run jupyter lab

render:
	uv run quarto render docs/
	open docs_output/index.html

publish:
	cd docs && uv run quarto publish gh-pages

_remove type name:
    -@find . -type {{type}} -name {{name}} | xargs rm -r

lint:
	uv run ruff check

fix:
	uv run ruff check --fix
