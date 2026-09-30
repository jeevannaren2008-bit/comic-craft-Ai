from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.routes import router

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"

app = FastAPI(
    title="ComicCraft",
    description="AI Comic Story Creator using Gemini and Stable Diffusion",
    version="1.0.0",
)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.include_router(router)
