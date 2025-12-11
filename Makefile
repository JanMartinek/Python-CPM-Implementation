.PHONY: help install install-dev test test-verbose test-coverage clean lint format examples all

help:
	@echo "CPM Python Implementation - Makefile"
	@echo ""
	@echo "Available targets:"
	@echo "  install        - Install core dependencies"
	@echo "  install-dev    - Install all dependencies (including dev/optional)"
	@echo "  test           - Run all tests (quiet mode)"
	@echo "  test-verbose   - Run all tests with verbose output"
	@echo "  test-coverage  - Run tests with coverage report"
	@echo "  examples       - Run all example scripts"
	@echo "  clean          - Remove build artifacts and cache files"
	@echo "  lint           - Check code style (if tools available)"
	@echo "  format         - Format code (if tools available)"
	@echo "  all            - Install deps and run tests"

install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements.txt
	pip install -e .

test:
	python -m pytest tests/ -q

test-verbose:
	python -m pytest tests/ -v

test-coverage:
	python -m pytest tests/ --cov=src --cov-report=html --cov-report=term

test-specific:
	python -m pytest tests/test_template.py -v

examples:
	@echo "Running basic examples..."
	python examples/basic_examples.py
	@echo ""
	@echo "Running advanced examples..."
	python examples/advanced_examples.py
	@echo ""
	@echo "Running template examples..."
	python examples/template_examples.py

clean:
	rm -rf __pycache__ .pytest_cache .coverage htmlcov
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build dist

lint:
	@command -v flake8 >/dev/null 2>&1 && flake8 src/ tests/ || echo "flake8 not installed"
	@command -v pylint >/dev/null 2>&1 && pylint src/ || echo "pylint not installed"

format:
	@command -v black >/dev/null 2>&1 && black src/ tests/ examples/ || echo "black not installed"
	@command -v isort >/dev/null 2>&1 && isort src/ tests/ examples/ || echo "isort not installed"

all: install test
	@echo "Setup complete and all tests passed!"