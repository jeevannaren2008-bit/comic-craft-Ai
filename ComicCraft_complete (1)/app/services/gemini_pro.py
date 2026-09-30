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
    """Extract JSON from Gemini response."""

    if not text:
        raise ValueError("Gemini returned an empty response.")

    text = text.strip()

    # Remove Markdown JSON code fences
    text = re.sub(
        r"^```(?:json)?\s*",
        "",
        text,
        flags=re.IGNORECASE,
    )

    text = re.sub(r"\s*```$", "", text)

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Find JSON object or array inside the response
    object_match = re.search(r"\{[\s\S]*\}", text)

    if object_match:
        try:
            return json.loads(object_match.group(0))
        except json.JSONDecodeError:
            pass

    array_match = re.search(r"\[[\s\S]*\]", text)

    if array_match:
        try:
            return json.loads(array_match.group(0))
        except json.JSONDecodeError:
            pass

    raise ValueError("Gemini did not return valid JSON.")


def _fallback_story(outline):
    """
    Local story generator.

    This is used when Gemini is unavailable.
    """

    story = []

    for panel in outline:
        panel_number = panel.get("panel_number", len(story) + 1)
        title = panel.get("title", f"Panel {panel_number}")
        description = panel.get(
            "scene_description",
            "The story continues.",
        )

        story.append(
            {
                "panel_number": panel_number,
                "title": title,
                "caption": description,
                "narration": (
                    f"The adventure continues as the characters "
                    f"face what lies ahead. {description}"
                ),
                "dialogue": (
                    "Hero: We have to keep moving forward!"
                ),
            }
        )

    return story


def _is_temporary_error(error: Exception) -> bool:
    """Detect temporary Gemini errors."""

    message = str(error).lower()

    temporary_errors = [
        "503",
        "unavailable",
        "high demand",
        "temporarily unavailable",
        "service unavailable",
        "overloaded",
        "timeout",
        "timed out",
        "429",
        "resource exhausted",
    ]

    return any(item in message for item in temporary_errors)


def generate_story(outline, character_name=None, tone=None):
    """
    Generate narration and dialogue for the comic.

    Gemini is attempted first.

    If Gemini returns a temporary error or is unavailable,
    a local fallback story is returned instead.
    """

    settings = get_settings()

    # Always make sure outline is valid
    if not outline:
        return []

    # Gemini package unavailable
    if genai is None or types is None:
        print("Gemini SDK unavailable. Using local story fallback.")
        return _fallback_story(outline)

    # No API key
    if not settings.gemini_api_key:
        print("GEMINI_API_KEY not configured. Using local story fallback.")
        return _fallback_story(outline)

    client = genai.Client(
        api_key=settings.gemini_api_key
    )

    prompt = f"""
Create narration and dialogue for this comic.

Comic outline:

{json.dumps(outline, indent=2)}

Main character:
{character_name or "Main character"}

Tone:
{tone or "Adventure"}

Return ONLY a valid JSON array.

Each item must contain:

panel_number
title
caption
narration
dialogue

Rules:

1. Keep the same characters throughout the story.
2. Keep the story consistent with the panel descriptions.
3. Make the narration engaging.
4. Make the dialogue short and natural.
5. Do not add extra panels.
6. Return exactly the same number of panels as the input.
7. Return JSON only.
"""

    max_attempts = 3
    delays = [2, 5, 10]

    for attempt in range(max_attempts):

        try:
            print(
                f"Generating comic story with Gemini "
                f"(attempt {attempt + 1}/{max_attempts})..."
            )

            response = client.models.generate_content(
                model=settings.gemini_story_model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.7,
                    response_mime_type="application/json",
                ),
            )

            response_text = getattr(
                response,
                "text",
                None,
            )

            if not response_text:
                raise ValueError(
                    "Gemini returned an empty story response."
                )

            data = _extract_json(response_text)

            if not isinstance(data, list):
                raise ValueError(
                    "Gemini story response is not a JSON array."
                )

            if len(data) != len(outline):
                raise ValueError(
                    "Gemini returned an incorrect number of story panels."
                )

            print("Gemini story generated successfully.")

            return data

        except Exception as error:

            print(
                f"Gemini story error "
                f"(attempt {attempt + 1}/{max_attempts}): "
                f"{error}"
            )

            # Final attempt → local fallback
            if attempt == max_attempts - 1:

                print(
                    "Gemini is unavailable. "
                    "Switching to local story generation."
                )

                return _fallback_story(outline)

            # Retry temporary errors
            if _is_temporary_error(error):

                delay = delays[attempt]

                print(
                    f"Temporary Gemini problem. "
                    f"Retrying in {delay} seconds..."
                )

                time.sleep(delay)

            else:

                print(
                    "Gemini returned a non-temporary error. "
                    "Using local story generation."
                )

                return _fallback_story(outline)

    return _fallback_story(outline)
