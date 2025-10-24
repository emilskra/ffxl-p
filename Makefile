.PHONY: test test-verbose test-coverage install-dev example clean lint format build publish-test publish

# Run tests
test:
	pytest tests/ -v

# Run tests with verbose output
test-verbose:
	pytest tests/ -vv

# Run tests with coverage (requires pytest-cov)
test-coverage:
	pytest tests/ --cov=src/ffxl_p --cov-report=term-missing --cov-report=html

# Install package in development mode with dev dependencies
install-dev:
	pip install -e ".[dev]"

# Run linter
lint:
	ruff check src/ tests/

# Format code
format:
	ruff format src/ tests/
	ruff check --fix src/ tests/

# Run example
example:
	python example.py

# Run example with dev mode
example-dev:
	FFXL_DEV_MODE=true python example.py

# Build package
build:
	python -m build

# Test build
build-test:
	python -m build
	twine check dist/*

# Publish to TestPyPI
publish-test: build
	twine upload --repository testpypi dist/*

# Publish to PyPI (use GitHub releases instead)
publish: build
	@echo "⚠️  Use GitHub releases to publish automatically!"
	@echo "Manual publish: twine upload dist/*"

# Clean up
clean:
	rm -rf __pycache__ .pytest_cache htmlcov .coverage
	rm -rf build dist *.egg-info
	rm -rf src/*.egg-info
	rm -rf .ruff_cache
	find . -type f -name '*.pyc' -delete
	find . -type d -name '__pycache__' -delete

# Show help
help:
	@echo "Available targets:"
	@echo "  test          - Run tests"
	@echo "  test-coverage - Run tests with coverage report"
	@echo "  lint          - Run ruff linter"
	@echo "  format        - Format code with ruff"
	@echo "  install-dev   - Install package in dev mode"
	@echo "  example       - Run example script"
	@echo "  build         - Build package"
	@echo "  clean         - Clean up temporary files"
