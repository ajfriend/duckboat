init: purge
	python -m venv env
	env/bin/pip install --upgrade pip wheel setuptools
	just lib

lib:
	# env/bin/pip install -e .[all]
	env/bin/pip install .[all]

clear:
	-env/bin/pip uninstall -y darkwing

	just remove d '__pycache__'
	just remove d '*.egg-info'
	just remove d '*.ipynb_checkpoints'
	just remove d 'output'

	just remove f '*.DS_Store'
	just remove f '*.pyc'

rebuild: clear lib



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

remove type name:
    -@find . -type {{type}} -name {{name}} | xargs rm -r
