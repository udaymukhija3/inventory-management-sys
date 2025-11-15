.PHONY: help build test deploy clean

help:
	@echo "Available commands:"
	@echo "  make build    - Build all services"
	@echo "  make test     - Run all tests"
	@echo "  make deploy   - Deploy to local environment"
	@echo "  make clean    - Clean build artifacts"

build:
	@echo "Building all services..."
	cd inventory-service && mvn clean package
	cd analytics-service && docker build -t analytics-service:latest .
	cd reorder-service && mvn clean package
	cd stream-processor && sbt clean assembly
	cd api-gateway && mvn clean package

test:
	@echo "Running tests..."
	cd inventory-service && mvn test
	cd analytics-service && pytest
	cd reorder-service && mvn test
	cd stream-processor && sbt test

deploy-local:
	docker-compose up -d

deploy-prod:
	docker-compose -f docker-compose.prod.yml up -d

clean:
	docker-compose down -v
	find . -name "target" -type d -exec rm -rf {} +
	find . -name "__pycache__" -type d -exec rm -rf {} +

