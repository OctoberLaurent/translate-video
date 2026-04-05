# 🚀 SubTranslate — Getting Started

---

## 🇬🇧 English

### Prerequisites

- **Python 3.12** — [python.org](https://www.python.org/downloads/)
- **Node.js 18+** — [nodejs.org](https://nodejs.org/)
- **Make** — usually pre-installed on macOS/Linux

### Quick Start

```bash
# 1. Install all dependencies
make install

# 2. Start the app (backend + frontend)
make start
```

Then open **http://localhost:5173** in your browser.

### Available Commands

| Command | Description |
|---|---|
| `make start` | Start backend + frontend in dev mode |
| `make backend` | Start backend only (port 8000) |
| `make frontend` | Start frontend only (port 5173) |
| `make install` | Install Python & Node dependencies |
| `make build` | Build packaged app (PyInstaller + Electron) |
| `make kill` | Stop all running processes |
| `make help` | Show all available commands |

### Architecture

```
Frontend (Vue 3 + Vite)  →  http://localhost:5173
        ↕ (proxy /api)
Backend (FastAPI + Whisper)  →  http://127.0.0.1:8000
```

### Without Make

If you don't have `make`, you can run manually:

```bash
# Backend
cd backend
.venv/bin/python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8000

# Frontend (in another terminal)
cd frontend
npm install
npx vite --host
```

### Build for Distribution

```bash
make build
```

This creates a macOS `.dmg` in `electron/dist/`.

---

## 🇫🇷 Français

### Prérequis

- **Python 3.12** — [python.org](https://www.python.org/downloads/)
- **Node.js 18+** — [nodejs.org](https://nodejs.org/)
- **Make** — généralement pré-installé sur macOS/Linux

### Démarrage rapide

```bash
# 1. Installer toutes les dépendances
make install

# 2. Lancer l'application (backend + frontend)
make start
```

Puis ouvrir **http://localhost:5173** dans votre navigateur.

### Commandes disponibles

| Commande | Description |
|---|---|
| `make start` | Lancer backend + frontend en mode dev |
| `make backend` | Lancer le backend uniquement (port 8000) |
| `make frontend` | Lancer le frontend uniquement (port 5173) |
| `make install` | Installer les dépendances Python & Node |
| `make build` | Builder l'app packagée (PyInstaller + Electron) |
| `make kill` | Arrêter tous les processus en cours |
| `make help` | Afficher toutes les commandes disponibles |

### Architecture

```
Frontend (Vue 3 + Vite)  →  http://localhost:5173
        ↕ (proxy /api)
Backend (FastAPI + Whisper)  →  http://127.0.0.1:8000
```

### Sans Make

Si vous n'avez pas `make`, vous pouvez lancer manuellement :

```bash
# Backend
cd backend
.venv/bin/python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8000

# Frontend (dans un autre terminal)
cd frontend
npm install
npx vite --host
```

### Build pour distribution

```bash
make build
```

Cela crée un `.dmg` macOS dans `electron/dist/`.