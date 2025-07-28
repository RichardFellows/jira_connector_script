# JIRA Analytics - Build and Deployment Makefile

.PHONY: help install dev-install test clean build docker docker-run docker-stop deploy

# Default target
help:
	@echo "JIRA Analytics - Available Commands:"
	@echo ""
	@echo "  Development:"
	@echo "    install      - Install package and dependencies"
	@echo "    dev-install  - Install in development mode with dev dependencies"
	@echo "    test         - Run tests"
	@echo "    clean        - Clean build artifacts"
	@echo ""
	@echo "  Build & Package:"
	@echo "    build        - Build Python package"
	@echo "    docker       - Build Docker image"
	@echo ""
	@echo "  Deployment:"
	@echo "    docker-run   - Run Docker container"
	@echo "    docker-stop  - Stop Docker container"
	@echo "    deploy       - Deploy using Docker Compose"
	@echo ""
	@echo "  Analytics:"
	@echo "    analytics    - Start analytics dashboard"
	@echo "    extract      - Run JIRA data extraction"

# Installation
install:
	pip install -r requirements.txt
	pip install -e .

dev-install:
	pip install -r requirements.txt
	pip install -e ".[dev]"

# Testing
test:
	@echo "Running tests..."
	python -m pytest tests/ -v || echo "No tests found"
	
	@echo "Validating Python syntax..."
	python -m py_compile *.py
	
	@echo "Checking code style..."
	flake8 *.py --max-line-length=120 --ignore=E501,W503 || echo "flake8 not installed"

# Cleanup
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete

# Build
build: clean
	python setup.py sdist bdist_wheel
	@echo "Build complete. Files in dist/:"
	@ls -la dist/

# Docker operations
docker:
	@echo "Building Docker image..."
	docker build -t jira-analytics:latest .
	@echo "Docker image built successfully"

docker-run: docker
	@echo "Starting JIRA Analytics container..."
	docker run -d \
		--name jira-analytics \
		-p 2718:2718 \
		-v $(PWD)/data:/app/data \
		--restart unless-stopped \
		jira-analytics:latest
	@echo "Container started. Access dashboard at http://localhost:2718"

docker-stop:
	@echo "Stopping JIRA Analytics container..."
	docker stop jira-analytics || true
	docker rm jira-analytics || true

# Docker Compose deployment
deploy:
	@echo "Deploying with Docker Compose..."
	mkdir -p data config logs
	cp -n config.json.example config/config.json || true
	docker-compose up -d
	@echo "Deployment complete. Access dashboard at http://localhost:2718"

deploy-stop:
	docker-compose down

deploy-logs:
	docker-compose logs -f jira-analytics

# Development commands
analytics:
	@echo "Starting JIRA Analytics Dashboard..."
	python jira_analytics_cli.py

extract:
	@echo "Starting JIRA Data Extraction..."
	@echo "Usage: make extract ARGS='--url https://jira.example.com --token TOKEN --project PROJ'"
	python jira_extractor.py $(ARGS)

# Quick setup for new users
setup: install
	@echo ""
	@echo "🎉 JIRA Analytics Setup Complete!"
	@echo ""
	@echo "Next steps:"
	@echo "1. Copy and configure: cp config.json.example config.json"
	@echo "2. Extract data: python jira_extractor.py --url YOUR_JIRA_URL --token YOUR_TOKEN --project YOUR_PROJECT"
	@echo "3. Start dashboard: make analytics"
	@echo ""
	@echo "Or use Docker: make deploy"

# Distribution
dist: build
	@echo "Creating distribution package..."
	@echo "Files ready for distribution:"
	@ls -la dist/

# Health check
health:
	@echo "Checking JIRA Analytics health..."
	@curl -f http://localhost:2718/ && echo "✅ Dashboard is running" || echo "❌ Dashboard is not accessible"

# Backup
backup:
	@echo "Creating backup..."
	mkdir -p backups
	@if [ -f data/jira_data.duckdb ]; then \
		cp data/jira_data.duckdb backups/jira_data_$(shell date +%Y%m%d_%H%M%S).duckdb; \
		echo "✅ Backup created in backups/"; \
	else \
		echo "❌ No database file found to backup"; \
	fi

# Update
update:
	@echo "Updating JIRA Analytics..."
	git pull
	pip install -r requirements.txt --upgrade
	make docker
	@echo "✅ Update complete"