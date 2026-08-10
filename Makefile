.PHONY: install test lint format run clean help

help: 
	@echo "Available commands:"
	@echo "  make install    - Install dependencies"
	@echo "  make test       - Run pytest"
	@echo "  make lint       - Run ruff check"
	@echo "  make format     - Run ruff format"
	@echo "  make run        - Run the ingest script"
	@echo "  make clean      - Remove cache files"

install: 
	pip install -r requirements.txt 

test:
	pytest tests/ -v

lint: 
	ruff check scripts/ tests/ 

format: 
	ruff format scripts/ tests/

run: 
	python scripts/ingest.py

clean: 
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name .DS_Store -delete 2>/dev/null || true	