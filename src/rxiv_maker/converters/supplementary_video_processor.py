"""Supplementary video processing for markdown to LaTeX conversion.

This module handles the conversion of supplementary video blocks. A
supplementary video is written as an (optional) still image followed by a
caption directive carrying a link to the video::

    ![alt](FIGURES/SVideo1.png)
    {#svideo:workflow url="https://youtu.be/XXXX"} **Title.** Description.

It is rendered as a non-floating, centred still image (so it is *not*
auto-numbered as a supplementary figure), followed by an automatically
numbered "Supplementary Video N. Title." caption, a "Watch video" hyperlink to
the URL, and the description. Videos are numbered independently from figures,
tables and notes, and can be cross-referenced from anywhere in the document
with ``@svideo:id`` (rendered as "Supplementary Video N").
"""

import re

from .types import LatexContent

# Block: optional image line, then `{#svideo:id ...attrs} **Title.** Description`.
# The whole block (image + title + the rest of the caption line) is captured and
# wrapped in an unbreakable minipage, so a still is never split from its caption
# across a page. The caption text is therefore emitted verbatim (not re-run
# through the Markdown formatters); video legends are plain prose.
_SVIDEO_PATTERN = re.compile(
    r"(?:!\[[^\]]*\]\(([^)]+)\)[ \t]*\r?\n[ \t]*)?"  # group 1: optional image path
    r"\{#svideo:([\w-]+)([^}]*)\}[ \t]*"  # group 2: id, group 3: raw attrs
    r"\*\*([^*]+)\*\*"  # group 4: bold title
    r"[ \t]*([^\r\n]*)",  # group 5: rest-of-line description
    re.MULTILINE,
)

_URL_ATTR = re.compile(r"""url\s*=\s*["']?([^"'\s}]+)""")
_WIDTH_ATTR = re.compile(r"""width\s*=\s*["']?([^"'\s}]+)""")

# Module-level store for protected replacements (mirrors the snote processor).
_svideo_replacements: dict[str, str] = {}


def _build_latex(image_path: str, svideo_id: str, attrs: str, title: str, description: str = "") -> str:
    """Build the LaTeX for one supplementary video block."""
    url_match = _URL_ATTR.search(attrs)
    width_match = _WIDTH_ATTR.search(attrs)
    width = width_match.group(1) if width_match else "0.9\\linewidth"

    url = url_match.group(1) if url_match else None

    parts: list[str] = []
    if image_path:
        image = f"\\includegraphics[width={width}]{{{image_path.strip()}}}"
        # Make the still itself a clickable link to the video when a URL is given.
        if url:
            image = f"\\href{{{url}}}{{{image}}}"
        parts.append("\\begin{center}\n" + image + "\n\\end{center}")

    caption = f"\\suppvideo{{{title.strip()}}}\\label{{svideo:{svideo_id}}}"
    if url:
        caption += f" (\\href{{{url}}}{{$\\blacktriangleright$~Watch video}})"
    if description.strip():
        caption += " " + description.strip()
    # Render the whole legend in the figure-caption font so it matches Fig./SFig.
    # legends (small sans-serif), rather than the larger body font.
    parts.append("{\\svideocaptionfont\\raggedright " + caption + "\\par}")

    body = "\n".join(parts)

    # Keep the block in place (right after the "Supplementary Videos" heading,
    # not floated away) while never splitting the still from its caption and
    # never overflowing the page: an unbreakable minipage preceded by \needspace,
    # which moves the whole block to the next page when it does not fit.
    if image_path:
        return (
            "\\par\\medskip\\needspace{0.5\\textheight}\n"
            "\\noindent\\begin{minipage}{\\linewidth}\n" + body + "\n\\end{minipage}\\par\\medskip"
        )
    return body


def process_supplementary_videos(content: LatexContent) -> LatexContent:
    """Convert supplementary video blocks to protected LaTeX placeholders.

    Must run BEFORE figure conversion so the still image is not turned into a
    numbered figure float. The replacement is stored behind an inert placeholder
    and restored after text formatting via
    :func:`restore_supplementary_video_placeholders`.

    Args:
        content: The markdown content to process.

    Returns:
        Content with supplementary video blocks replaced by placeholders.
    """
    global _svideo_replacements
    _svideo_replacements = {}

    counter = 0

    def _replace(match: re.Match) -> str:
        nonlocal counter
        image_path = match.group(1) or ""
        svideo_id = match.group(2).strip()
        attrs = match.group(3) or ""
        title = match.group(4)
        description = match.group(5) or ""

        placeholder = f"XXSVIDEOPROTECTEDXX{counter}XXENDXX"
        _svideo_replacements[placeholder] = _build_latex(image_path, svideo_id, attrs, title, description)
        counter += 1
        return placeholder

    return _SVIDEO_PATTERN.sub(_replace, content)


def restore_supplementary_video_placeholders(content: LatexContent) -> LatexContent:
    """Restore supplementary video placeholders with their LaTeX.

    Should be called after all text formatting is complete.
    """
    global _svideo_replacements
    for placeholder, latex in _svideo_replacements.items():
        content = content.replace(placeholder, latex)
    _svideo_replacements = {}
    return content


def process_supplementary_video_references(content: LatexContent) -> LatexContent:
    r"""Convert ``@svideo:id`` references to "Supplementary Video \\ref{...}".

    Run before citation processing so the reference is not mistaken for a
    citation key.
    """

    def _replace(match: re.Match) -> str:
        label = match.group(1)
        return f"Sup. Video~\\ref{{svideo:{label}}}"

    return re.sub(r"@svideo:([a-zA-Z0-9_-]+)", _replace, content)
