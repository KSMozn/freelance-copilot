.PHONY: help up down logs build migrate revision seed create-admin backend-dev frontend-dev backend-test fmt lint

help:
	@echo "Targets:"
	@echo "  up             docker compose up -d --build"
	@echo "  down           docker compose down"
	@echo "  logs           tail compose logs"
	@echo "  migrate        run alembic upgrade head inside backend container"
	@echo "  revision m=... create a new alembic revision (autogenerate)"
	@echo "  seed           seed the DORMANT professional demo (job/portfolios/resumes)"
	@echo "  create-admin   create/reset an admin user (email=... password=... [name=...])"
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

# Seeds the DORMANT professional surface's demo data (job, portfolios,
# resumes, applications). For the live product, use create-admin instead.
seed:
	docker compose exec backend python -m app.scripts.seed

# Create (or reset the password of) a PersonaArmory admin user. Idempotent.
create-admin:
	@test -n "$(email)" || (echo 'usage: make create-admin email=you@example.com password=secret [name="Full Name"]' && exit 1)
	@test -n "$(password)" || (echo 'usage: make create-admin email=you@example.com password=secret [name="Full Name"]' && exit 1)
	docker compose exec -e ADMIN_EMAIL=$(email) -e ADMIN_PASSWORD=$(password) -e ADMIN_FULL_NAME=$(name) backend python -m app.scripts.create_admin

# uv run syncs .venv from uv.lock on demand — no manual activation needed.
backend-dev:
	cd backend && uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

frontend-dev:
	cd frontend && npm run dev

backend-test:
	docker compose exec backend pytest

fmt:
	cd backend && uv run --extra dev ruff format . && uv run --extra dev ruff check --fix .
	cd frontend && npm run format

lint:
	cd backend && uv run --extra dev ruff check .
	cd frontend && npm run lint && npm run typecheck
