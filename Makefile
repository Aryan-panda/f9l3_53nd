# ==============================================================================
# f9l3_53nd — Developer Automation Makefile
# ==============================================================================

.PHONY: help setup secrets dev test security-test lint format typecheck clean docker-up docker-down

help:
	@echo "f9l3_53nd — Management Commands:"
	@echo "  make setup          Initialize python venv and install frontend dependencies"
	@echo "  make secrets        Generate secure development secrets (.env)"
	@echo "  make dev            Run local backend and frontend dev servers"
	@echo "  make test           Run all backend and frontend unit tests"
	@echo "  make security-test  Run adversarial and security regression test suites"
	@echo "  make lint           Check code quality and style (ruff + eslint)"
	@echo "  make format         Auto-format backend and frontend code"
	@echo "  make typecheck      Run static type checking (mypy + tsc)"
	@echo "  make healthcheck    Run live and readiness health probes"
	@echo "  make docker-up      Start containerized infrastructure"
	@echo "  make docker-down    Stop containerized infrastructure"
	@echo "  make clean          Clean cache, build artifacts, and temp files"

setup:
	@bash scripts/bootstrap.sh

secrets:
	@bash scripts/generate-dev-secrets.sh

dev:
	@echo "Starting development servers..."
	@trap 'kill 0' EXIT; \
	(cd backend && .venv/bin/uvicorn src.app.main:app --reload --host 0.0.0.0 --port 8000) & \
	(cd frontend && npm run dev)

test:
	@bash scripts/test.sh

security-test:
	@bash scripts/security-test.sh

lint:
	@echo "==> Linting backend with ruff..."
	@cd backend && .venv/bin/ruff check .
	@echo "==> Linting frontend with eslint..."
	@cd frontend && npm run lint

format:
	@echo "==> Formatting backend..."
	@cd backend && .venv/bin/ruff format .
	@echo "==> Formatting frontend..."
	@cd frontend && npm run format || true

typecheck:
	@echo "==> Typechecking backend with mypy..."
	@cd backend && .venv/bin/mypy src
	@echo "==> Typechecking frontend with tsc..."
	@cd frontend && npm run typecheck


healthcheck:
	@bash scripts/healthcheck.sh

docker-up:
	@bash scripts/docker-up.sh

docker-down:
	@bash scripts/docker-down.sh


clean:
	@bash scripts/reset-dev-environment.sh
