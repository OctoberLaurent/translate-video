# SubTranslate 🎬🇫🇷

Application locale de génération de sous-titres (.srt) traduits en français à partir de vidéos dans n'importe quelle langue.

> **100% local** — Vos données restent sur votre machine. Aucune donnée n'est envoyée vers des serveurs externes.

## Architecture

| Couche | Technologie |
|--------|-------------|
| **Frontend** | Vue.js 3 + Tailwind CSS (style Notion) |
| **Backend** | FastAPI (Python) |
| **Speech-to-Text** | faster-whisper (local) |
| **Traduction** | LM Studio API (OpenAI-compatible, local) |
| **Audio** | FFmpeg |
| **Desktop** | Electron |

## Pipeline de traitement

1. **Extraction audio** — FFmpeg convertit la vidéo en WAV (16kHz, mono)
2. **Transcription** — Whisper génère des segments texte + timestamps
3. **Traduction** — LM Studio traduit les segments en français par lots
4. **Assemblage SRT** — Fusion timestamps + textes traduits → fichier `.srt`

## Prérequis

### Logiciels requis
- **Python 3.10+** (avec pip)
- **Node.js 18+** (avec npm)
- **FFmpeg** — Installé et accessible dans le PATH
- **LM Studio** — Téléchargeable sur [lmstudio.ai](https://lmstudio.ai/)

### Matériel recommandé
- **macOS** : Apple Silicon (M1/M2/M3/M4) recommandé
- **Windows** : GPU NVIDIA avec CUDA recommandé
- **RAM/VRAM** : 8 Go minimum, 16 Go+ recommandé

## Installation & Développement

### 1. Cloner le projet
```bash
cd translate-vidéo
```

### 2. Installer le backend (Python)
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# ou: venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### 3. Installer le frontend (Node.js)
```bash
cd ../frontend
npm install
```

### 4. Configurer LM Studio
1. Lancez LM Studio
2. Chargez un modèle LLM (ex: Llama 3, Mistral, etc.)
3. Activez le **serveur local** dans l'onglet "Local Server" (port 1234 par défaut)

## Lancement en mode développement

### Terminal 1 — Backend
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### Terminal 2 — Frontend
```bash
cd frontend
npm run dev
```

Ouvrez ensuite **http://localhost:5173** dans votre navigateur.

## Build & Distribution

### Build complet (macOS)
```bash
chmod +x scripts/*.sh
./scripts/build-app.sh
```
Produit un fichier `.dmg` dans `dist-electron/`.

### Build complet (Windows)
```bash
scripts\build-app.bat
```
Produit un installateur `.exe` dans `dist-electron\`.

### Build backend uniquement
```bash
./scripts/build-backend.sh
```

## Structure du projet

```
translate-vidéo/
├── backend/                  # FastAPI Python
│   ├── app/
│   │   ├── main.py           # Point d'entrée
│   │   ├── routers/          # Endpoints API
│   │   │   ├── upload.py     # Upload vidéo
│   │   │   ├── models.py     # Liste des modèles
│   │   │   ├── pipeline.py   # Pipeline WebSocket
│   │   │   └── download.py   # Téléchargement SRT
│   │   ├── services/         # Logique métier
│   │   │   ├── audio_extractor.py
│   │   │   ├── whisper_service.py
│   │   │   ├── translator.py
│   │   │   └── srt_builder.py
│   │   └── utils/
│   │       └── config.py
│   ├── requirements.txt
│   └── backend.spec          # Config PyInstaller
│
├── frontend/                 # Vue.js 3 + Tailwind
│   ├── src/
│   │   ├── App.vue           # Composant principal
│   │   ├── components/
│   │   │   ├── DropZone.vue
│   │   │   ├── ConfigPanel.vue
│   │   │   ├── PipelineStatus.vue
│   │   │   └── DownloadSection.vue
│   │   └── services/
│   │       └── api.js
│   ├── tailwind.config.js
│   └── vite.config.js
│
├── electron/                 # Couche Desktop
│   ├── main.js               # Process principal
│   ├── preload.js
│   └── package.json
│
├── scripts/                  # Scripts de build
│   ├── build-backend.sh
│   └── build-app.sh
│
└── README.md
```

## API Endpoints

| Méthode | Route | Description |
|---------|-------|-------------|
| `POST` | `/api/upload` | Upload une vidéo |
| `GET` | `/api/whisper-models` | Liste les modèles Whisper |
| `GET` | `/api/llm-models` | Liste les modèles LM Studio |
| `GET` | `/api/device` | Info sur le device de calcul |
| `WS` | `/api/ws/pipeline` | Pipeline via WebSocket |
| `GET` | `/api/download/{filename}` | Télécharge le fichier SRT |
| `GET` | `/api/health` | Vérification santé |

## Licence

Projet privé — Tous droits réservés.