from pathlib import Path
from uuid import uuid4

from fpdf import FPDF


BASE_DIR = Path(__file__).resolve().parents[2]
EXPORT_DIR = BASE_DIR / "static" / "exports"

EXPORT_DIR.mkdir(parents=True, exist_ok=True)


def _clean_text(value) -> str:
    """Convert any value to safe printable PDF text."""

    if value is None:
        return ""

    text = str(value)

    # Replace characters that can cause wrapping problems.
    text = text.replace("\r", " ")
    text = text.replace("\n\n\n", "\n\n")

    # Replace very long runs of spaces.
    while "  " in text:
        text = text.replace("  ", " ")

    return text.strip()


def _safe_text(text: str) -> str:
    """
    Make text compatible with the default FPDF font.
    """

    text = _clean_text(text)

    replacements = {
        "“": '"',
        "”": '"',
        "‘": "'",
        "’": "'",
        "—": "-",
        "–": "-",
        "…": "...",
        "•": "-",
        "₹": "Rs.",
        "→": "->",
        "←": "<-",
        "↓": "v",
        "↑": "^",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    # Keep only characters supported by Helvetica.
    return text.encode("latin-1", "replace").decode("latin-1")


def _write_wrapped(pdf: FPDF, text: str, height: float = 6):
    """
    Safely write text using character wrapping.

    Character wrapping prevents the FPDF error:
    'Not enough horizontal space to render a single character'.
    """

    text = _safe_text(text)

    if not text:
        return

    try:
        # Modern fpdf2 supports CHAR wrapping.
        pdf.multi_cell(
            0,
            height,
            text,
            wrapmode="CHAR",
        )

    except TypeError:
        # Compatibility with older FPDF versions.
        pdf.multi_cell(
            0,
            height,
            text,
        )


def save_pdf(layout):
    """
    Create a PDF containing all comic panels.

    Parameters
    ----------
    layout:
        List of dictionaries containing panel information.

    Returns
    -------
    str:
        Relative path to the generated PDF.
    """

    if not layout:
        raise ValueError("Cannot create PDF because comic layout is empty.")

    filename = f"comic_{uuid4().hex[:10]}.pdf"
    output_path = EXPORT_DIR / filename

    pdf = FPDF(
        orientation="P",
        unit="mm",
        format="A4",
    )

    pdf.set_auto_page_break(
        auto=True,
        margin=15,
    )

    for index, panel in enumerate(layout, start=1):

        pdf.add_page()

        # -------------------------------------------------
        # PANEL TITLE
        # -------------------------------------------------

        panel_number = panel.get(
            "panel_number",
            index,
        )

        title = _safe_text(
            panel.get(
                "title",
                f"Panel {panel_number}",
            )
        )

        pdf.set_font(
            "Helvetica",
            "B",
            18,
        )

        pdf.cell(
            0,
            12,
            f"Panel {panel_number}: {title}",
            new_x="LMARGIN",
            new_y="NEXT",
        )

        # -------------------------------------------------
        # IMAGE
        # -------------------------------------------------

        image_path = panel.get("image_path")

        if image_path:

            image_file = Path(image_path)

            # Handle relative paths such as static/panels/image.png
            if not image_file.is_absolute():
                image_file = BASE_DIR / image_file

            if image_file.exists():

                # Keep image inside page margins.
                image_width = 175

                pdf.image(
                    str(image_file),
                    x=17.5,
                    y=None,
                    w=image_width,
                )

                pdf.ln(8)

        # -------------------------------------------------
        # SCENE DESCRIPTION
        # -------------------------------------------------

        scene_description = _safe_text(
            panel.get(
                "scene_description",
                "",
            )
        )

        if scene_description:

            pdf.set_font(
                "Helvetica",
                "B",
                11,
            )

            pdf.cell(
                0,
                7,
                "Scene:",
                new_x="LMARGIN",
                new_y="NEXT",
            )

            pdf.set_font(
                "Helvetica",
                "",
                10,
            )

            _write_wrapped(
                pdf,
                scene_description,
                5,
            )

            pdf.ln(3)

        # -------------------------------------------------
        # CAPTION
        # -------------------------------------------------

        caption = _safe_text(
            panel.get(
                "caption",
                "",
            )
        )

        if caption:

            pdf.set_font(
                "Helvetica",
                "B",
                11,
            )

            pdf.cell(
                0,
                7,
                "Caption:",
                new_x="LMARGIN",
                new_y="NEXT",
            )

            pdf.set_font(
                "Helvetica",
                "",
                10,
            )

            _write_wrapped(
                pdf,
                caption,
                5,
            )

            pdf.ln(3)

        # -------------------------------------------------
        # NARRATION
        # -------------------------------------------------

        narration = _safe_text(
            panel.get(
                "narration",
                "",
            )
        )

        if narration:

            pdf.set_font(
                "Helvetica",
                "B",
                11,
            )

            pdf.cell(
                0,
                7,
                "Narration:",
                new_x="LMARGIN",
                new_y="NEXT",
            )

            pdf.set_font(
                "Helvetica",
                "",
                10,
            )

            _write_wrapped(
                pdf,
                narration,
                5,
            )

            pdf.ln(3)

        # -------------------------------------------------
        # DIALOGUE
        # -------------------------------------------------

        dialogue = _safe_text(
            panel.get(
                "dialogue",
                "",
            )
        )

        if dialogue:

            pdf.set_font(
                "Helvetica",
                "B",
                11,
            )

            pdf.cell(
                0,
                7,
                "Dialogue:",
                new_x="LMARGIN",
                new_y="NEXT",
            )

            pdf.set_font(
                "Helvetica",
                "",
                10,
            )

            _write_wrapped(
                pdf,
                dialogue,
                5,
            )

    # -----------------------------------------------------
    # SAVE PDF
    # -----------------------------------------------------

    pdf.output(str(output_path))

    return f"/static/exports/{filename}"