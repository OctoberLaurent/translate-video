.PHONY: help start backend frontend install build kill

help: ## Show available commands
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

# ── Development ──────────────────────────────────────────────

start: kill ## Start backend + frontend (dev mode)
	@echo "🚀 Starting SubTranslate..."
	@$(MAKE) -j2 _backend _frontend || true

_backend:
	@echo "🔧 Starting backend on http://127.0.0.1:8000"
	@cd backend && .venv/bin/python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8000

_frontend:
	@echo "🎨 Starting frontend on http://localhost:5173"
	@cd frontend && npx vite --host

backend: ## Start backend only
	@cd backend && .venv/bin/python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8000

frontend: ## Start frontend only
	@cd frontend && npx vite --host

# ── Setup ────────────────────────────────────────────────────

install: ## Install all dependencies (Python + Node)
	@echo "📦 Setting up SubTranslate..."
	@echo "🐍 Creating Python venv..."
	@test -d backend/.venv || python3.12 -m venv backend/.venv
	@echo "📥 Installing Python dependencies..."
	@backend/.venv/bin/pip install --upgrade pip --quiet
	@backend/.venv/bin/pip install -r backend/requirements.txt --quiet
	@echo "📥 Installing Node dependencies..."
	@cd frontend && npm install
	@echo "✅ All dependencies installed!"

# ── Build ────────────────────────────────────────────────────

build: ## Build packaged app (PyInstaller backend + Electron)
	@echo "🏗️  Building SubTranslate..."
	@bash scripts/build-backend.sh
	@bash scripts/build-app.sh
	@echo "✅ Build complete!"

build-backend: ## Build backend only (PyInstaller)
	@bash scripts/build-backend.sh

build-frontend: ## Build frontend only (Vite)
	@cd frontend && npm run build

# ── Utilities ────────────────────────────────────────────────

kill: ## Kill processes on ports 8000 and 5173
	@echo "🛑 Stopping existing processes..."
	@lsof -ti:8000 | xargs kill 2>/dev/null || true
	@lsof -ti:5173 | xargs kill 2>/dev/null || true
	@echo "✅ Done"