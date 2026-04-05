"""SubTranslate Backend — FastAPI main application."""
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import upload, models, pipeline, download

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%H:%M:%S",
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="SubTranslate",
    description="Application locale de génération de sous-titres traduits en français",
    version="1.0.0",
)

# Configure CORS for local frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",   # Vite dev server
        "http://localhost:3000",   # Alternative dev port
        "http://localhost:8000",   # Same origin
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(upload.router)
app.include_router(models.router)
app.include_router(pipeline.router)
app.include_router(download.router)


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": "SubTranslate Backend",
        "version": "1.0.0",
    }


@app.on_event("startup")
async def startup():
    logger.info("🚀 SubTranslate Backend started")


@app.on_event("shutdown")
async def shutdown():
    logger.info("👋 SubTranslate Backend shutting down")


if __name__ == "__main__":
    import sys
    import uvicorn

    # Parse CLI args
    host = "127.0.0.1"
    port = 8000
    for i, arg in enumerate(sys.argv):
        if arg == "--host" and i + 1 < len(sys.argv):
            host = sys.argv[i + 1]
        elif arg == "--port" and i + 1 < len(sys.argv):
            port = int(sys.argv[i + 1])

    # Pass app object directly (works in PyInstaller frozen mode)
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info",
    )
