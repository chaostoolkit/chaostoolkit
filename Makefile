.PHONY: install
install:
	pip install --no-cache-dir --upgrade pip setuptools wheel
	pip install --no-cache-dir --upgrade -r requirements.txt

.PHONY: install-dev
install-dev: install
	pip install --no-cache-dir --upgrade -r requirements-dev.txt
	pip install --no-cache-dir --upgrade -e .

.PHONY: build
build:
	python3 setup.py build

.PHONY: lint
lint:
	ruff chaostoolkit/ tests/
	isort --check-only --profile black chaostoolkit/ tests/
	black --check --diff chaostoolkit/ tests/

.PHONY: format
format:
	isort --profile black chaostoolkit/ tests/
	black chaostoolkit/ tests/
	ruff chaostoolkit/ tests/ --fix

.PHONY: tests
tests:
	pytest -s
