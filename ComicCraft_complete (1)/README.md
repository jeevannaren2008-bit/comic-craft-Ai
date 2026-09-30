# ComicCraft — AI Comic Story Creator

ComicCraft is a FastAPI web application based on the supplied project specification. It accepts a story prompt, character name, setting, tone, and art style, then creates a five-panel comic, previews it in the browser, and exports it as PDF.

The supplied specification describes a FastAPI + Jinja2 frontend, Gemini Flash for the structured outline, Gemini Pro for narration/dialogue, Stable Diffusion through Hugging Face Diffusers for images, and FPDF for PDF export.

## Architecture

- `app/routes.py` — browser and JSON API routes
- `app/services/gemini_flash.py` — structured five-panel outline
- `app/services/gemini_pro.py` — narration/dialogue
- `app/services/image_generator.py` — Stable Diffusion / local placeholder mode
- `app/services/layout_builder.py` — combines text and images
- `app/services/exporters.py` — PDF creation
- `templates/` — Jinja2 pages
- `static/` — CSS, generated panels, generated PDFs

## Important implementation note

The original document names `gemini-1.5-flash` and `gemini-1.5-pro`. Those model IDs are configurable in `.env` rather than hard-coded because model availability can change. The included defaults are current configurable examples; if your Google account exposes different model IDs, change them in `.env`.

The image pipeline is also configurable. `IMAGE_BACKEND=placeholder` lets you test the complete application without downloading a large Stable Diffusion checkpoint. Set `IMAGE_BACKEND=diffusers` to enable the local Diffusers pipeline.

## Windows + VS Code setup

1. Install Python 3.11 or newer.
2. Open this folder in VS Code.
3. Open Terminal → New Terminal.
4. Create a virtual environment:

   `python -m venv .venv`

5. Activate it in PowerShell:

   `.\.venv\Scripts\Activate.ps1`

   If PowerShell blocks activation, use Command Prompt:

   `.venv\Scripts\activate`

6. Upgrade pip:

   `python -m pip install --upgrade pip`

7. Install dependencies:

   `pip install -r requirements.txt`

8. Copy `.env.example` to `.env`.

9. Put your Gemini API key in `GEMINI_API_KEY`.

10. For the first test, keep:

    `IMAGE_BACKEND=placeholder`

11. Start the server:

    `uvicorn app.main:app --reload`

12. Open:

    http://127.0.0.1:8000

13. API docs:

    http://127.0.0.1:8000/docs

## Real Stable Diffusion images

Change:

`IMAGE_BACKEND=diffusers`

The first generation downloads the configured Stable Diffusion checkpoint and can require substantial disk space, RAM/VRAM, and time. A CUDA-capable GPU is recommended. If you use a gated/private Hugging Face model, provide `HF_API_KEY`.

## API examples

POST `/generate-comic/json`

```json
{
  "story_prompt": "A brave fox explores an enchanted forest.",
  "character_name": "Fenn",
  "setting": "Forest",
  "tone": "Dramatic",
  "art_style": "Comic book"
}
```

POST `/test-image`

```json
{
  "prompt": "A brave fox in an enchanted forest, comic book illustration"
}
```

GET `/health`

## Testing

With the virtual environment active:

`pytest -q`

The tests use placeholder image mode so they do not download a large image model.

## Troubleshooting

- Gemini errors: check `GEMINI_API_KEY` and the configured model IDs.
- Slow image generation: use a CUDA GPU or keep `IMAGE_BACKEND=placeholder` for development.
- PDF problems: ensure the generated panel files exist under `static/panels`.
- Windows activation issue: use Command Prompt activation instead of PowerShell.
- If a provider changes a model name, update the corresponding `.env` variable without changing the application code.

## Project flow

Browser form → FastAPI `/generate` → Gemini outline → Gemini story → image generation → layout builder → FPDF → preview/PDF download.

This follows the workflow and route structure described in the supplied ComicCraft documentation.
