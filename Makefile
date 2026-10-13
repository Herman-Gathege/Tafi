.PHONY: help setup up down logs ps migrate psql test test-backend test-frontend lint format clean

help: ## Show the available commands
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

setup: ## Create .env from .env.example if it does not exist
	@test -f .env || cp .env.example .env
	@echo "Environment ready. Run 'make up'."

up: setup ## Build and start the whole stack
	docker compose up --build -d
	@echo "API:     http://localhost:8000/health"
	@echo "Docs:    http://localhost:8000/docs"
	@echo "Web:     http://localhost:5173"

down: ## Stop the stack
	docker compose down

clean: ## Stop the stack and delete the database/redis volumes
	docker compose down -v

logs: ## Follow the logs for every service
	docker compose logs -f --tail=100

ps: ## Show service status and health
	docker compose ps

migrate: ## Apply database migrations
	docker compose run --rm api alembic upgrade head

psql: ## Open a psql shell on the development database
	docker compose exec db psql -U $${POSTGRES_USER:-tafi} -d $${POSTGRES_DB:-tafi}

test: test-backend test-frontend ## Run every test suite

test-backend: ## Run the backend tests locally with uv
	cd backend && uv run pytest -q

test-frontend: ## Run the frontend checks locally with npm
	cd frontend && npm run lint && npm run typecheck

lint: ## Lint and typecheck both sides
	cd backend && uv run ruff check . && uv run ruff format --check . && uv run mypy app
	cd frontend && npm run lint && npm run typecheck

format: ## Auto-format both sides
	cd backend && uv run ruff format . && uv run ruff check --fix .
	cd frontend && npm run lint -- --fix
