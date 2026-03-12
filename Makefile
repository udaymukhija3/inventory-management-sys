.PHONY: help build test demo seed up backfill clean

help:
	@echo "Available commands:"
	@echo "  make up       - Start the supported local stack"
	@echo "  make seed     - Load deterministic demo data"
	@echo "  make demo     - Run the supported end-to-end demo"
	@echo "  make backfill - Rebuild metrics for a date range (requires BACKFILL_START/BACKFILL_END)"
	@echo "  make build    - Build the supported services"
	@echo "  make test     - Run the supported tests"
	@echo "  make clean    - Stop containers and clean build artifacts"

up:
	docker compose -f docker-compose.dev.yml up --build -d postgres redis zookeeper kafka inventory-service analytics-service data-pipeline prometheus grafana

build:
	docker compose -f docker-compose.dev.yml build inventory-service analytics-service data-pipeline

seed:
	./scripts/seed-data.sh

demo:
	./scripts/demo.sh

backfill:
	@if [ -z "$(BACKFILL_START)" ] || [ -z "$(BACKFILL_END)" ]; then \
		echo "Usage: make backfill BACKFILL_START=2026-03-01T00:00:00 BACKFILL_END=2026-03-13T00:00:00 [FORCE_REPROCESS=true]"; \
		exit 1; \
	fi
	FORCE_REPROCESS="$(FORCE_REPROCESS)" bash ./scripts/backfill.sh "$(BACKFILL_START)" "$(BACKFILL_END)"

test:
	cd inventory-service && mvn test
	./scripts/run-analytics-tests.sh
	bash ./scripts/run-data-pipeline-tests.sh

clean:
	docker compose -f docker-compose.dev.yml down -v
	find . -name "target" -type d -exec rm -rf {} +
	find . -name "__pycache__" -type d -exec rm -rf {} +
