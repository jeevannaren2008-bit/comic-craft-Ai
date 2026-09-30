import json
import re
import time
from typing import Any

from app.config import get_settings

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None
    types = None


def _extract_json(text: str) -> Any:
    """Extract JSON from Gemini's response."""

    if not text:
        raise ValueError("Gemini returned an empty response.")

    text = text.strip()

    # Remove Markdown code fences
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text)

    # First try to parse the complete response
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try to find a JSON array inside the response
    match = re.search(r"\[[\s\S]*\]", text)

    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    raise ValueError("Gemini did not return valid JSON.")


def _fallback_outline(
    story_prompt: str,
    character_name: str,
    setting: str,
    tone: str,
    art_style: str,
):
    """Generate a local comic outline without using Gemini."""

    settings = get_settings()

    panel_count = settings.comic_panels

    descriptions = [
        (
            "The Beginning",
            f"{character_name} discovers the first clue connected to "
            f"{story_prompt}."
        ),
        (
            "A Strange Turn",
            f"The situation suddenly changes as {character_name} explores "
            f"{setting}."
        ),
        (
            "The Challenge",
            f"{character_name} faces the central challenge and must act "
            f"bravely."
        ),
        (
            "The Turning Point",
            f"A surprising idea helps {character_name} change the course "
            f"of events."
        ),
        (
            "A New Dawn",
            f"{character_name} resolves the main conflict and leaves "
            f"{setting} with a lesson learned."
        ),
    ]

    # Make sure the fallback supports any configured panel count.
    while len(descriptions) < panel_count:
        number = len(descriptions) + 1
        descriptions.append(
            (
                f"Chapter {number}",
                f"{character_name} continues the adventure connected to "
                f"{story_prompt}."
            )
        )

    descriptions = descriptions[:panel_count]

    return [
        {
            "panel_number": index,
            "title": title,
            "scene_description": description,
            "image_prompt": (
                f"{art_style} comic illustration, "
                f"{setting}, "
                f"{character_name}, "
                f"{description}, "
                f"tone: {tone}, "
                "consistent character design, "
                "cinematic composition, "
                "clear facial expression, "
                "detailed environment, "
                "high quality, "
                "no written text, "
                "no speech bubbles, "
                "no captions, "
                "no logos, "
                "no watermark"
            ),
        }
        for index, (title, description) in enumerate(descriptions, start=1)
    ]


def _is_temporary_error(error: Exception) -> bool:
    """Check whether an error looks like a temporary Gemini failure."""

    error_text = str(error).lower()

    temporary_messages = [
        "503",
        "unavailable",
        "high demand",
        "temporarily unavailable",
        "service unavailable",
        "overloaded",
        "deadline exceeded",
        "timeout",
        "timed out",
        "429",
        "resource exhausted",
    ]

    return any(message in error_text for message in temporary_messages)


def generate_outline(
    story_prompt: str,
    character_name: str,
    setting: str,
    tone: str,
    art_style: str,
):
    """
    Generate a comic outline using Gemini.

    If Gemini is unavailable, the function automatically falls back
    to a locally generated comic outline.
    """

    settings = get_settings()

    # If Gemini SDK is unavailable, use fallback.
    if genai is None or types is None:
        print("Gemini SDK is not installed. Using local fallback.")
        return _fallback_outline(
            story_prompt,
            character_name,
            setting,
            tone,
            art_style,
        )

    # If API key is missing, use fallback.
    if not settings.gemini_api_key:
        print("GEMINI_API_KEY is missing. Using local fallback.")
        return _fallback_outline(
            story_prompt,
            character_name,
            setting,
            tone,
            art_style,
        )

    client = genai.Client(api_key=settings.gemini_api_key)

    prompt = f"""
Create exactly {settings.comic_panels} panels for a comic.

Story idea:
{story_prompt}

Main character:
{character_name}

Setting:
{setting}

Tone:
{tone}

Art style:
{art_style}

Return ONLY a JSON array.

Each item must contain exactly these fields:

panel_number:
integer

title:
string

scene_description:
string

image_prompt:
string

Requirements:

1. Create exactly {settings.comic_panels} panels.
2. Keep the same main character visually consistent across every panel.
3. Each panel must advance the story.
4. Make the story exciting and easy to understand.
5. Image prompts must describe one comic panel.
6. Do not include written text inside image prompts.
7. Do not include captions.
8. Do not include speech bubbles.
9. Do not include logos.
10. Do not include watermarks.
11. Return valid JSON only.
"""

    # Retry settings
    max_attempts = 3

    # Increasing delay: 2 seconds, 5 seconds, 10 seconds
    retry_delays = [2, 5, 10]

    for attempt in range(max_attempts):

        try:
            print(
                f"Gemini outline request "
                f"(attempt {attempt + 1}/{max_attempts})..."
            )

            response = client.models.generate_content(
                model=settings.gemini_outline_model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.8,
                    response_mime_type="application/json",
                ),
            )

            response_text = getattr(response, "text", None)

            if not response_text:
                raise ValueError("Gemini returned an empty response.")

            data = _extract_json(response_text)

            if not isinstance(data, list):
                raise ValueError(
                    "Gemini returned an invalid comic outline."
                )

            if len(data) != settings.comic_panels:
                raise ValueError(
                    f"Gemini returned {len(data)} panels, "
                    f"but {settings.comic_panels} were expected."
                )

            print("Gemini outline generated successfully.")

            return data

        except Exception as error:

            print(
                f"Gemini outline error "
                f"(attempt {attempt + 1}/{max_attempts}): {error}"
            )

            # If this is the final attempt, use fallback.
            if attempt == max_attempts - 1:
                print(
                    "Gemini is currently unavailable. "
                    "Using local fallback outline."
                )

                return _fallback_outline(
                    story_prompt,
                    character_name,
                    setting,
                    tone,
                    art_style,
                )

            # Retry temporary errors.
            if _is_temporary_error(error):
                delay = retry_delays[attempt]

                print(
                    f"Temporary Gemini error detected. "
                    f"Retrying in {delay} seconds..."
                )

                time.sleep(delay)

            else:
                # For non-temporary errors, don't repeatedly retry.
                print(
                    "Non-temporary Gemini error detected. "
                    "Using local fallback outline."
                )

                return _fallback_outline(
                    story_prompt,
                    character_name,
                    setting,
                    tone,
                    art_style,
                )

    # Safety fallback
    return _fallback_outline(
        story_prompt,
        character_name,
        setting,
        tone,
        art_style,
    )
