from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    gemini_api_key: str = ""
    hf_api_key: str = ""
    gemini_outline_model: str = "gemini-2.5-flash"
    gemini_story_model: str = "gemini-2.5-pro"
    image_model_id: str = "runwayml/stable-diffusion-v1-5"
    image_backend: str = "diffusers"  # diffusers | placeholder
    comic_panels: int = 5
    image_width: int = 512
    image_height: int = 512
    image_steps: int = 20
    output_dir: str = str(BASE_DIR / "static")
    max_prompt_length: int = 2000

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

@lru_cache
def get_settings() -> Settings:
    return Settings()
