from pathlib import Path
from uuid import uuid4
from PIL import Image, ImageDraw, ImageFont

from app.config import get_settings

_PIPELINE = None

def _safe_name(prompt: str) -> str:
    cleaned = "".join(c if c.isalnum() else "_" for c in prompt[:50]).strip("_")
    return cleaned or "panel"

def _placeholder(prompt: str, output_path: Path):
    settings = get_settings()
    image = Image.new("RGB", (settings.image_width, settings.image_height), (242, 235, 220))
    draw = ImageDraw.Draw(image)
    draw.rectangle((12, 12, settings.image_width-12, settings.image_height-12), outline=(40,40,40), width=5)
    try:
        font = ImageFont.truetype("arial.ttf", 22)
    except Exception:
        font = ImageFont.load_default()
    short = prompt[:220]
    draw.multiline_text((30, 35), "ComicCraft\n\n" + short, fill=(25,25,25), font=font, spacing=8)
    image.save(output_path, "PNG")
    return output_path

def generate_image(prompt: str) -> str:
    settings = get_settings()
    output_dir = Path(settings.output_dir) / "panels"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{_safe_name(prompt)}_{uuid4().hex[:8]}.png"

    if settings.image_backend.lower() == "placeholder":
        return str(_placeholder(prompt, output_path).relative_to(Path(settings.output_dir))).replace("\\", "/")

    global _PIPELINE
    try:
        import torch
        from diffusers import StableDiffusionPipeline

        if _PIPELINE is None:
            dtype = torch.float16 if torch.cuda.is_available() else torch.float32
            kwargs = {"torch_dtype": dtype}
            if settings.hf_api_key:
                kwargs["token"] = settings.hf_api_key
            _PIPELINE = StableDiffusionPipeline.from_pretrained(settings.image_model_id, **kwargs)
            if torch.cuda.is_available():
                _PIPELINE = _PIPELINE.to("cuda")
            else:
                _PIPELINE = _PIPELINE.to("cpu")

        result = _PIPELINE(
            prompt=prompt,
            num_inference_steps=settings.image_steps,
            width=settings.image_width,
            height=settings.image_height,
        )
        result.images[0].save(output_path)
        return str(output_path.relative_to(Path(settings.output_dir))).replace("\\", "/")
    except Exception:
        # Keep the web app usable when local Diffusers/PyTorch is not available.
        return str(_placeholder(prompt, output_path).relative_to(Path(settings.output_dir))).replace("\\", "/")
