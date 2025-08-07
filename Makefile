# Makefile for Custom Blast Radius

.PHONY: help install build run docker-build docker-run docker-stop clean test examples

# Default target
help:
	@echo "Custom Blast Radius - Available Commands:"
	@echo ""
	@echo "Installation:"
	@echo "  install      - Install Python dependencies"
	@echo "  build        - Build Docker image"
	@echo ""
	@echo "Running:"
	@echo "  run          - Serve examples locally"
	@echo "  docker-build - Build Docker image"
	@echo "  docker-run   - Run with Docker Compose"
	@echo "  docker-stop  - Stop Docker containers"
	@echo ""
	@echo "Development:"
	@echo "  export       - Export diagrams for all examples"
	@echo "  clean        - Remove generated files"
	@echo "  test         - Run tests"
	@echo "  examples     - Initialize Terraform examples"
	@echo ""
	@echo "Examples:"
	@echo "  aws-vpc      - Serve AWS VPC example"
	@echo "  multi-tier   - Serve multi-tier app example"
	@echo "  kubernetes   - Serve Kubernetes example"
	@echo "  serverless   - Serve serverless example"

# Install Python dependencies
install:
	@echo "Installing Python dependencies..."
	pip install -r requirements.txt
	@echo "Installation complete"

# Build Docker image
build:
	@echo "Building Docker image..."
	docker build -t custom-blast-radius .
	@echo "Docker image built successfully"

# Run examples locally
run:
	@echo "Starting local server..."
	@echo "Available examples:"
	@echo "  - AWS VPC: http://localhost:5000"
	@echo "  - Multi-tier App: http://localhost:5001"
	@echo "  - Kubernetes: http://localhost:5002"
	@echo "  - Serverless: http://localhost:5003"
	@echo ""
	@echo "Press Ctrl+C to stop"
	python blast_radius.py --serve examples/aws-vpc --host 0.0.0.0 --port 5000

# Build and run with Docker
docker-build:
	@echo "Building Docker image..."
	docker-compose build
	@echo "Docker build complete"

docker-run:
	@echo "Starting Docker containers..."
	docker-compose up -d
	@echo "Services started:"
	@echo "  - AWS VPC: http://localhost:5000"
	@echo "  - Multi-tier App: http://localhost:5001"
	@echo "  - Kubernetes: http://localhost:5002"
	@echo "  - Serverless: http://localhost:5003"

docker-stop:
	@echo "Stopping Docker containers..."
	docker-compose down
	@echo "Docker containers stopped"

# Export diagrams for all examples
export:
	@echo "Exporting diagrams for all examples..."
	@mkdir -p output
	@for example in examples/*; do \
		if [ -d "$$example" ]; then \
			echo "Exporting $$(basename $$example)..."; \
			python blast_radius.py --export "$$example" --format all --output output/$$(basename $$example); \
		fi; \
	done
	@echo "Export complete. Files saved to output/ directory"

# Clean generated files
clean:
	@echo "Cleaning generated files..."
	rm -rf output/
	rm -rf diagrams/
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	@echo "Clean complete"

# Run tests
test:
	@echo "Running tests..."
	pytest tests/ -v
	@echo "Tests complete"

# Initialize Terraform examples
examples:
	@echo "Initializing Terraform examples..."
	@for example in examples/*; do \
		if [ -d "$$example" ]; then \
			echo "Initializing $$(basename $$example)..."; \
			cd "$$example" && terraform init -backend=false && cd ../..; \
		fi; \
	done
	@echo "Terraform examples initialized"

# Individual example targets
aws-vpc:
	@echo "Serving AWS VPC example at http://localhost:5000"
	python blast_radius.py --serve examples/aws-vpc --host 0.0.0.0 --port 5000

multi-tier:
	@echo "Serving multi-tier app example at http://localhost:5000"
	python blast_radius.py --serve examples/multi-tier-app --host 0.0.0.0 --port 5000

kubernetes:
	@echo "Serving Kubernetes example at http://localhost:5000"
	python blast_radius.py --serve examples/kubernetes --host 0.0.0.0 --port 5000

serverless:
	@echo "Serving serverless example at http://localhost:5000"
	python blast_radius.py --serve examples/serverless --host 0.0.0.0 --port 5000 