.PHONY: help up down logs build migrate revision seed backend-dev frontend-dev backend-test fmt lint

help:
	@echo "Targets:"
	@echo "  up             docker compose up -d --build"
	@echo "  down           docker compose down"
	@echo "  logs           tail compose logs"
	@echo "  migrate        run alembic upgrade head inside backend container"
	@echo "  revision m=... create a new alembic revision (autogenerate)"
	@echo "  seed           insert a demo user"
	@echo "  backend-dev    run backend locally with reload (no docker)"
	@echo "  frontend-dev   run vite dev server locally (no docker)"
	@echo "  backend-test   pytest inside backend container"
	@echo "  fmt            ruff format + prettier"
	@echo "  lint           ruff check + tsc --noEmit"

up:
	docker compose up -d --build

down:
	docker compose down

logs:
	docker compose logs -f --tail=200

build:
	docker compose build

migrate:
	docker compose exec backend alembic upgrade head

revision:
	@test -n "$(m)" || (echo "usage: make revision m=\"add foo\"" && exit 1)
	docker compose exec backend alembic revision --autogenerate -m "$(m)"

seed:
	docker compose exec backend python -m app.scripts.seed

backend-dev:
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

frontend-dev:
	cd frontend && npm run dev

backend-test:
	docker compose exec backend pytest

fmt:
	cd backend && ruff format . && ruff check --fix .
	cd frontend && npm run format

lint:
	cd backend && ruff check .
	cd frontend && npm run lint && npm run typecheck
