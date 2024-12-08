default:
      @just --list

init: purge
	python -m venv env
	env/bin/pip install --upgrade pip wheel setuptools
	just lib

lib:
	# env/bin/pip install -e .[all]
	env/bin/pip install .[all]

# uninstall darkwing and remove extranous files
clear:
	-env/bin/pip uninstall -y darkwing

	just _remove d '__pycache__'
	just _remove d '*.egg-info'
	just _remove d '*.ipynb_checkpoints'
	just _remove d 'output'

	just _remove f '*.DS_Store'
	just _remove f '*.pyc'

rebuild: clear lib

# remove env
purge:
	-rm -rf env
	just clear

test:
	env/bin/pytest

lab:
	env/bin/pip install jupyterlab
	env/bin/jupyter lab

render:
	source env/bin/activate; quarto render docs/

publish:
	source env/bin/activate; cd docs; quarto publish gh-pages

_remove type name:
    -@find . -type {{type}} -name {{name}} | xargs rm -r
