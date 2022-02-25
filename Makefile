.PHONY: install
install:
	pip install --upgrade pip setuptools wheel
	pip install -r requirements.txt

.PHONY: install-dev
install-dev: install
	pip install -r requirements-dev.txt
	pip install -e .

.PHONY: build
build:
	python3 setup.py build

.PHONY: lint
lint:
	flake8 chaostoolkit/ tests/
	isort --check-only --profile black chaostoolkit/ tests/
	black --check --diff chaostoolkit/ tests/

.PHONY: format
format:
	isort --profile black chaostoolkit/ tests/
	black chaostoolkit/ tests/

.PHONY: tests
tests:
	pytest -s
