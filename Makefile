.PHONY: install test lint format lint-sql format-sql run clean help

help:
	@echo "Available commands:"
	@echo "  make install      - Install dependencies"
	@echo "  make test         - Run pytest"
	@echo "  make lint         - Run ruff check (Python)"
	@echo "  make lint-sql     - Run sqlfluff lint"
	@echo "  make format       - Run ruff format (Python)"
	@echo "  make format-sql   - Run sqlfluff fix"
	@echo "  make run          - Run the ingest script"
	@echo "  make clean        - Remove cache files"

install:
	pip install -r requirements.txt

test:
	pytest tests/ -v

lint:
	ruff check scripts/ tests/

lint-sql:
	sqlfluff lint models/

format:
	ruff format scripts/ tests/

format-sql:
	sqlfluff fix models/

run:
	python scripts/ingest.py

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name .DS_Store -delete 2>/dev/null || true