.PHONY: dev backend frontend seed test lint clean docker-up docker-down

# Start both backend and frontend
dev:
	@echo "Starting SafeGuard development servers..."
	@make -j2 backend frontend

backend:
	cd backend && uvicorn server:app --reload --port 8000

frontend:
	cd frontend && npm start

# Seed the database with sample incidents
seed:
	curl -X POST http://localhost:8000/api/seed/

# Run backend tests
test:
	cd backend && python -m pytest tests/ -v

# Lint Python code
lint:
	cd backend && ruff check . && ruff format --check .

# Docker development
docker-up:
	docker compose up -d --build

docker-down:
	docker compose down

# Clean generated files
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf backend/.pytest_cache backend/htmlcov backend/.coverage
