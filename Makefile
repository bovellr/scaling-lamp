.PHONY: setup run test clean install

# Default target
all: setup

# Complete project setup
setup:
	@echo "🚀 Setting up Bank Reconciliation AI..."
	python setup.py

# Run the application
run:
	@echo "🎯 Running Bank Reconciliation AI..."
	python main.py

# Run tests
test:
	@echo "🧪 Running tests..."
	python tests/test_basic.py

# Install dependencies only
install:
	@echo "📦 Installing dependencies..."
	pip install -r requirements/desktop.txt

# Clean generated files
clean:
	@echo "🧹 Cleaning generated files..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	rm -rf logs/*.log
	rm -rf output/*

# Create virtual environment
venv:
	@echo "🔧 Creating virtual environment..."
	python3 -m venv venv
	@echo "✅ Virtual environment created. Activate with: source venv/bin/activate"

# Help
help:
	@echo "Available commands:"
	@echo "  make setup   - Complete project setup (install deps + bootstrap)"
	@echo "  make install - Install dependencies only"
	@echo "  make run     - Run the application"
	@echo "  make test    - Run tests"
	@echo "  make clean   - Clean generated files"
	@echo "  make venv    - Create virtual environment" 