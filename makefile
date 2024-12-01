init: purge
	python -m venv env
	env/bin/pip install --upgrade pip wheel setuptools
	make lib

lib:
	env/bin/pip install -e .[all]

clear:
	-@env/bin/pip uninstall -y darkwing
	-@rm -rf MANIFEST
	-@rm -rf .pytest_cache tests/__pycache__ __pycache__ _skbuild dist .coverage
	-@find . -type d -name '*.egg-info' | xargs rm -r
	-@find . -type f -name '*.pyc' | xargs rm -r
	-@find . -type d -name '*.ipynb_checkpoints' | xargs rm -r
	-@find ./tests -type f -name '*.c' | xargs rm -r

rebuild:
	make clear
	make lib

purge:
	-@rm -rf env
	make clear

test:
	env/bin/pytest

lab:
	env/bin/pip install jupyterlab
	env/bin/jupyter lab

render:
	source env/bin/activate; quarto render docs/
