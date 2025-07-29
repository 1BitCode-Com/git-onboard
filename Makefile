.PHONY: help install test clean build publish

help: ## Show this help message
	@echo "Git Onboard - Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install the package
	pip install -e .

test: ## Run tests
	python3 git_onboard.py test
	python3 -m pytest tests/ -v

clean: ## Clean up build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

build: clean ## Build the package
	python3 setup.py sdist bdist_wheel

publish: build ## Publish to PyPI (requires twine)
	twine upload dist/*

format: ## Format code with black
	black git_onboard.py tests/

lint: ## Lint code with flake8
	flake8 git_onboard.py tests/

check: format lint test ## Run all checks

install-dev: ## Install development dependencies
	pip install -e ".[dev]"

dev: install-dev ## Set up development environment
	@echo "Development environment ready!"

.DEFAULT_GOAL := help 