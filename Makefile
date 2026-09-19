# Common tasks. Run from the repository root.

.PHONY: install dev backend frontend test lint eval seed-ai compare-judgment benchmark-judgment build docker

install:            ## Install backend and frontend dependencies
	cd backend && uv sync
	cd frontend && npm install

dev:                ## Run backend (:8000) and frontend (:5173) together
	@$(MAKE) -j2 backend frontend

backend:            ## Run the API with auto-reload
	cd backend && uv run uvicorn app.main:app --reload --port 8000

frontend:           ## Run the Vite dev server
	cd frontend && npm run dev

test:               ## Backend tests (rule-based provider, no API calls)
	cd backend && uv run pytest -q

lint:               ## Lint and format-check everything
	cd backend && uv run ruff check app scripts tests && uv run ruff format --check app scripts tests
	cd frontend && npx tsc -b

eval:               ## Check the committed AI analyses against expectations (no API calls)
	cd backend && uv run python -m scripts.eval

seed-ai:            ## Regenerate data/seed_analyses.json with the configured provider (API calls)
	cd backend && uv run python -m scripts.generate_seed_analyses

compare-judgment:    ## Compare Jev vs the LLM on the 12 seed accounts (needs TYPESAFE_API_KEY)
	cd backend && uv run python -m scripts.compare_judgment

benchmark-judgment:  ## Measure Jev vs Sonnet 5 latency/cost for judgment alone (needs both keys)
	cd backend && uv run python -m scripts.benchmark_judgment

build:              ## Build the frontend so FastAPI can serve it
	cd frontend && npm run build

docker:             ## Build and run the single-container image on :8000
	docker compose up --build

help:
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-12s %s\n", $$1, $$2}'
