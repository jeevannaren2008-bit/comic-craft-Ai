from pathlib import Path
from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.templating import Jinja2Templates

from app.config import get_settings
from app.schemas import PromptRequest, ImageTestRequest
from app.services.gemini_flash import generate_outline
from app.services.gemini_pro import generate_story
from app.services.image_generator import generate_image
from app.services.layout_builder import build_comic_layout
from app.services.exporters import save_pdf

router = APIRouter()
BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

def generate_comic(data: PromptRequest):
    outlines = generate_outline(
        data.story_prompt, data.character_name, data.setting,
        data.tone, data.art_style
    )
    stories = generate_story(outlines, data.character_name, data.tone)
    images = [generate_image(panel["image_prompt"]) for panel in outlines]
    layout = build_comic_layout(outlines, stories, images)
    pdf_path = save_pdf(layout)
    return layout, pdf_path

@router.get("/")
async def home(request: Request):
    return templates.TemplateResponse(request=request, name="index.html", context={})

@router.post("/generate")
async def generate(
    request: Request,
    story_prompt: str = Form(...),
    character_name: str = Form(...),
    setting: str = Form(...),
    tone: str = Form(...),
    art_style: str = Form(...),
):
    try:
        data = PromptRequest(
            story_prompt=story_prompt,
            character_name=character_name,
            setting=setting,
            tone=tone,
            art_style=art_style,
        )
        layout, pdf_path = generate_comic(data)
        return templates.TemplateResponse(
            request=request,
            name="comic_preview.html",
            context={"layout": layout, "pdf_path": pdf_path},
        )
    except Exception as exc:
        return templates.TemplateResponse(
            request=request,
            name="error.html",
            context={"error": str(exc)},
            status_code=500,
        )

@router.post("/generate-comic/json")
async def generate_comic_json(data: PromptRequest):
    try:
        layout, pdf_path = generate_comic(data)
        return {"success": True, "layout": layout, "pdf_path": f"/exports/{Path(pdf_path).name}"}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

@router.post("/test-image")
async def test_image(data: ImageTestRequest):
    try:
        image_path = generate_image(data.prompt)
        return {"success": True, "image_path": "/static/" + image_path}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

@router.get("/download/{filename}")
async def download(filename: str):
    settings = get_settings()
    path = Path(settings.output_dir) / "exports" / filename
    if not path.exists() or path.suffix.lower() != ".pdf":
        raise HTTPException(status_code=404, detail="PDF not found.")
    return FileResponse(path, media_type="application/pdf", filename=path.name)

@router.get("/export-success")
async def export_success(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="export_success.html",
        context={},
    )

@router.get("/health")
async def health():
    return {"status": "ok"}
