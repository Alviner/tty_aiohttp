
PROJECT_PATH := tty_aiohttp

VERSION = $(shell uv version --short)

CI_REGISTRY ?= ghcr.io
CI_PROJECT_NAMESPACE ?= alviner
CI_PROJECT_NAME ?= $(shell echo $(PROJECT_PATH) | tr -cd "[:alnum:]")
CI_REGISTRY_IMAGE ?= $(CI_REGISTRY)/$(CI_PROJECT_NAMESPACE)/$(CI_PROJECT_NAME)
DOCKER_TAG = $(shell echo $(VERSION) | tr '+' '-')

all:
	@echo "make build          - Build a docker image"
	@echo "make lint           - Syntax check python with ruff and mypy"
	@echo "make pytest         - Test this project"
	@echo "make format         - Format project with ruff"
	@echo "make upload         - Upload this project to the docker-registry"
	@echo "make clean          - Remove files which creates by distutils"
	@echo "make purge          - Complete cleanup the project"
	@exit 0

static:
	yarn build

wheel:
	uv build --wheel

build: clean wheel
	docker build -t $(CI_REGISTRY_IMAGE):$(DOCKER_TAG) --target release .

clean:
	rm -fr dist

clean-pyc:
	find . -iname '*.pyc' -delete

lint:
	uv run mypy $(PROJECT_PATH)
	uv run ruff check $(PROJECT_PATH) tests

format:
	uv run ruff format $(PROJECT_PATH) tests

purge: clean
	rm -rf ./.venv

pytest:
	uv run pytest

pytest-ci:
	uv run pytest -v --cov $(PROJECT_PATH) --cov-report term-missing --disable-warnings --junitxml=report.xml
	uv run coverage xml

upload: build
	docker push $(CI_REGISTRY_IMAGE):$(DOCKER_TAG)

develop: clean
	uv --version
	uv sync
	yarn install
