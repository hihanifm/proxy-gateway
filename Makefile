# Quick reference:
#   make build && make up   — pick up Dockerfile / dependency changes
#   make rebuild            — full --no-cache rebuild + up (after git pull if containers act stale)
#   make rebuild-gateway    — gateway image only (faster when only gateway/ changed)
.PHONY: help up down build rebuild rebuild-gateway logs logs-gateway restart ps \
        prod-up prod-down prod-logs pip-cache clean

help:
	@echo "Dev:"
	@echo "  make build && make up   Build images + start dev stack (gateway on :8001)"
	@echo "  make rebuild            Full --no-cache rebuild + up"
	@echo "  make rebuild-gateway    Rebuild gateway image only (faster)"
	@echo "  make restart            down + up without rebuild"
	@echo "  make logs               Tail all dev logs"
	@echo "  make logs-gateway       Tail gateway logs only"
	@echo "  make ps                 Container status"
	@echo ""
	@echo "Prod (explicit, runs on :8000):"
	@echo "  make prod-up            Start prod stack"
	@echo "  make prod-down          Stop prod stack"
	@echo "  make prod-logs          Tail prod logs"
	@echo ""
	@echo "Maintenance:"
	@echo "  make pip-cache          Download wheels for offline builds (arch-aware)"
	@echo "  make clean              Remove containers/volumes; prune images"

up:
	docker compose --profile dev up -d

down:
	docker compose --profile dev down --remove-orphans

build:
	docker compose --profile dev build

rebuild:
	docker compose --profile dev build --no-cache
	docker compose --profile dev up -d

rebuild-gateway:
	docker compose --profile dev build --no-cache gateway
	docker compose --profile dev up -d gateway

restart:
	docker compose --profile dev down --remove-orphans
	docker compose --profile dev up -d

logs:
	docker compose --profile dev logs -f

logs-gateway:
	docker compose --profile dev logs -f gateway

ps:
	docker compose ps

prod-up:
	docker compose --profile dev down --remove-orphans
	docker compose --profile prod up -d --build

prod-down:
	docker compose --profile prod down --remove-orphans

prod-logs:
	docker compose --profile prod logs -f

pip-cache:
	@mkdir -p pip-cache
	@ARCH=$$(uname -m); \
	if [ "$$ARCH" = "arm64" ] || [ "$$ARCH" = "aarch64" ]; then \
	  PLAT="--platform manylinux_2_17_aarch64 --platform linux_aarch64"; \
	else \
	  PLAT="--platform manylinux_2_17_x86_64 --platform manylinux2014_x86_64 --platform linux_x86_64"; \
	fi; \
	pip download $$PLAT \
	  --python-version 3.11 --implementation cp --abi cp311 \
	  --only-binary=:all: \
	  -r requirements.txt \
	  -d pip-cache/

clean:
	docker compose --profile dev down --remove-orphans --volumes
	docker compose --profile prod down --remove-orphans --volumes
	docker image prune -f
